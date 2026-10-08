<script setup>
// Sunrise on Fuji: the contour render is revealed from the summit outwards, the way first
// light reaches the top of the mountain before its foot. GSAP drives the mask radius.
import { ref, onMounted, onBeforeUnmount } from 'vue'
import gsap from 'gsap'
import Icon from '../Icon.vue'
import { t } from '../../i18n.js'
const base = import.meta.env.BASE_URL
const el = ref(null), elev = ref('3,776 m'), playing = ref(true)
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
let tl, io, visible = true
// summit position in the desktop render (fraction of width / height)
const SX = 0.5, SY = 0.471
const setR = (r) => el.value?.style.setProperty('--r', r + '%')
function play() {
  tl?.kill(); playing.value = true
  const o = { r: 0 }
  tl = gsap.timeline({ repeat: -1, repeatDelay: 1.5, paused: !visible })
  // close the mask while the picture is faded out, so the loop restarts from darkness
  tl.fromTo(o, { r: 0 }, { r: 120, duration: 9, ease: 'power1.inOut', onUpdate: () => setR(o.r) })
    .to(el.value, { opacity: 0, duration: 1.2, delay: 2 })
    .call(() => setR(0))
    .set(el.value, { opacity: 1 })
}
function toggle() { if (!tl) return play(); playing.value = !playing.value; tl.paused(!playing.value || !visible) }
function replay() { if (reduce) { tl?.kill(); setR(140); return } play() }
onMounted(() => {
  if (reduce) { setR(140); playing.value = false; return }
  play()
  // rest off-screen, like the canvas stages
  io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; tl?.paused(!playing.value || !visible) }, { threshold: 0.05 })
  io.observe(el.value)
})
onBeforeUnmount(() => { tl?.kill(); io?.disconnect() })
</script>

<template>
  <figure class="fuji" :aria-label="t('anim').fuji[0]">
    <picture ref="el" class="reveal" :style="{ '--sx': SX * 100 + '%', '--sy': SY * 100 + '%' }">
      <source media="(max-width: 640px)" :srcset="`${base}wallpapers/preview/fuji_phone.webp`" />
      <img :src="`${base}wallpapers/preview/fuji_desktop.webp`" alt="" width="1920" height="1080" />
    </picture>
    <figcaption class="cap">{{ t('anim').fuji[1] }}</figcaption>
    <div class="counter mono">{{ elev }}</div>
    <div class="controls">
      <button v-if="!reduce" type="button" class="ctl" :aria-pressed="!playing" :aria-label="playing ? t('pauseAnim') : t('playAnim')" @click="toggle"><Icon :name="playing ? 'pause' : 'play'" /><span class="t">{{ playing ? t('pause') : t('play') }}</span></button>
      <button type="button" class="ctl" :aria-label="t('replayFuji')" @click="replay"><Icon name="replay" /><span class="t">{{ t('replay') }}</span></button>
    </div>
  </figure>
</template>

<style scoped>
.fuji { position: relative; margin: 0; background: #000; border: 1px solid var(--line); overflow: hidden; }
.reveal { display: block; --r: 0%;
  -webkit-mask-image: radial-gradient(circle at var(--sx) var(--sy), #000 calc(var(--r) - 6%), transparent var(--r));
          mask-image: radial-gradient(circle at var(--sx) var(--sy), #000 calc(var(--r) - 6%), transparent var(--r)); }
.reveal img { width: 100%; height: auto; aspect-ratio: 16 / 9; object-fit: cover; }
.counter { position: absolute; right: clamp(12px, 2vw, 24px); bottom: clamp(8px, 1.6vw, 18px); font-size: clamp(28px, 5vw, 64px); font-weight: 300; color: var(--accent); font-variant-numeric: tabular-nums; pointer-events: none; text-shadow: 0 0 24px #000; }
.cap { position: absolute; left: clamp(12px, 2vw, 24px); top: clamp(10px, 1.6vw, 18px); font-size: 13px; color: var(--dim); text-shadow: 0 0 6px #000; pointer-events: none; }
.controls { position: absolute; left: clamp(12px, 2vw, 24px); bottom: clamp(10px, 1.6vw, 18px); display: flex; gap: 6px; }
@container pane (max-width: 640px) { .controls .t { display: none; } }
@container pane (max-width: 640px) { .reveal img { aspect-ratio: 3 / 4; object-position: 50% 30%; } .reveal { --sy: 55% !important; } }
</style>
