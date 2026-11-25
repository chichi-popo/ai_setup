---
paths:
  - "**/*.vue"
  - "**/*.ts"
  - "**/*.js"
  - "**/*.css"
---
# stack-vue-ts: Vue3·TypeScript 점검표

> 출처: ECC(MIT) `rules/vue`, `rules/typescript` 발췌 요약(third_party/ECC@ccd8da1). 프로젝트 규칙(CLAUDE.md, 디자인 토큰, 기존 컴포넌트)이 이 파일보다 우선한다.
>
> 적용 범위: 이번에 쓰거나 고치는 코드에만 적용한다. 수정 범위 밖의 위반은 고치지 말고 보고만 한다(프로젝트의 최소 변경 원칙이 우선).

## SFC·반응성
- 새 코드는 `<script setup lang="ts">`와 Composition API. 기존 파일이 JS면 그 언어를 따른다(TypeScript 전환은 요청이 있을 때만).
- `ref`가 기본이고 `reactive`는 묶음 객체에만 쓰며 통째로 재할당하지 않는다. `reactive`나 Pinia store를 `toRefs`/`storeToRefs` 없이 구조 분해하면 반응성이 조용히 사라진다.
- `computed`는 순수 함수. `watch`는 반응형 속성을 getter로(`watch(() => x.value, ...)`). `watchEffect`는 첫 `await` 뒤 의존성 추적을 멈춘다.
- 타이머·리스너·구독은 `onUnmounted`에서 정리한다. `v-for`에는 안정적인 고유 `:key`(인덱스·객체 금지), 같은 요소에 `v-if`와 `v-for`를 같이 쓰지 않는다.

## 컴포저블·상태·라우팅
- 컴포저블은 `MaybeRefOrGetter` 입력을 `toValue`로 정규화한다. 생명주기·`inject`를 쓰는 컴포저블은 `setup` 안에서만 호출한다.
- `provide`/`inject`는 `InjectionKey<T>` 키를 쓰고 제공 쪽이 변경을 맡는다. 인증 토큰은 `localStorage`에 저장하지 않는다.
- vue-router는 라우트 컴포넌트를 동적 `import()`로 지연 로딩한다. vue-query 쿼리 키에는 `.value`가 아니라 `ref`/`computed` 자체를 넣는다(고정되어 재조회가 멈춘다).

## TypeScript
- 공개 API에 매개변수·반환 타입을 쓰고 지역 변수는 추론에 맡긴다. `enum`보다 문자열 리터럴 유니온을 우선한다.
- `any` 대신 `unknown`으로 받아 좁히고 `catch (error: unknown)`. 외부 입력은 스키마(Zod 등)로 검증한다. 운영 코드에 `console.log`를 남기지 않는다.

## 보안
- `v-html`은 XSS 경로다. 사용자 콘텐츠에 쓰지 않고 불가피하면 DOMPurify로 먼저 정화한다. 사용자 입력을 템플릿으로 컴파일하거나 사용자 문자열로 `:is`를 정하지 않는다.
- `:href`/`:src`는 이스케이프되지 않아 `javascript:` URL이 실행된다. 스킴을 `http`/`https`/`mailto`로 제한하고 `:style`에 사용자 문자열을 넣지 않는다.
- 클라이언트 번들에 비밀 값을 넣지 않는다(`VITE_` 변수는 브라우저에 노출된다).

## 검사·테스트
- 프로젝트에 이미 있는 도구만 쓴다: `vue-tsc --noEmit`(작업 끝에 한 번), `eslint`, `prettier`, 테스트가 있으면 Vitest. 새 패키지 설치는 승인을 받는다.
- 테스트는 공개 인터페이스(props, emit, slots, 렌더 결과)만 검증하고, `trigger`/`setValue`는 `await`, 상태 변경 뒤에는 `nextTick`/`flushPromises`로 기다린다.
