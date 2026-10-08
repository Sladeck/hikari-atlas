<script setup>
import { watch, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import gsap from 'gsap'
import IndexMenu from './components/IndexMenu.vue'
import { SECTIONS } from './sections.js'
import { pageEntered } from './router.js'

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
  <header ref="top" class="top" :class="{ 'on-home': route.path === '/' }">
    <div class="wrap top-row">
      <router-link to="/" class="brand" aria-label="Hikari Atlas, home">
        <span class="brand-mark" aria-hidden="true">光</span>
        <span class="brand-name">Hikari Atlas</span>
      </router-link>
      <IndexMenu v-if="route.path !== '/'" :sections="SECTIONS" />
    </div>
  </header>

  <router-view v-slot="{ Component, route: r }">
    <Transition name="page" mode="out-in" @enter="pageEntered">
      <component :is="Component" :key="r.path" />
    </Transition>
  </router-view>

  <footer class="foot">
    <div class="wrap foot-row">
      <p>Japan drawn as light on pure black, from public scientific data. Every unlit pixel is exactly <span class="mono">#000000</span>, so OLED screens switch it off. Wallpapers are free to use.</p>
      <p>Rendered in Python with NumPy, SciPy and Pillow. Animations run on the same data in the browser, with Vue and GSAP.</p>
    </div>
  </footer>
</template>

<style>
.top { position: sticky; top: 0; z-index: 20; background: rgba(0, 0, 0, .82); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-bottom: 1px solid var(--line); }
.top-row { display: flex; align-items: center; gap: 24px 40px; padding-block: 12px; flex-wrap: wrap; }
/* on wide screens the front page's own title leads its board, so the bar steps aside there */
@media (min-width: 861px) { .top.on-home { display: none; } }
.brand { min-height: 44px; display: flex; align-items: center; gap: 10px; text-decoration: none; color: var(--fg); }
.brand-mark { font-family: var(--mincho); font-size: 22px; color: var(--accent); line-height: 1; transition: color .6s; }
.brand-name { font-size: 15px; letter-spacing: .04em; }
.page-enter-active, .page-leave-active { transition: opacity .35s ease, transform .35s ease; }
.page-enter-from { opacity: 0; transform: translateY(12px); }
.page-leave-to { opacity: 0; transform: translateY(-8px); }
.foot { border-top: 1px solid var(--line); margin-top: 48px; }
.foot-row { padding-block: 32px 56px; display: grid; gap: 12px; color: var(--dim); font-weight: 300; max-width: 820px; margin-inline: 0; }
.foot-row p { margin: 0; }
</style>
