<script setup>
// Every river in Japan flowing from its springs down to the sea. A front moves seaward, kilometre by
// kilometre of distance to the sea along the rivers themselves, and each reach lights up from its
// upstream end downwards as the front passes it: the far headwaters of the long rivers first, deep in
// the mountains, then the tributaries joining them, and every river reaches the sea together.
// The counter is how far the water has come from the farthest spring; it ends on the longest river.
// Each reach is as bright and as wide as the water it carries, coloured like the wallpaper.
import Stage from './Stage.vue'
import { load, meta, ramp, rgba, glowSprite } from './data.js'
import { t } from '../../i18n.js'

// log10 discharge (m3/s) -> colour: indigo trickles, blue streams, ice-white great rivers
const flow = ramp([[-1, [.22, .26, .85]], [-0.1, [.25, .52, 1]], [0.85, [.55, .78, 1]], [1.7, [.86, .94, 1]], [2.6, [1, 1, 1]]])
let PT, OFF, RE, order = [], N = 0, MAX = 300
let layer, lctx, next = 0, active = []
const tip = glowSprite([.8, .92, 1], 32)

async function init() {
  [PT, OFF, RE] = await Promise.all([load('rivers.u16', Uint16Array), load('rivers_offsets.u32', Uint32Array), load('rivers_reach.u16', Uint16Array)])
  MAX = (await meta()).rivers?.maxKm || MAX
  N = OFF.length - 1
  // farthest from the sea first, by the reach's upstream end (its distance to the sea plus its length)
  order = Array.from({ length: N }, (_, i) => i).sort((a, b) => (RE[b * 3] + RE[b * 3 + 1]) - (RE[a * 3] + RE[a * 3 + 1]))
}
function reset({ w, h }) {
  layer = document.createElement('canvas'); layer.width = w * 2; layer.height = h * 2
  lctx = layer.getContext('2d'); lctx.scale(2, 2); lctx.globalCompositeOperation = 'lighter'; lctx.lineCap = 'round'; lctx.lineJoin = 'round'
  next = 0; active = []
}
const K = 1 / 65535
function xy(map, j) { const o = j * 4; return map(PT[o] * K, PT[o + 1] * K, PT[o + 2] * K, PT[o + 3] * K) }
function style(r, k) {
  const q = RE[r * 3 + 2] / 100, s = Math.sqrt(Math.min(q, 400) / 400)
  lctx.strokeStyle = rgba(flow(Math.log10(Math.max(q, 0.1))), 0.28 + 0.62 * s)
  lctx.lineWidth = (0.45 + 2.2 * s) * k
}
// the reach's points run downstream, the way the water goes: draw points fromK..toK in that order
function stroke(map, r, fromK, toK, k) {
  const a = OFF[r], n = OFF[r + 1] - a
  if (toK <= fromK || n < 2) return
  style(r, k)
  lctx.beginPath()
  let [x, y] = xy(map, a + fromK); lctx.moveTo(x, y)
  for (let s = fromK + 1; s <= toK; s++) { [x, y] = xy(map, a + s); lctx.lineTo(x, y) }
  lctx.stroke()
}
function draw({ ctx, w, h, p, map, still }) {
  const k = Math.min(w, h) / 700
  const front = MAX * Math.pow(1 - p, 1.7)           // distance left to the sea: quick in the mountains, slow on the busy coasts
  if (still) {
    for (let r = 0; r < N; r++) stroke(map, r, 0, OFF[r + 1] - OFF[r] - 1, k)
    next = N
  } else {
    while (next < N && (RE[order[next] * 3] + RE[order[next] * 3 + 1]) / 100 >= front) active.push({ r: order[next++], done: 0 })
    for (const a of active) {
      const len = Math.max(RE[a.r * 3 + 1] / 100, 0.01), n = OFF[a.r + 1] - OFF[a.r] - 1
      const top = RE[a.r * 3] / 100 + len                 // the reach's upstream end, in km to the sea
      const upto = p >= 1 ? n : Math.min(n, Math.floor(n * (top - front) / len))
      if (upto > a.done) { stroke(map, a.r, a.done, upto, k); a.done = upto }
    }
  }
  ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h)
  ctx.drawImage(layer, 0, 0, w, h)
  // a spark at the head of the water in the larger rivers
  ctx.globalCompositeOperation = 'lighter'
  for (const a of active) {
    const q = RE[a.r * 3 + 2] / 100
    if (q < 8) continue
    const [x, y] = xy(map, OFF[a.r] + a.done), s = (2 + 3 * Math.sqrt(Math.min(q, 400) / 400)) * k
    ctx.globalAlpha = 0.8; ctx.drawImage(tip, x - s, y - s, s * 2, s * 2)
  }
  ctx.globalAlpha = 1
  active = active.filter((a) => a.done < OFF[a.r + 1] - OFF[a.r] - 1)
}
// the last frame holds the longest river's exact length; on the way there, whole kilometres
const counter = (p) => (p >= 1 ? `${MAX.toFixed(1)} km` : `${Math.round(MAX - MAX * Math.pow(1 - p, 1.7))} km`)
</script>

<template>
  <Stage :label="t('anim').rivers[0]" :duration="22" :hold="5"
         :init="init" :reset="reset" :draw="draw" :counter="counter" :caption="t('anim').rivers[1]" />
</template>
