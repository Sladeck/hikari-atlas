<script setup>
import { watch, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import gsap from 'gsap'
import IndexMenu from './components/IndexMenu.vue'
import StationRail from './components/StationRail.vue'
import StageLayer from './components/StageLayer.vue'
import { SECTIONS } from './sections.js'
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
    gsap.to(root, { '--accent': s.accent, '--accent2': s.accent2, duration: reduce ? 0 : 0.9, ease: 'power2.out' })
    document.title = `${s.title} · Hikari Atlas`
  },
  { immediate: true },
)
</script>

<template>
  <a class="skip" href="#main" @click.prevent="skip">Skip to content</a>
  <!-- phones only: on wider screens the rail carries the name and the chapters -->
  <header ref="top" class="top">
    <div class="wrap top-row">
      <router-link to="/" class="brand" aria-label="Hikari Atlas, home">
        <span class="brand-mark" aria-hidden="true">光</span>
        <span class="brand-name">Hikari Atlas</span>
      </router-link>
      <IndexMenu v-if="route.path !== '/'" :sections="SECTIONS" />
    </div>
  </header>

  <!-- one page: the rail stays, only the pane beside it changes; the live stage is the front page,
       and lifts over a chapter while a board row is pointed at -->
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
        <p>Japan drawn as light on pure black, from public scientific data. Every unlit pixel is exactly <span class="mono">#000000</span>, so OLED screens switch it off. Wallpapers are free to use.</p>
        <p>Rendered in Python with NumPy, SciPy and Pillow. Animations run on the same data in the browser, with Vue and GSAP.</p>
      </div>
    </footer>
  </div>
</template>

<style>
.top { position: sticky; top: 0; z-index: 20; background: rgba(0, 0, 0, .82); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-bottom: 1px solid var(--line); }
.top-row { display: flex; align-items: center; gap: 24px 40px; padding-block: 12px; flex-wrap: wrap; }
@media (min-width: 861px) { .top { display: none; } }
.brand { min-height: 44px; display: flex; align-items: center; gap: 10px; text-decoration: none; color: var(--fg); }
.brand-mark { font-family: var(--mincho); font-size: 22px; color: var(--accent); line-height: 1; transition: color .6s; }
.brand-name { font-size: 15px; letter-spacing: .04em; }
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
/* the stage shares the pane's cell and stays in view over a scrolled chapter */
.layer { grid-area: pane; position: sticky; top: 0; align-self: start; z-index: 5; }
@media (max-width: 860px) {
  .shell { display: flex; flex-direction: column; }
  .side { position: static; align-self: stretch; height: auto; overflow: visible; border-right: 0; order: 1; }
  .shell:not(.home) .side { display: none; }
  .layer { position: relative; }
  .foot { order: 2; }
}
</style>
