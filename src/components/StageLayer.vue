<script setup>
// The live stage, held by the shell beside the rail: on the front page it is the page itself.
// Choosing a board row sends the same cloud of light to that chapter's scene; opening it shows the
// chapter, and the stage waits out of sight (drawing nothing) until the visitor comes back.
// Without WebGL it crossfades between the chapters' stills.
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import gsap from 'gsap'
import Icon from './Icon.vue'
import ParticleStage from './ParticleStage.vue'
import { SECTIONS } from '../sections.js'
import { sections, t } from '../i18n.js'
import { selected, reduce, touched } from '../station.js'

const route = useRoute()
const base = import.meta.env.BASE_URL
const home = computed(() => route.path === '/')
const shown = home
const s = computed(() => sections.value[selected.value])
const scenes = SECTIONS.map((x) => x.scene)
const webgl = ref(true)
const armed = ref(shown.value)                        // the stage loads the first time it is needed
watch(shown, (v) => { if (v) armed.value = true })

// the interface wears the light of whatever the stage shows, and the chapter's own once it falls back
function tint(sec) {
  if (sec) gsap.to(document.documentElement, { '--accent': sec.accent, '--accent2': sec.accent2, duration: reduce ? 0 : 0.8, ease: 'power2.out' })
}
watch([selected, shown], () => tint(shown.value ? s.value : route.meta.section), { immediate: true })

function noWebGL() { webgl.value = false; window.hikariLoader?.done() }
function poke() { if (home.value) touched() }
</script>

<template>
  <section class="layer" :class="{ shown, home }" :inert="!shown" :aria-hidden="!shown" :aria-label="t('preview')"
           :style="{ '--tone': s.accent }" @pointerdown="poke" @keydown="poke">
    <ParticleStage v-if="webgl && armed" :scenes="scenes" :index="selected" :active="shown" @unsupported="noWebGL" />
    <template v-else-if="!webgl">
      <Transition name="still">
        <picture :key="s.still" class="still">
          <source media="(max-width: 860px)" :srcset="`${base}wallpapers/feature/${s.still}_p.webp`" />
          <img :src="`${base}wallpapers/feature/${s.still}_d.webp`" alt="" width="2560" height="1440" />
        </picture>
      </Transition>
    </template>
    <div class="veil" aria-hidden="true"></div>
    <Transition name="cap" mode="out-in">
      <div :key="s.id + s.title" class="caption" :aria-live="shown ? 'polite' : 'off'">
        <p class="cap-title"><span class="cap-badge mono" aria-hidden="true">{{ s.code }}</span>{{ s.scene.title }}</p>
        <p class="cap-line">{{ s.scene.line }}</p>
        <p class="cap-act">
          <router-link :to="`/${s.id}`" class="cap-go">{{ t('open', s.title) }} <Icon name="arrow" /></router-link>
          <span class="cap-count">{{ t('count', s.wallpapers.length * 2) }}</span>
        </p>
      </div>
    </Transition>
  </section>
</template>

<style scoped>
/* where it sits is the shell's business (App.vue); here only what it shows and how it comes and goes */
.layer { overflow: hidden; background: #000; height: 100vh; height: 100svh; min-height: 520px;
  transition: opacity .45s var(--ease-out), visibility 0s; }
.layer:not(.shown) { opacity: 0; visibility: hidden; pointer-events: none; transition: opacity .35s ease, visibility 0s linear .35s; }
.still { position: absolute; inset: 0; }
.still img { width: 100%; height: 100%; object-fit: cover; }
.still-enter-active, .still-leave-active { transition: opacity 1.2s var(--ease-out); }
.still-enter-from, .still-leave-to { opacity: 0; }
/* a floor of darkness where the words sit, so text never fights the light */
.veil { position: absolute; inset: auto 0 0 0; height: 42%; pointer-events: none;
  background: linear-gradient(to top, rgba(0, 0, 0, .92), rgba(0, 0, 0, .55) 45%, transparent); }
.caption { position: absolute; left: clamp(20px, 3vw, 48px); right: clamp(20px, 3vw, 48px); bottom: clamp(20px, 4vh, 44px);
  display: grid; gap: 10px; max-width: 760px; }
.cap-title { margin: 0; font-weight: 300; font-size: clamp(24px, 2.6vw, 40px); line-height: 1.1; text-wrap: balance; text-shadow: 0 0 20px #000; }
/* the chosen row's line badge, carried onto the stage */
.cap-badge { display: inline-grid; place-items: center; min-width: 2.6em; height: 1.6em; padding: 0 .45em; margin-right: .6em;
  vertical-align: .35em; border-radius: 6px; background: var(--tone); color: #000; font-size: .42em; letter-spacing: .06em; }
.cap-line { margin: 0; font-weight: 300; color: var(--fg); opacity: .78; max-width: 58ch; text-shadow: 0 0 14px #000; }
.cap-act { margin: 4px 0 0; display: flex; align-items: center; flex-wrap: wrap; gap: 8px 22px; }
.cap-go { display: inline-flex; align-items: center; gap: 12px; min-height: 44px; padding: 0 18px; border: 1px solid var(--tone);
  color: var(--tone); text-decoration: none; background: #000; transition: background-color .3s, color .3s; }
.cap-go:hover { background: var(--tone); color: #000; }
.cap-go svg { width: 18px; height: 18px; transition: transform .5s var(--ease-out); }
.cap-go:hover svg { transform: translateX(5px); }
.cap-count { font-size: 14px; color: var(--dim); }
.cap-enter-active { transition: opacity .7s var(--ease-out) .35s, transform .7s var(--ease-out) .35s, filter .7s var(--ease-out) .35s; }
.cap-leave-active { transition: opacity .3s ease, filter .3s ease; }
.cap-enter-from { opacity: 0; transform: translateY(10px); filter: blur(6px); }
.cap-leave-to { opacity: 0; filter: blur(4px); }

/* ---------- phones: the front page's stage on top, the rail's board right under it ---------- */
@media (max-width: 860px) {
  .layer { height: 50vh; height: 50svh; min-height: 320px; border-bottom: 1px solid var(--line); }
  .layer:not(.home) { display: none; }
  .caption { gap: 6px; }
  .cap-line { font-size: 14px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
}
@media (prefers-reduced-motion: reduce) {
  .cap-enter-active, .cap-leave-active, .still-enter-active, .still-leave-active { transition: none; }
}
</style>
