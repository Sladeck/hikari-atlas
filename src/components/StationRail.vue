<script setup>
// The rail: the atlas's name and its departure board, held at the left of every page so any chapter
// is one click away, with the language switch beside the name. Pointing at a row shows that chapter on the live stage (StageLayer), clicking
// opens it. On the front page the stage is the page and the board turns over by itself; on a
// chapter page the board marks where the visitor is, and pointing at a row lifts the stage over
// the chapter until the pointer leaves.
import { computed, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import DepartureBoard from './DepartureBoard.vue'
import LangSwitch from './LangSwitch.vue'
import { sections, lang, t } from '../i18n.js'
import { selected, auto, peeking, DWELL, select, touched, peek, hold, unpeek } from '../station.js'

const route = useRoute()
const home = computed(() => route.path === '/')
const here = computed(() => sections.value.findIndex((s) => s.id === route.meta.section?.id))
onBeforeUnmount(() => clearTimeout(intent))
function poke() { if (home.value) touched() }
// a pointer only crossing the rail on its way somewhere does not lift the stage: it has to rest on a row
let intent = 0
function choose(i) {
  clearTimeout(intent)
  if (home.value) select(i)
  else if (peeking.value) peek(i)
  else intent = setTimeout(() => peek(i), 140)
}
function leave(e) { clearTimeout(intent); if (peeking.value && e.pointerType === 'mouse') unpeek(240) }
// keyboard: the peek lasts while focus is on the board or on the stage's own link
function out(e) { if (peeking.value && !e.relatedTarget?.closest('.rail, .layer')) unpeek() }
</script>

<template>
  <aside class="rail" :aria-label="t('name')" @pointerdown="poke" @keydown="poke"
         @pointerenter="hold" @pointerleave="leave" @focusout="out">
    <div class="rail-top">
      <router-link to="/" class="name" :class="{ ja: lang === 'ja' }" :aria-label="t('home')">{{ t('name') }}</router-link>
      <LangSwitch />
    </div>
    <DepartureBoard :sections="sections" :selected="home || peeking ? selected : here" preview
                    :dwell="home && auto ? DWELL : 0" @select="choose" />
    <p class="thesis">{{ t('thesis') }}</p>
  </aside>
</template>

<style scoped>
.rail { display: flex; flex-direction: column; gap: clamp(12px, 2.4vh, 28px); min-width: 0;
  padding: clamp(20px, 3.6vh, 40px) clamp(14px, 1.6vw, 28px) 20px; }
.rail-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.name { min-width: 0; text-decoration: none; color: var(--fg); white-space: nowrap;
  font-weight: 300; font-size: clamp(28px, 2.3vw, 38px); line-height: 1.1; letter-spacing: -.02em; }
.name.ja { font-family: var(--mincho); font-weight: 700; letter-spacing: .12em; color: var(--accent); transition: color .6s; }
.name:focus-visible { outline-offset: 6px; }
.rail .board { --row: 48px; }
.thesis { margin: auto 0 0; padding-top: 12px; max-width: 40ch; font-weight: 300; font-size: 14px; line-height: 1.55; color: var(--dim); }

/* phones: the header carries the name, so the rail is just the board under the front page's stage */
@media (max-width: 860px) {
  .rail { padding: 18px var(--gutter) 8px; }
  .rail-top, .thesis { display: none; }
  .rail .board { --row: 54px; }
}
</style>
