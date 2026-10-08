<script setup>
// The rail: the atlas's name and its departure board, held at the left of every page so any chapter
// is one click away. Pointing at a row shows that chapter on the live stage (StageLayer), clicking
// opens it. On the front page the stage is the page and the board turns over by itself; on a
// chapter page the board marks where the visitor is, and pointing at a row lifts the stage over
// the chapter until the pointer leaves.
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import DepartureBoard from './DepartureBoard.vue'
import { SECTIONS } from '../sections.js'
import { selected, auto, peeking, reduce, DWELL, select, touched, peek, hold, unpeek } from '../station.js'

const route = useRoute()
const home = computed(() => route.path === '/')
const here = computed(() => SECTIONS.findIndex((s) => s.id === route.meta.section?.id))
const en = ref(false)                                 // the board's face, title included: Japanese or English
let flip = 0
onMounted(() => { if (!reduce) flip = setInterval(() => { en.value = !en.value }, 4200) })
onBeforeUnmount(() => { clearInterval(flip); clearTimeout(intent) })
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
  <aside class="rail" aria-label="Hikari Atlas" @pointerdown="poke" @keydown="poke"
         @pointerenter="hold" @pointerleave="leave" @focusout="out">
    <router-link to="/" class="name" :class="{ en, still: reduce }">
      <span class="visually-hidden">Hikari Atlas, <span lang="ja">光の地図</span>, front page</span>
      <span class="face jp" lang="ja" aria-hidden="true">光の地図</span><span class="face" aria-hidden="true">Hikari Atlas</span>
    </router-link>
    <DepartureBoard :sections="SECTIONS" :selected="home || peeking ? selected : here" preview
                    :dwell="home && auto ? DWELL : 0" :face="reduce ? null : en" @select="choose" />
    <p class="thesis">Japan drawn only with light, from real data. Every chapter ends in free OLED wallpapers.</p>
  </aside>
</template>

<style scoped>
.rail { display: flex; flex-direction: column; gap: clamp(12px, 2.4vh, 28px); min-width: 0;
  padding: clamp(20px, 3.6vh, 40px) clamp(14px, 1.6vw, 28px) 20px; }
/* the name turns over with the board: 光の地図 and Hikari Atlas share one line */
.name { position: relative; display: grid; align-self: start; height: 1.1em; overflow: hidden; text-decoration: none; color: var(--fg);
  font-weight: 300; font-size: clamp(30px, 2.5vw, 42px); line-height: 1.1; letter-spacing: -.02em; }
.face { grid-area: 1 / 1; white-space: nowrap; transition: transform .7s var(--ease-out), opacity .7s var(--ease-out); }
.face.jp { font-family: var(--mincho); font-weight: 700; letter-spacing: .12em; color: var(--accent); }
.face:not(.jp) { transform: translateY(100%); opacity: 0; }
.name.en .face.jp { transform: translateY(-100%); opacity: 0; }
.name.en .face:not(.jp) { transform: none; opacity: 1; }
.name.still { height: auto; display: flex; flex-wrap: wrap; gap: 0 .4em; }
.name.still .face { transform: none; opacity: 1; }
.name:focus-visible { outline-offset: 6px; }
.rail .board { --row: 48px; }
.thesis { margin: auto 0 0; padding-top: 12px; max-width: 40ch; font-weight: 300; font-size: 14px; line-height: 1.55; color: var(--dim); }

/* phones: the header carries the name, so the rail is just the board under the front page's stage */
@media (max-width: 860px) {
  .rail { padding: 18px var(--gutter) 8px; }
  .name, .thesis { display: none; }
  .rail .board { --row: 54px; }
}
</style>
