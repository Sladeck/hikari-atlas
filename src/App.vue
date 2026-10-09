<script setup>
import { watch, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import gsap from 'gsap'
import IndexMenu from './components/IndexMenu.vue'
import StationRail from './components/StationRail.vue'
import StageLayer from './components/StageLayer.vue'
import LangSwitch from './components/LangSwitch.vue'
import Icon from './components/Icon.vue'
import { SECTIONS } from './sections.js'
import { sections, local, t } from './i18n.js'
import { pageEntered } from './router.js'
import { selected } from './station.js'

const route = useRoute()
// publish the sticky header's height so full-screen stages can fit beneath it
const top = ref(null)
onMounted(() => {
  const set = () => document.documentElement.style.setProperty('--hdr', top.value.offsetHeight + 'px')
  set(); new ResizeObserver(set).observe(top.value)
})
function skip() { const m = document.getElementById('main'); m?.focus(); m?.scrollIntoView() }

// tween the interface accent to the section's own light
watch(
  () => route.meta.section,
  (s) => {
    if (!s) return
    selected.value = SECTIONS.findIndex((x) => x.id === s.id)   // back on the front page, the stage opens on this chapter
    const root = document.documentElement
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    gsap.to(root, { '--accent': s.accent, duration: reduce ? 0 : 0.9, ease: 'power2.out' })
  },
  { immediate: true },
)
// the tab's title, in the current language
watch([() => route.meta.section, sections], ([s]) => {
  document.title = s ? `${local(s).title} · ${t('name')}` : t('name')
}, { immediate: true })
</script>

<template>
  <a class="skip" href="#main" @click.prevent="skip">{{ t('skip') }}</a>
  <!-- phones only: on wider screens the rail carries the name and the chapters -->
  <header ref="top" class="top" :class="{ chapter: route.path !== '/' }">
    <div class="wrap top-row">
      <!-- on a chapter page the mark is the way back, pinned with the header while the chapter scrolls -->
      <router-link to="/" class="brand" :aria-label="route.path !== '/' ? t('back') : t('home')">
        <Icon v-if="route.path !== '/'" name="back" class="brand-back" />
        <span class="brand-mark" aria-hidden="true">光</span>
        <span class="brand-name">{{ t('name') }}</span>
      </router-link>
      <LangSwitch class="top-lang" />
      <IndexMenu v-if="route.path !== '/'" :sections="sections" />
    </div>
  </header>

  <!-- one page: the rail stays, only the pane beside it changes; the live stage is the front page -->
  <div class="shell" :class="{ home: route.path === '/' }">
    <StationRail class="side" />
    <StageLayer />
    <div class="pane">
      <router-view v-slot="{ Component, route: r }">
        <Transition name="page" mode="out-in" @enter="pageEntered">
          <component :is="Component" :key="r.path" />
        </Transition>
      </router-view>
    </div>
    <footer class="foot">
      <div class="foot-row">
        <p>{{ t('foot1')[0] }}<span class="mono">#000000</span>{{ t('foot1')[1] }}</p>
        <p>{{ t('foot2') }}</p>
      </div>
    </footer>
  </div>
</template>

<style>
.top { position: sticky; top: 0; z-index: 20; background: rgba(0, 0, 0, .82); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-bottom: 1px solid var(--line); }
.top-row { display: flex; align-items: center; gap: 12px 16px; padding-block: 12px; flex-wrap: wrap; }
@media (min-width: 861px) { .top { display: none; } }
.brand { min-height: 44px; display: flex; align-items: center; gap: 10px; text-decoration: none; color: var(--fg); }
.brand-mark { font-family: var(--mincho); font-size: 22px; color: var(--accent); line-height: 1; transition: color .6s; }
.brand-name { font-size: 15px; letter-spacing: .04em; }
.top.chapter .brand { gap: 8px; padding: 0 12px 0 10px; border: 1px solid var(--edge); background: #000; transition: border-color .25s, color .25s; }
.top.chapter .brand:hover, .top.chapter .brand:focus-visible { border-color: var(--accent); }
.brand-back { width: 20px; height: 20px; }
/* the narrowest phones keep the header on one line: the arrow alone, closer together */
@media (max-width: 380px) { .top.chapter .top-row { column-gap: 8px; } .top.chapter .brand { width: 44px; padding: 0; justify-content: center; }
  .top.chapter .brand-mark { display: none; } }
.top-lang { margin-left: auto; }
/* a narrow phone fits the mark, the switch and the index on one line by dropping the wordmark */
@media (max-width: 420px) { .top.chapter .brand-name { display: none; } }
.page-enter-active, .page-leave-active { transition: opacity .35s ease, transform .35s ease; }
.page-enter-from { opacity: 0; transform: translateY(12px); }
.page-leave-to { opacity: 0; transform: translateY(-8px); }
.foot { grid-area: foot; border-top: 1px solid var(--line); margin-top: 48px; }
.foot-row { padding: 32px var(--gutter) 56px; display: grid; gap: 12px; color: var(--dim); font-weight: 300; max-width: 820px; }
.foot-row p { margin: 0; }

/* the rail holds still at the left while the window scrolls the pane; the pane is the container
   its pages size themselves against, since its width is the window's minus the rail */
.shell { display: grid; grid-template-columns: clamp(320px, 26vw, 400px) minmax(0, 1fr); grid-template-areas: "side pane" "side foot"; }
.side { grid-area: side; position: sticky; top: 0; align-self: start; height: 100vh; height: 100svh; overflow-y: auto;
  border-right: 1px solid var(--line); scrollbar-width: thin; }
.pane { grid-area: pane; min-width: 0; container: pane / inline-size; }
/* the stage shares the pane's cell; it is the front page and stays out of sight on chapter pages */
.layer { grid-area: pane; position: sticky; top: 0; align-self: start; z-index: 5; }
/* the front page is the stage alone: a footer under it would only add a scrollbar that moves nothing */
@media (min-width: 861px) { .shell.home .foot { display: none; } }
@media (max-width: 860px) {
  .shell { display: flex; flex-direction: column; }
  .side { position: static; align-self: stretch; height: auto; overflow: visible; border-right: 0; order: 1; }
  .shell:not(.home) .side { display: none; }
  .layer { position: relative; align-self: stretch; }       /* a column flex item would shrink to its absolute children: 0 px */
  .foot { order: 2; }
}
</style>
