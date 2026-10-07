<script setup>
defineProps({ sections: { type: Array, required: true } })
</script>

<template>
  <nav class="tabs" aria-label="Sections">
    <router-link
      v-for="s in sections"
      :key="s.id"
      :to="`/${s.id}`"
      class="tab"
      :style="{ '--tab': s.accent }"
    >
      <span class="tab-jp" lang="ja" aria-hidden="true">{{ s.kanji }}</span>
      <span class="tab-en"><span class="long">{{ s.title }}</span><span class="short" aria-hidden="true">{{ s.short }}</span></span>
    </router-link>
  </nav>
</template>

<style scoped>
.tabs { display: flex; gap: 2px; overflow-x: auto; scrollbar-width: none; flex: 1 1 auto; min-width: 0; }
.tabs::-webkit-scrollbar { display: none; }
.tab { display: flex; align-items: baseline; gap: 8px; padding: 10px 12px; text-decoration: none; color: var(--dim); border-bottom: 2px solid transparent; white-space: nowrap; transition: color .25s, border-color .25s; }
.tab:hover { color: var(--fg); }
.tab-jp { font-family: var(--mincho); font-size: 17px; }
.tab-en { font-size: 13px; }
.short { display: none; }
.tab.router-link-active { color: var(--tab); border-bottom-color: var(--tab); }
/* phones: kanji over a short English word, six equal columns, nothing hidden from screen readers */
@media (max-width: 720px) {
  .tabs { justify-content: space-between; gap: 0; }
  .tab { flex: 1 1 0; flex-direction: column; align-items: center; gap: 2px; padding: 8px 2px 6px; min-height: 52px; }
  .tab-jp { font-size: 17px; line-height: 1.1; }
  .tab-en { font-size: 10.5px; letter-spacing: .02em; }
  .long { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
  .short { display: inline; }
}
</style>
