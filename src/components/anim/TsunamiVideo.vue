<script setup>
// Pre-rendered simulation (289 frames, one per 5 simulated minutes, 24 fps).
// The counter converts video time to hours after the earthquake.
import { ref, onMounted, onBeforeUnmount } from 'vue'
import Icon from '../Icon.vue'
import { t } from '../../i18n.js'
const base = import.meta.env.BASE_URL
// `playing` mirrors the video's own play/pause events, so the button stays truthful when the
// browser refuses autoplay (iOS Low Power Mode, data saver); `wanted` is the visitor's choice
const v = ref(null), hours = ref('+0:00'), playing = ref(false)
let raf = 0, io, visible = true
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
let wanted = !reduce
function tick() {
  raf = requestAnimationFrame(tick)
  if (!v.value) return
  const simMin = Math.round(v.value.currentTime * 24 * 5)     // frames x 5 minutes
  hours.value = `+${Math.floor(simMin / 60)}:${String(simMin % 60).padStart(2, '0')}`
}
function sync() { if (wanted && visible) v.value.play().catch(() => {}); else v.value.pause() }
function toggle() { wanted = !playing.value; sync() }
function replay() { v.value.currentTime = 0; wanted = true; sync() }
onMounted(() => {
  if (reduce) v.value.currentTime = 7
  raf = requestAnimationFrame(tick)
  // rest off-screen, like the canvas stages
  io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; sync() }, { threshold: 0.05 })
  io.observe(v.value)
})
onBeforeUnmount(() => { cancelAnimationFrame(raf); io?.disconnect() })
</script>

<template>
  <figure class="tv" :aria-label="t('anim').tsunami[0]">
    <video ref="v" :poster="`${base}video/tsunami_poster.webp`" muted loop playsinline preload="auto"
           :aria-label="t('anim').tsunami[2]" @play="playing = true" @pause="playing = false">
      <source :src="`${base}video/tsunami.webm`" type="video/webm" />
      <source :src="`${base}video/tsunami.mp4`" type="video/mp4" />
    </video>
    <figcaption class="cap">{{ t('anim').tsunami[1] }}</figcaption>
    <div class="counter mono">{{ hours }}</div>
    <div class="controls">
      <button type="button" class="ctl" :aria-pressed="!playing" :aria-label="playing ? t('pauseAnim') : t('playAnim')" @click="toggle"><Icon :name="playing ? 'pause' : 'play'" /><span class="t">{{ playing ? t('pause') : t('play') }}</span></button>
      <button type="button" class="ctl" :aria-label="t('replayAnim')" @click="replay"><Icon name="replay" /><span class="t">{{ t('replay') }}</span></button>
    </div>
  </figure>
</template>

<style scoped>
.tv { position: relative; margin: 0; background: #000; border: 1px solid var(--line); overflow: hidden; }
video { width: 100%; height: auto; aspect-ratio: 16 / 9; display: block; object-fit: cover; }
.counter { position: absolute; right: clamp(12px, 2vw, 24px); bottom: clamp(8px, 1.6vw, 18px); font-size: clamp(28px, 5vw, 64px); font-weight: 300; color: var(--accent); font-variant-numeric: tabular-nums; pointer-events: none; text-shadow: 0 0 24px #000; }
.cap { position: absolute; left: clamp(12px, 2vw, 24px); top: clamp(10px, 1.6vw, 18px); font-size: 13px; color: var(--dim); text-shadow: 0 0 6px #000; pointer-events: none; }
.controls { position: absolute; left: clamp(12px, 2vw, 24px); bottom: clamp(10px, 1.6vw, 18px); display: flex; gap: 6px; }
@container pane (max-width: 640px) { .controls .t { display: none; } }
@container pane (max-width: 640px) { video { aspect-ratio: 4 / 3; } }
</style>
