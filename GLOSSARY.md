# 용어 (지침·skill·hook·rule 작성용, 상시 로드하지 않음)

## Claude 제공 기능: 영어 그대로 쓴다
| 표기 | 뜻 | 위치 |
| --- | --- | --- |
| CLAUDE.md | 상시 로드 지침 | `~/.claude/CLAUDE.md`, 프로젝트 루트 |
| skill | 필요할 때 읽는 작업 절차 | `.claude/skills/<이름>/SKILL.md` |
| agent | 별도 컨텍스트에서 도는 subagent | `.claude/agents/<이름>.md` |
| hook | 이벤트에 붙는 강제 스크립트 | `settings.json` → `.claude/hooks/` |
| rule | 경로·주제별 지침 | `.claude/rules/*.md` |
| settings | 권한·hook·env 설정 | `settings.json` |
| frontmatter | 파일 첫머리 `---` 블록 | skill, agent |
| worktree | git worktree | 병렬 작업 격리 |
| plugin | skill·hook·MCP 묶음 | 외부 도입 대상 |

복수형도 그대로 쓴다(skill 6종, agent 3종). "스킬", "에이전트", "훅", "서브에이전트" 표기는 쓰지 않는다.

## 설계 용어: 한국어로 쓴다
| 표기 | 뜻 |
| --- | --- |
| 루프 3요소 | 성공 기준·검증자·중단 조건 |
| 결정적 검사 | 종료 코드로 판정하는 테스트·빌드·린트·커버리지 |
| 사람 승인 | 설계 직후·최종(커밋·배포 전) 승인 |
| 메인 세션 | 작업을 수행하는 대화 세션 |
| 목표 한 줄 | 끝나면 참인 것 한 문장 |
| 프로젝트 지식 skill | conventions·architecture·database·testing 스텁 |
| 프리셋 | roster.yaml의 프로젝트 유형별 구성 |

## 판정 토큰: 대문자 영어, kr/en 동일
PASS, FAIL, UNVERIFIED, BLOCKED, CODE, TEST, SPEC, ENV. 출력 머리말 Findings, Uncertainty, Next action도 두 언어에서 같다.
