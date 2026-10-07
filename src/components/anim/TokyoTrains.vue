<script setup>
// Tokyo's network in official line colours, with trains running along every line.
// Trains are bright dots shuttling end to end; the Shinkansen run faster, in white.
import Stage from './Stage.vue'
import { load, meta, rgba, glowSprite } from './data.js'

let T, lines = [], base, trains = [], clock = 0
async function init() {
  T = await load('trains_tokyo.f32'); lines = (await meta()).trains.lines
}
function reset({ w, h, map }) {
  base = document.createElement('canvas'); base.width = w * 2; base.height = h * 2
  const b = base.getContext('2d'); b.scale(2, 2); b.globalCompositeOperation = 'lighter'; b.lineJoin = 'round'
  trains = []
  for (const L of lines) {
    const pts = []
    for (let i = 0; i < L.n; i++) { const o = (L.o + i) * 4; pts.push(map(T[o], T[o + 1], T[o + 2], T[o + 3])) }
    const cum = [0]
    for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    const len = cum[cum.length - 1]
    if (len < 4) continue
    b.strokeStyle = rgba(L.c, L.s ? 0.55 : 0.35); b.lineWidth = L.s ? 1.6 : 1
    b.beginPath(); pts.forEach(([x, y], i) => (i ? b.lineTo(x, y) : b.moveTo(x, y))); b.stroke()
    const count = Math.max(1, Math.round(len / (L.s ? 160 : 70)))
    const spr = glowSprite(L.s ? [1, 1, 1] : L.c.map((v) => Math.min(1, v * 1.15 + .1)), 32)
    for (let k = 0; k < count; k++) trains.push({ pts, cum, len, d: (k / count) * len * 2, v: (L.s ? 90 : 34) * (0.8 + 0.4 * ((k * 37) % 10) / 10), spr, big: L.s })
  }
  clock = 0
}
function at(t, d) {                 // position along the polyline at distance d (ping-pong)
  d = d % (2 * t.len); if (d > t.len) d = 2 * t.len - d
  let lo = 0, hi = t.cum.length - 1
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (t.cum[m] < d) lo = m; else hi = m }
  const f = (d - t.cum[lo]) / Math.max(t.cum[hi] - t.cum[lo], 1e-6)
  return [t.pts[lo][0] + (t.pts[hi][0] - t.pts[lo][0]) * f, t.pts[lo][1] + (t.pts[hi][1] - t.pts[lo][1]) * f]
}
function draw({ ctx, w, h, dt }) {
  clock += dt
  ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h)
  ctx.drawImage(base, 0, 0, w, h)
  ctx.globalCompositeOperation = 'lighter'
  const k = Math.min(w, h) / 700
  for (const t of trains) {
    t.d += t.v * k * dt
    const [x, y] = at(t, t.d), s = (t.big ? 7 : 4.5) * k
    ctx.globalAlpha = 0.9
    ctx.drawImage(t.spr, x - s, y - s, s * 2, s * 2)
  }
  ctx.globalAlpha = 1
}
const counter = () => {
  const d = new Date(); return d.toLocaleTimeString('en-GB', { timeZone: 'Asia/Tokyo', hour: '2-digit', minute: '2-digit' }) + ' JST'
}
</script>

<template>
  <Stage label="Animation: trains moving along every railway line in central Tokyo, in official line colours" :duration="1e9" :hold="0"
         :init="init" :reset="reset" :draw="draw" :counter="counter" caption="Central Tokyo · trains illustrative, not timetable" />
</template>
