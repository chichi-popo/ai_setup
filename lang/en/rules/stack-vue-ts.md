---
paths:
  - "**/*.vue"
  - "**/*.ts"
  - "**/*.js"
  - "**/*.css"
---
# stack-vue-ts: Vue3 and TypeScript checklist

> Source: condensed from ECC (MIT) `rules/vue` and `rules/typescript` (third_party/ECC@ccd8da1). Project rules (CLAUDE.md, design tokens, existing components) win over this file.
>
> Scope: apply to the code you write or change now. Report violations outside the change instead of fixing them (the project's surgical-change rule wins).

## SFC and reactivity
- New code uses `<script setup lang="ts">` and the Composition API. If the existing file is JS, keep that language (switch to TypeScript only when asked).
- `ref` is the default; use `reactive` only for grouped object state and never reassign it whole. Destructuring a `reactive` object or a Pinia store without `toRefs`/`storeToRefs` silently drops reactivity.
- `computed` stays pure. Watch a reactive property through a getter (`watch(() => x.value, ...)`). `watchEffect` stops tracking dependencies after its first `await`.
- Clean up timers, listeners, and subscriptions in `onUnmounted`. Give every `v-for` a stable unique `:key` (never the index or an object) and never put `v-if` and `v-for` on the same element.

## Composables, state, and routing
- A composable normalizes `MaybeRefOrGetter` inputs with `toValue`. One that uses lifecycle hooks or `inject` is called only inside `setup`.
- `provide`/`inject` use `InjectionKey<T>` keys and the provider owns mutations. Never persist auth tokens to `localStorage`.
- vue-router lazy-loads route components with dynamic `import()`. In a vue-query key put the `ref`/`computed` itself, not `.value` (it freezes the key and stops refetching).

## TypeScript
- Add parameter and return types on public APIs and let locals infer. Prefer string literal unions over `enum`.
- Take external input as `unknown` instead of `any` and narrow it, and catch errors as `catch (error: unknown)`. Validate external input with a schema (Zod and the like). Leave no `console.log` in production code.

## Security
- `v-html` is an XSS path: do not use it on user content, and if unavoidable sanitize first with DOMPurify. Never compile user input as a template or let a user string decide `:is`.
- `:href`/`:src` are not escaped and `javascript:` URLs execute. Restrict schemes to `http`/`https`/`mailto` and never put user strings in `:style`.
- Keep secrets out of the client bundle (`VITE_` variables are exposed to the browser).

## Checks and tests
- Use only the tools the project already has: `vue-tsc --noEmit` (once at the end of the work), `eslint`, `prettier`, and Vitest if tests exist. Ask before installing new packages.
- Tests assert only the public interface (props, emitted events, slots, rendered output); `await` `trigger`/`setValue` and wait for the DOM after a state change with `nextTick`/`flushPromises`.
