<script setup>
import { watch, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import gsap from 'gsap'
import IndexMenu from './components/IndexMenu.vue'
import StationRail from './components/StationRail.vue'
import StageLayer from './components/StageLayer.vue'
import LangSwitch from './components/LangSwitch.vue'
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
      <router-link to="/" class="brand" :aria-label="t('home')">
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
@media (max-width: 860px) {
  .shell { display: flex; flex-direction: column; }
  .side { position: static; align-self: stretch; height: auto; overflow: visible; border-right: 0; order: 1; }
  .shell:not(.home) .side { display: none; }
  .layer { position: relative; }
  .foot { order: 2; }
}
</style>
