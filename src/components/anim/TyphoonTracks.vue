<script setup>
// Every typhoon since 1951, each storm drawing its own track as its season arrives.
// The bright head is the storm's eye; the trail stays as a thin line coloured by pressure.
import Stage from './Stage.vue'
import { load, meta, ramp, rgba, glowSprite } from './data.js'
import { t } from '../../i18n.js'

const pColor = ramp([[905, [1, 1, 1]], [935, [.7, 1, 1]], [960, [.1, .9, 1]], [985, [0, .55, 1]], [1006, [.05, .22, .95]]])
let Y0 = 1951, Y1 = 2026                 // replaced by the exported range in init()
let P, OFF, storms = [], layer, lctx, active = [], next = 0
const head = glowSprite([.75, 1, 1], 48)

async function init() {
  P = await load('typhoons.f32'); OFF = await load('typhoons_offsets.u32', Uint32Array)
  const m = (await meta()).typhoons; if (m.y1) { Y0 = m.y0; Y1 = m.y1 + 1 }
  // spread each season's storms evenly through its year
  const byYear = {}
  for (let s = 0; s < OFF.length - 1; s++) {
    const y = P[OFF[s] * 7 + 6]; (byYear[y] ||= []).push(s)
  }
  storms = []
  for (const y of Object.keys(byYear).map(Number).sort((a, b) => a - b)) {
    const list = byYear[y]
    list.forEach((s, i) => {
      let minP = 2000
      for (let j = OFF[s]; j < OFF[s + 1]; j++) minP = Math.min(minP, P[j * 7 + 4])
      storms.push({ s, start: y + i / list.length, strong: minP <= 930 })
    })
  }
}
function reset({ w, h }) {
  layer = document.createElement('canvas'); layer.width = w * 2; layer.height = h * 2
  lctx = layer.getContext('2d'); lctx.scale(2, 2); lctx.globalCompositeOperation = 'lighter'; lctx.lineCap = 'round'
  active = []; next = 0
}
function segment(map, s, from, to, strong) {
  for (let j = Math.max(OFF[s] + 1, from); j <= to && j < OFF[s + 1]; j++) {
    const a = (j - 1) * 7, b = j * 7
    const [x0, y0] = map(P[a], P[a + 1], P[a + 2], P[a + 3])
    const [x1, y1] = map(P[b], P[b + 1], P[b + 2], P[b + 3])
    const pres = P[b + 4], extra = P[b + 5] === 6
    const c = pColor(pres)
    const strength = Math.min(Math.max((1000 - pres) / 60, 0), 1.6)
    lctx.strokeStyle = rgba(extra ? [c[0] * .5, c[1] * .45, c[2] * .8] : c, strong ? 0.18 + 0.4 * strength : 0.07)
    lctx.lineWidth = strong ? 0.6 + 0.9 * strength : 0.5
    lctx.beginPath(); lctx.moveTo(x0, y0); lctx.lineTo(x1, y1); lctx.stroke()
  }
}
function draw({ ctx, w, h, p, dt, map, still }) {
  const year = Y0 + (Y1 - Y0) * p
  while (next < storms.length && storms[next].start <= year) {
    const st = storms[next++]
    if (still) segment(map, st.s, OFF[st.s] + 1, OFF[st.s + 1] - 1, st.strong)
    else active.push({ ...st, pos: OFF[st.s], done: OFF[st.s] })
  }
  for (const a of active) {                        // each storm walks its track in ~1.4 s
    const len = OFF[a.s + 1] - OFF[a.s]
    a.pos = Math.min(a.pos + dt * len / 1.4, OFF[a.s + 1] - 1)
    const upto = Math.floor(a.pos)
    if (upto > a.done) { segment(map, a.s, a.done + 1, upto, a.strong); a.done = upto }
  }
  ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h)
  ctx.drawImage(layer, 0, 0, w, h)
  ctx.globalCompositeOperation = 'lighter'
  const k = Math.min(w, h) / 700
  for (const a of active) {
    const j = Math.floor(a.pos), f = a.pos - j, o = j * 7, o2 = Math.min(j + 1, OFF[a.s + 1] - 1) * 7
    const [x0, y0] = map(P[o], P[o + 1], P[o + 2], P[o + 3]); const [x1, y1] = map(P[o2], P[o2 + 1], P[o2 + 2], P[o2 + 3])
    const pres = P[o + 4], s = (a.strong ? 7 : 3.5) * k * (0.6 + Math.min(Math.max((1000 - pres) / 60, 0), 1.6) * 0.5)
    ctx.globalAlpha = a.strong ? 0.95 : 0.45
    ctx.drawImage(head, x0 + (x1 - x0) * f - s, y0 + (y1 - y0) * f - s, s * 2, s * 2)
  }
  active = active.filter((a) => a.pos < OFF[a.s + 1] - 1)
  ctx.globalAlpha = 1
}
const counter = (p) => String(Math.min(Y1 - 1, Math.floor(Y0 + (Y1 - Y0) * p)))
</script>

<template>
  <Stage :label="t('anim').typhoons[0]" :duration="30" :hold="5"
         :init="init" :reset="reset" :draw="draw" :counter="counter" :caption="t('anim').typhoons[1]" />
</template>
