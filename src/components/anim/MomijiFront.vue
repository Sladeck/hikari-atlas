<script setup>
// The autumn leaf front as a season: a date line sweeps from October into January and a maple leaf
// lands at every city (all 73 autumns at once) as the line passes the day its leaves turned red.
// Gold for the 1950s, crimson for the last autumns, so the crimson trails behind: autumn comes later.
// Desktop: date left -> right, latitude bottom -> top. Narrow screens: date top -> bottom.
import Stage from './Stage.vue'
import { load, meta } from './data.js'
import { t, lang } from '../../i18n.js'

let S, n = 0, M, flowers = [], petals = [], bloomIdx = 0, layer, lctx, live = []
const WHITE = [1, .80, .32], PINK = [.98, .16, .20]      // gold (1953) -> crimson (2025)
const MONTHS = [['Oct', 274], ['Nov', 305], ['Dec', 335], ['Jan', 366]]

function petalSprite(c, r) {     // a maple leaf: a palm with five pointed lobes and a short stem
  const s = document.createElement('canvas'), n = Math.ceil(r * 2.6); s.width = s.height = n
  const g = s.getContext('2d'); g.translate(n / 2, n / 2)
  const col = `rgb(${c.map((v) => Math.round(v * 255)).join(',')})`
  const lobes = [[0, 1], [0.95, 0.92], [-0.95, 0.92], [1.85, 0.68], [-1.85, 0.68]]
  g.fillStyle = col; g.shadowColor = col; g.shadowBlur = r * 0.35
  g.beginPath()
  const pts = []
  for (const [a, L] of lobes) pts.push([a, L])
  pts.sort((p, q) => p[0] - q[0])
  g.moveTo(Math.sin(-2.6) * r * 0.42, -Math.cos(-2.6) * r * 0.42)
  for (const [a, L] of pts) {
    g.lineTo(Math.sin(a - 0.42) * r * 0.46, -Math.cos(a - 0.42) * r * 0.46)
    g.lineTo(Math.sin(a) * r * L, -Math.cos(a) * r * L)
    g.lineTo(Math.sin(a + 0.42) * r * 0.46, -Math.cos(a + 0.42) * r * 0.46)
  }
  g.lineTo(Math.sin(2.6) * r * 0.42, -Math.cos(2.6) * r * 0.42)
  g.closePath(); g.fill()
  g.shadowBlur = 0; g.strokeStyle = col; g.lineWidth = Math.max(1, r * 0.08)
  g.beginPath(); g.moveTo(0, 0); g.lineTo(0, r * 0.62); g.stroke()
  return s
}
async function init() {
  S = await load('momiji.f32'); M = (await meta()).momiji; n = S.length / 4
  const steps = 10
  for (let i = 0; i < steps; i++) {
    const t = Math.pow(i / (steps - 1), 1.2)
    petals.push(petalSprite(WHITE.map((v, k) => v * (1 - t) + PINK[k] * t), 24))
  }
}
function layout(w, h, portrait) {
  const mx = portrait ? 0.12 : 0.07, my = portrait ? 0.1 : 0.12
  return (a, b) => portrait
    ? [w * mx + b * w * (1 - 2 * mx), h * my + a * h * (1 - 2 * my)]
    : [w * mx + a * w * (1 - 2 * mx), h * (1 - my) - b * h * (1 - 2 * my)]
}
function reset({ w, h, portrait }) {
  layer = document.createElement('canvas'); layer.width = w * 2; layer.height = h * 2
  lctx = layer.getContext('2d'); lctx.scale(2, 2)
  const L = layout(w, h, portrait)
  // sort every bloom by date so the sweep only has to walk forward
  flowers = []
  let seed = 7
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647)
  for (let i = 0; i < n; i++) {
    const a = S[i * 4] + (rnd() - .5) / (M.doy1 - M.doy0), b = S[i * 4 + 1], y = S[i * 4 + 2]
    let [x, yy] = L(a, b)
    const jit = (rnd() - .5) * Math.min(w, h) * 0.012
    if (portrait) x += jit; else yy += jit
    flowers.push({ a, x, y: yy, t: (y - M.y0) / (M.y1 - M.y0), rot: rnd() * 6.28 })
  }
  flowers.sort((p, q) => p.a - q.a)
  bloomIdx = 0; live = []           // blossoms mid-bloom belong to the old layout
  // month ticks and city names, drawn once into the layer
  lctx.font = `300 ${portrait ? 11 : 12}px "IBM Plex Mono", monospace`
  lctx.fillStyle = '#6e665d'; lctx.textBaseline = 'middle'
  for (const [name, doy] of MONTHS) {
    const a = (doy - M.doy0) / (M.doy1 - M.doy0)
    const [x, y] = L(a, 0)
    if (portrait) { lctx.textAlign = 'left'; lctx.fillText(name, 6, y) }
    else { lctx.textAlign = 'center'; lctx.fillText(name, x, h * 0.95) }
  }
  lctx.fillStyle = '#8a7f74'
  for (const c of M.cities) {
    const [x, y] = L(c.a, c.b)
    if (portrait) { lctx.textAlign = 'center'; lctx.fillText(c.name, x, y + 14) }       // after the latest leaves
    else { lctx.textAlign = 'left'; lctx.fillText(c.name, x + 12, y) }
  }
  lctx.globalCompositeOperation = 'lighter'
}
function draw({ ctx, w, h, p, dt, portrait, still }) {
  const k = Math.min(w, h) / 700
  const r = (portrait ? 5 : 5.5) * k
  while (bloomIdx < flowers.length && flowers[bloomIdx].a <= p) {
    const f = flowers[bloomIdx++]
    if (still) stamp(f, r, 1)
    else live.push({ ...f, life: 0 })
  }
  ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h)
  ctx.drawImage(layer, 0, 0, w, h)
  ctx.globalCompositeOperation = 'lighter'
  for (const f of live) {                      // bloom: grow from a bud, then settle into the layer
    f.life += dt * 2.2
    const g = Math.min(f.life, 1), s = r * (0.3 + 0.9 * g) * (1 + 0.6 * (1 - g))
    drawFlower(ctx, f, s, 0.9)
    if (f.life >= 1) stamp(f, r, 1)
  }
  live = live.filter((f) => f.life < 1)
  // the date line
  const L = layout(w, h, portrait)
  const [lx, ly] = L(p, 0)
  ctx.globalCompositeOperation = 'source-over'
  ctx.strokeStyle = 'rgba(255,120,80,0.35)'; ctx.lineWidth = 1
  ctx.beginPath()
  if (portrait) { ctx.moveTo(0, ly); ctx.lineTo(w, ly) } else { ctx.moveTo(lx, 0); ctx.lineTo(lx, h) }
  ctx.stroke()
}
function drawFlower(c, f, s, alpha) {
  const spr = petals[Math.min(petals.length - 1, Math.round(f.t * (petals.length - 1)))]
  c.save(); c.globalAlpha = alpha; c.translate(f.x, f.y); c.rotate(f.rot)
  c.drawImage(spr, -s * 1.3, -s * 1.3, s * 2.6, s * 2.6); c.restore()
}
function stamp(f, r, a) { drawFlower(lctx, f, r, 0.75 * a) }
const counter = (p) => {
  const doy = Math.round(M ? M.doy0 + (M.doy1 - M.doy0) * p : 1)
  const d = new Date(2001, 0, 1); d.setDate(d.getDate() + doy - 1)
  return d.toLocaleDateString(lang.value === 'ja' ? 'ja-JP' : 'en-GB', { day: 'numeric', month: lang.value === 'ja' ? 'long' : 'short' })
}
</script>

<template>
  <Stage :label="t('anim').momiji[0]" :duration="18" :hold="5"
         :init="init" :reset="reset" :draw="draw" :counter="counter" :caption="t('anim').momiji[1]" />
</template>
