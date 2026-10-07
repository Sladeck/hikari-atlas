<script setup>
// Shared canvas stage for the live animations.
// Wide containers draw a 16:9 frame from the "desktop" projection; narrow ones a 3:4 crop
// of the "phone" projection. The loop pauses off-screen; reduced motion shows the final frame.
import { ref, onMounted, onBeforeUnmount } from 'vue'
import Icon from '../Icon.vue'

const props = defineProps({
  label: { type: String, required: true },
  duration: { type: Number, default: 20 },     // seconds for progress 0 -> 1
  hold: { type: Number, default: 4 },           // seconds to rest on the final frame
  init: { type: Function, default: async () => {} },
  reset: { type: Function, default: () => {} },
  draw: { type: Function, required: true },     // ({ctx, w, h, portrait, p, dt, map})
  counter: { type: Function, default: () => '' },
  caption: { type: String, default: '' },
})

const wrap = ref(null), canvas = ref(null)
const playing = ref(true), ready = ref(false), counterText = ref(''), failed = ref(false)
const PHONE_RATIO = 2796 / 1290
let ctx, w = 0, h = 0, portrait = false, raf = 0, last = 0, elapsed = 0, visible = true, io, ro
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches

// normalised data coords -> canvas px. (xd,yd) desktop 16:9 frame, (xp,yp) phone frame
function map(xd, yd, xp, yp) {
  if (!portrait) return [xd * w, yd * h]
  const full = w * PHONE_RATIO
  return [xp * w, yp * full - (full - h) / 2]
}

function size() {
  const r = wrap.value.getBoundingClientRect()
  portrait = r.width < 640
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  w = Math.round(r.width); h = Math.round(portrait ? r.width * 4 / 3 : r.width * 9 / 16)
  wrap.value.style.height = h + 'px'
  canvas.value.width = w * dpr; canvas.value.height = h * dpr
  canvas.value.style.width = w + 'px'; canvas.value.style.height = h + 'px'
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function restart() {
  elapsed = 0
  ctx.globalCompositeOperation = 'source-over'
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h)
  props.reset({ ctx, w, h, portrait, map })
}

function frame(t) {
  raf = requestAnimationFrame(frame)
  const dt = last ? Math.min((t - last) / 1000, 0.1) : 0
  last = t
  if (!playing.value || !visible) return
  elapsed += dt
  if (elapsed > props.duration + props.hold) restart()
  const p = Math.min(elapsed / props.duration, 1)
  props.draw({ ctx, w, h, portrait, p, dt, map })
  counterText.value = props.counter(p)
}

function still() {   // reduced motion or paused render of the final state
  restart()
  props.draw({ ctx, w, h, portrait, p: 1, dt: 0, map, still: true })
  counterText.value = props.counter(1)
  elapsed = props.duration          // Play resumes on the final frame's hold, then loops from the start
}

function toggle() {
  if (reduce && !raf) { playing.value = true; restart(); last = 0; raf = requestAnimationFrame(frame); return }
  playing.value = !playing.value; last = 0
}
function replay() { restart(); playing.value = true; last = 0; if (!raf) raf = requestAnimationFrame(frame) }

onMounted(async () => {
  ctx = canvas.value.getContext('2d')
  size()
  try { await props.init({ ctx, w, h, portrait, map }) } catch (e) { failed.value = true; console.error(e); return }
  ready.value = true
  if (reduce) { playing.value = false; still() } else { restart(); raf = requestAnimationFrame(frame) }
  io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; last = 0 }, { threshold: 0.05 })
  io.observe(wrap.value)
  let lastW = w
  ro = new ResizeObserver(() => {
    const nw = Math.round(wrap.value.getBoundingClientRect().width)
    if (Math.abs(nw - lastW) < 2) return
    lastW = nw; size(); if (playing.value && !reduce) restart(); else still()
  })
  ro.observe(wrap.value)
})
onBeforeUnmount(() => { cancelAnimationFrame(raf); io?.disconnect(); ro?.disconnect() })
</script>

<template>
  <figure ref="wrap" class="stage-wrap" :aria-label="label">
    <canvas ref="canvas" role="img" :aria-label="label"></canvas>
    <figcaption v-if="caption" class="cap">{{ caption }}</figcaption>
    <div class="counter mono" aria-live="off">{{ counterText }}</div>
    <div v-if="ready" class="controls">
      <button type="button" class="ctl" :aria-pressed="!playing" :aria-label="playing ? 'Pause animation' : 'Play animation'" @click="toggle"><Icon :name="playing ? 'pause' : 'play'" /><span class="t">{{ playing ? 'Pause' : 'Play' }}</span></button>
      <button type="button" class="ctl" aria-label="Replay animation from the start" @click="replay"><Icon name="replay" /><span class="t">Replay</span></button>
    </div>
    <p v-if="!ready && !failed" class="status mono">Loading data…</p>
    <p v-if="failed" class="status mono">The animation data could not load. The wallpapers below still work.</p>
  </figure>
</template>

<style scoped>
.stage-wrap { position: relative; margin: 0; background: #000; overflow: hidden; border: 1px solid var(--line); }
canvas { display: block; }
.counter { position: absolute; right: clamp(12px, 2vw, 24px); bottom: clamp(8px, 1.6vw, 18px); font-size: clamp(28px, 5vw, 64px); font-weight: 300; color: var(--accent); font-variant-numeric: tabular-nums; letter-spacing: -.02em; pointer-events: none; text-shadow: 0 0 24px #000, 0 0 8px #000; }
.cap { position: absolute; left: clamp(12px, 2vw, 24px); top: clamp(10px, 1.6vw, 18px); font-size: 13px; color: var(--dim); pointer-events: none; text-shadow: 0 0 6px #000; }
.controls { position: absolute; left: clamp(12px, 2vw, 24px); bottom: clamp(10px, 1.6vw, 18px); display: flex; gap: 6px; }
@media (max-width: 640px) { .controls .t { display: none; } }
.status { position: absolute; inset: 0; display: grid; place-items: center; margin: 0; color: var(--dim); font-size: 13px; padding: 16px; text-align: center; }
</style>
