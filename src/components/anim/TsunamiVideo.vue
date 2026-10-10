<script setup>
// Pre-rendered simulation of the tsunami striking Japan (tsunami_japan_render.py), about 12 s at 24 fps.
// public/data/tsunami_marks.json gives every frame's simulated minute and camera box, so the counter
// and the labels follow the video: the epicentre pulses as it starts, and each place appears when
// the simulated wave reaches it, staying on its place while the camera zooms out.
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import Icon from '../Icon.vue'
import { t } from '../../i18n.js'
const base = import.meta.env.BASE_URL
// `playing` mirrors the video's own play/pause events, so the button stays truthful when the
// browser refuses autoplay (iOS Low Power Mode, data saver); `wanted` is the visitor's choice
const v = ref(null), playing = ref(false), fi = ref(0), marks = ref(null)
let raf = 0, io, visible = true
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
let wanted = !reduce
fetch(`${base}data/tsunami_marks.json`).then((r) => r.ok && r.json()).then((m) => { marks.value = m || null }).catch(() => {})
const L = computed(() => t('anim').tsunamiMarks)
const minutes = computed(() => marks.value?.minutes[Math.min(fi.value, marks.value.minutes.length - 1)] ?? 0)
const hours = computed(() => { const m = Math.round(minutes.value); return `+${Math.floor(m / 60)}:${String(m % 60).padStart(2, '0')}` })
// a lon/lat place -> its spot on the current frame, as fractions; null once the camera has left it
function at([lo, la]) {
  const [x0, x1, y0, y1] = marks.value.box[Math.min(fi.value, marks.value.box.length - 1)]
  const x = (lo - x0) / (x1 - x0), y = (y1 - la) / (y1 - y0)
  return x < 0 || x > 1 || y < 0 || y > 1 ? null : [x, y]
}
const JAPAN = [139.6, 39.6]                     // the name, over the land in northern Honshu, clear of the buttons
const pos = ([x, y]) => ({ left: `${x * 100}%`, top: `${y * 100}%` })
const shown = computed(() => {
  if (!marks.value) return []
  const out = []
  const [, , y0, y1] = marks.value.box[Math.min(fi.value, marks.value.box.length - 1)]
  for (const p of marks.value.places) {
    if (p.near && y1 - y0 > 12) continue          // the close-up's places, once the camera has zoomed out
    const q = at(p.at)
    if (q && minutes.value >= p.minutes) out.push({ key: p.key, q, text: L.value.at(L.value[p.key], p.minutes) })
  }
  return out
})
function tick() {
  raf = requestAnimationFrame(tick)
  if (v.value && marks.value) fi.value = Math.floor(v.value.currentTime * marks.value.fps)
}
function sync() { if (wanted && visible) v.value.play().catch(() => {}); else v.value.pause() }
function toggle() { wanted = !playing.value; sync() }
function replay() { v.value.currentTime = 0; wanted = true; sync() }
onMounted(() => {
  if (reduce) v.value.currentTime = 5            // reduced motion: rest on the wave striking the coast
  raf = requestAnimationFrame(tick)
  // rest off-screen, like the canvas stages
  io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; sync() }, { threshold: 0.05 })
  io.observe(v.value)
})
onBeforeUnmount(() => { cancelAnimationFrame(raf); io?.disconnect() })
</script>

<template>
  <figure class="tv" :aria-label="t('anim').tsunami[0]">
    <!-- the frame keeps the video's 16:9 even where the figure crops it to 4:3, so the labels stay on their places -->
    <div class="frame">
      <video ref="v" :poster="`${base}video/tsunami_poster.webp`" muted loop playsinline preload="auto"
             :aria-label="t('anim').tsunami[2]" @play="playing = true" @pause="playing = false">
        <source :src="`${base}video/tsunami.webm`" type="video/webm" />
        <source :src="`${base}video/tsunami.mp4`" type="video/mp4" />
      </video>
      <div v-if="marks" class="marks" aria-hidden="true">
        <span v-if="at(JAPAN)" class="jp" :style="pos(at(JAPAN))">{{ L.japan }}</span>
        <!-- the epicentre is named while the wave leaves it, then only ringed, so the coast's names have room -->
        <span v-if="at(marks.epicentre)" class="mk epi" :class="{ quake: minutes < 10 }" :style="pos(at(marks.epicentre))"><i /><b v-if="minutes < 20">{{ L.epicentre }}</b></span>
        <span v-for="p in shown" :key="p.key" class="mk on" :class="{ left: p.q[0] > 0.65, up: p.q[1] > 0.8, down: p.q[1] < 0.2 }"
              :style="pos(p.q)"><i /><b>{{ p.text }}</b></span>
      </div>
    </div>
    <figcaption class="cap">{{ t('anim').tsunami[1] }}</figcaption>
    <div class="counter mono">{{ hours }}</div>
    <div class="controls">
      <button type="button" class="ctl" :aria-pressed="!playing" :aria-label="playing ? t('pauseAnim') : t('playAnim')" @click="toggle"><Icon :name="playing ? 'pause' : 'play'" /><span class="t">{{ playing ? t('pause') : t('play') }}</span></button>
      <button type="button" class="ctl" :aria-label="t('replayAnim')" @click="replay"><Icon name="replay" /><span class="t">{{ t('replay') }}</span></button>
    </div>
  </figure>
</template>

<style scoped>
.tv { position: relative; margin: 0; background: #000; border: 1px solid var(--line); overflow: hidden; width: 100%; aspect-ratio: 16 / 9; }
.frame { position: absolute; inset: 0; }
video { width: 100%; height: 100%; display: block; }
.counter { position: absolute; right: clamp(12px, 2vw, 24px); bottom: clamp(8px, 1.6vw, 18px); font-size: clamp(28px, 5vw, 64px); font-weight: 300; color: var(--accent); font-variant-numeric: tabular-nums; pointer-events: none; text-shadow: 0 0 24px #000; }
.cap { position: absolute; left: clamp(12px, 2vw, 24px); top: clamp(10px, 1.6vw, 18px); font-size: 13px; color: var(--dim); text-shadow: 0 0 6px #000; pointer-events: none; }
.controls { position: absolute; left: clamp(12px, 2vw, 24px); bottom: clamp(10px, 1.6vw, 18px); display: flex; gap: 6px; }

/* labels: a ring on the place, the name beside it, a black halo over the beams */
.marks { position: absolute; inset: 0; pointer-events: none; font-size: 12px; line-height: 1; }
.marks > span { position: absolute; white-space: nowrap; text-shadow: 0 0 4px #000, 0 0 8px #000; }
.jp { transform: translate(-50%, -50%); color: #ffcf8a; font-size: 13px; letter-spacing: .04em; }
.mk i { position: absolute; left: -4px; top: -4px; width: 8px; height: 8px; border: 1px solid var(--dim); border-radius: 50%; box-shadow: 0 0 0 1px #000; }
.mk b { position: absolute; left: 10px; top: -14px; font-weight: 400; color: var(--dim); }
.mk.left b { left: auto; right: 10px; }
/* near the bottom: above the ring, clear of the Play and Replay buttons; near the top: below it, clear of the caption */
.mk.up b { top: -28px; left: 2px; }
.mk.down b { top: 6px; }
.mk.on { animation: in .6s var(--ease-out); }
@keyframes in { from { opacity: 0; } }
.epi b { color: var(--fg); }
/* the first moments: the epicentre rings out */
.epi.quake i::after { content: ''; position: absolute; inset: -1px; border: 1px solid var(--fg); border-radius: 50%; animation: ring 1s var(--ease-out) infinite; }
@keyframes ring { from { transform: scale(1); opacity: 1; } to { transform: scale(5); opacity: 0; } }
@media (prefers-reduced-motion: reduce) { .epi.quake i::after, .mk.on { animation: none; } }

@container pane (max-width: 640px) {
  .controls .t { display: none; }
  /* the middle 4:3 of the 16:9 video */
  .tv { aspect-ratio: 4 / 3; }
  .frame { inset: 0 auto; width: 133.333%; left: -16.667%; }
  .marks { font-size: 11px; }
}
</style>
