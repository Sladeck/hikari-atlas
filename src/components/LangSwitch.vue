<script setup>
// The language switch: English or Japanese, the whole site at once. Each option is written in its
// own language, so it can be found by someone who reads only that one.
import { lang, t } from '../i18n.js'
const OPTIONS = [['en', 'EN', 'English (EN)'], ['ja', '日本語', '日本語']]
</script>

<template>
  <div class="lang" role="group" :aria-label="t('language')">
    <button v-for="[code, label, full] in OPTIONS" :key="code" type="button" :lang="code" :aria-label="full"
            :aria-pressed="lang === code" @click="lang = code">{{ label }}</button>
  </div>
</template>

<style scoped>
.lang { display: inline-flex; border: 1px solid var(--edge); }
.lang button { min-height: 36px; min-width: 44px; padding: 0 12px; background: #000; border: 0; color: var(--dim);
  font-size: 13px; cursor: pointer; transition: color .25s, background-color .25s; }
.lang button + button { border-left: 1px solid var(--edge); }
.lang button[lang="ja"] { font-family: var(--mincho); font-weight: 500; font-size: 14px; }
.lang button:hover { color: var(--fg); }
.lang button[aria-pressed="true"] { color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, #000); cursor: default; }
.lang button:focus-visible { outline-offset: -2px; }
@media (hover: none), (max-width: 860px) { .lang button { min-height: 44px; } }
</style>
