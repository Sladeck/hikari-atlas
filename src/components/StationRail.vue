<script setup>
// The rail: the atlas's name and its departure board, held at the left of every page so any chapter
// is one click away, with the language switch beside the name. On the front page, pointing at a row
// shows that chapter on the live stage (StageLayer) and the board turns over by itself; clicking
// opens the chapter. On a chapter page the board is plain navigation: it marks where the visitor is,
// and a row opens its chapter straight away. The way back to the stage is the front page.
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DepartureBoard from './DepartureBoard.vue'
import LangSwitch from './LangSwitch.vue'
import { sections, lang, t } from '../i18n.js'
import { selected, auto, DWELL, select, touched } from '../station.js'

const route = useRoute()
const home = computed(() => route.path === '/')
const here = computed(() => sections.value.findIndex((s) => s.id === route.meta.section?.id))
function poke() { if (home.value) touched() }
</script>

<template>
  <aside class="rail" :aria-label="t('name')" @pointerdown="poke" @keydown="poke">
    <div class="rail-top">
      <router-link to="/" class="name" :class="{ ja: lang === 'ja' }" :aria-label="t('home')">{{ t('name') }}</router-link>
      <LangSwitch />
    </div>
    <DepartureBoard :sections="sections" :selected="home ? selected : here" :preview="home"
                    :dwell="home && auto ? DWELL : 0" @select="select" />
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
