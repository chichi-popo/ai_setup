<!-- SEED FILE for bundle test (stack-vue-ts). Planted issues; do not ship. Copy into src/, delete after the test. -->
<script setup>
import { reactive, ref, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'

const state = reactive({ items: [], q: '' })
const { items, q } = state
const id = ref(1)
useQuery({ queryKey: ['item', id.value], queryFn: () => fetch('/api/item/' + id.value).then(r => r.json()) })
watch(state, () => console.log('changed'))
</script>

<template>
  <div><div>
    <div v-for="(it, i) in items" :key="i" v-if="it.visible" v-html="it.bio"></div>
  </div></div>
</template>
