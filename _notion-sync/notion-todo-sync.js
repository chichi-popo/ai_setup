#!/usr/bin/env node
'use strict';

/**
 * Claude Code TodoWrite -> Notion 체크리스트 동기화 훅 스크립트
 *
 * 트리거: PostToolUse (matcher: "TodoWrite")
 * 동작:
 *   - 프로젝트 루트의 .ai/.notion_prop 이 있는 프로젝트만 동기화 대상으로 삼음
 *   - 신규 todo -> Notion 페이지 생성
 *   - 상태 변경(수집/진행중/완료) -> 기존 Notion 페이지 상태 속성 업데이트
 *   - 목록에서 사라진 todo(삭제) -> 상태를 "취소"로 변경, 추적 목록에서 제거
 *   - 재정렬(순서)은 동기화하지 않음
 *   - 어떤 오류가 나도 Claude Code 동작을 막지 않도록 항상 exit 0, 로그만 남김
 *
 * 필요 환경변수:
 *   NOTION_TOKEN             - Notion 인테그레이션 시크릿 (secret_...)
 *   NOTION_TODO_DB_ID        - 체크리스트 DB ID
 */

const fs = require('fs');
const path = require('path');

const NOTION_TOKEN = process.env.NOTION_TOKEN;
const TODO_DB_ID = process.env.NOTION_TODO_DB_ID;
const NOTION_VERSION = '2022-06-28';

// Claude Code TodoWrite status -> Notion "상태" 속성 옵션명
const STATUS_MAP = {
  pending: '수집',
  in_progress: '진행중',
  completed: '완료',
};
// todo가 목록에서 사라졌을 때(삭제) 부여할 상태
const STATUS_CANCELLED = '취소';

function log(cwd, msg) {
  try {
    const dir = path.join(cwd, '.claude');
    fs.mkdirSync(dir, { recursive: true });
    fs.appendFileSync(
      path.join(dir, 'notion-sync.log'),
      `[${new Date().toISOString()}] ${msg}\n`
    );
  } catch (_) {
    // 로깅 실패는 무시 (Claude Code 동작에 영향 주지 않음)
  }
}

async function notionFetch(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: {
      Authorization: `Bearer ${NOTION_TOKEN}`,
      'Notion-Version': NOTION_VERSION,
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(`Notion API ${res.status}: ${JSON.stringify(data)}`);
  }
  return data;
}

function readJson(file, fallback) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (_) {
    return fallback;
  }
}

function writeJson(file, data) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2));
}

async function findPageIdByTitle(dbId, titleProp, value, extraFilter) {
  const filter = extraFilter
    ? { and: [{ property: titleProp, title: { equals: value } }, extraFilter] }
    : { property: titleProp, title: { equals: value } };

  const result = await notionFetch(
    `https://api.notion.com/v1/databases/${dbId}/query`,
    { method: 'POST', body: JSON.stringify({ filter }) }
  );
  return result.results[0] ? result.results[0].id : null;
}

// 체크리스트 DB의 "프로젝트" relation -> 프로젝트 DB -> (필요시) "영역" relation -> 영역 DB
// 순서로 실제 연결할 프로젝트 페이지 ID를 찾아낸다.
async function resolveProjectRelationId(proj, area) {
  const todoSchema = await notionFetch(
    `https://api.notion.com/v1/databases/${TODO_DB_ID}`
  );
  const projectProp = todoSchema.properties['프로젝트'];
  if (!projectProp || projectProp.type !== 'relation') {
    throw new Error('체크리스트 DB의 "프로젝트" 속성이 relation 타입이 아닙니다.');
  }
  const projectsDbId = projectProp.relation.database_id;

  const projectsSchema = await notionFetch(
    `https://api.notion.com/v1/databases/${projectsDbId}`
  );
  const areaProp = projectsSchema.properties['영역'];

  let extraFilter;
  if (area && areaProp && areaProp.type === 'relation') {
    const areasDbId = areaProp.relation.database_id;
    const areaPageId = await findPageIdByTitle(areasDbId, '이름', area);
    if (!areaPageId) {
      throw new Error(`영역 DB에서 "${area}" 항목을 찾지 못했습니다.`);
    }
    extraFilter = { property: '영역', relation: { contains: areaPageId } };
  }

  const projectPageId = await findPageIdByTitle(
    projectsDbId,
    '이름',
    proj,
    extraFilter
  );
  if (!projectPageId) {
    throw new Error(`프로젝트 DB에서 "${proj}"(영역: ${area || '-'}) 항목을 찾지 못했습니다.`);
  }
  return projectPageId;
}

function statusPropertyPayload(propType, statusName) {
  return propType === 'status'
    ? { status: { name: statusName } }
    : { select: { name: statusName } };
}

async function readStdin() {
  let raw = '';
  for await (const chunk of process.stdin) raw += chunk;
  return raw;
}

async function main() {
  const raw = await readStdin();

  let payload;
  try {
    payload = JSON.parse(raw);
  } catch (_) {
    return; // 훅 입력 파싱 실패 -> 조용히 종료
  }

  const cwd = payload.cwd || process.cwd();

  if (payload.tool_name !== 'TodoWrite') return;

  if (!NOTION_TOKEN || !TODO_DB_ID) {
    log(cwd, 'NOTION_TOKEN 또는 NOTION_TODO_DB_ID 환경변수가 없어 동기화를 건너뜁니다.');
    return;
  }

  const propFile = path.join(cwd, '.ai', '.notion_prop');
  if (!fs.existsSync(propFile)) return; // Notion 연동 대상이 아닌 프로젝트

  const { proj, area } = readJson(propFile, {});
  if (!proj) {
    log(cwd, '.notion_prop에 proj 값이 없습니다.');
    return;
  }

  const todos = (payload.tool_input && payload.tool_input.todos) || [];
  const stateFile = path.join(cwd, '.claude', 'notion-todo-state.json');
  const state = readJson(stateFile, {
    items: [],
    projectRelationId: null,
    statusPropType: null,
  });

  try {
    if (!state.projectRelationId) {
      state.projectRelationId = await resolveProjectRelationId(proj, area);
    }
    if (!state.statusPropType) {
      const schema = await notionFetch(
        `https://api.notion.com/v1/databases/${TODO_DB_ID}`
      );
      state.statusPropType =
        (schema.properties['상태'] && schema.properties['상태'].type) || 'select';
    }

    // 목록에서 사라진(삭제된) todo -> Notion 상태를 "취소"로 변경
    const currentContents = new Set(todos.map((t) => t.content));
    const stillTracked = [];
    for (const item of state.items) {
      if (currentContents.has(item.content)) {
        stillTracked.push(item);
        continue;
      }
      try {
        await notionFetch(`https://api.notion.com/v1/pages/${item.pageId}`, {
          method: 'PATCH',
          body: JSON.stringify({
            properties: {
              상태: statusPropertyPayload(state.statusPropType, STATUS_CANCELLED),
            },
          }),
        });
        // 취소 처리 완료 -> 더 이상 추적하지 않음 (동일 문구 재등장 시 새 항목으로 생성)
      } catch (err) {
        log(cwd, `취소 처리 실패 (${item.content}): ${err.message}`);
        stillTracked.push(item); // 실패 시 다음 실행에서 재시도
      }
    }
    state.items = stillTracked;

    for (const todo of todos) {
      const statusName = STATUS_MAP[todo.status] || STATUS_MAP.pending;
      const existing = state.items.find((i) => i.content === todo.content);

      if (!existing) {
        const page = await notionFetch('https://api.notion.com/v1/pages', {
          method: 'POST',
          body: JSON.stringify({
            parent: { database_id: TODO_DB_ID },
            properties: {
              이름: { title: [{ text: { content: todo.content } }] },
              상태: statusPropertyPayload(state.statusPropType, statusName),
              프로젝트: { relation: [{ id: state.projectRelationId }] },
            },
          }),
        });
        state.items.push({
          content: todo.content,
          status: todo.status,
          pageId: page.id,
        });
      } else if (existing.status !== todo.status) {
        await notionFetch(`https://api.notion.com/v1/pages/${existing.pageId}`, {
          method: 'PATCH',
          body: JSON.stringify({
            properties: {
              상태: statusPropertyPayload(state.statusPropType, statusName),
            },
          }),
        });
        existing.status = todo.status;
      }
    }

    writeJson(stateFile, state);
  } catch (err) {
    log(cwd, `동기화 실패: ${err.message}`);
  }
}

main();
