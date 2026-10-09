<script setup>
// The sakura front as a season: a date line sweeps from January to May and every city
// blooms (all 66 years at once) as the line passes its first-bloom date.
// Desktop: date left -> right, latitude bottom -> top. Narrow screens: date top -> bottom.
import Stage from './Stage.vue'
import { load, meta } from './data.js'
import { t, lang } from '../../i18n.js'

let S, n = 0, M, flowers = [], petals = [], bloomIdx = 0, layer, lctx, live = []
const WHITE = [1, .97, .98], PINK = [1, .42, .66]
const MONTHS = [['Jan', 1], ['Feb', 32], ['Mar', 60], ['Apr', 91], ['May', 121], ['Jun', 152]]

function petalSprite(c, r) {     // five soft petals, notched tips
  const s = document.createElement('canvas'), n = Math.ceil(r * 2.6); s.width = s.height = n
  const g = s.getContext('2d'); g.translate(n / 2, n / 2)
  const col = `rgb(${c.map((v) => Math.round(v * 255)).join(',')})`
  for (let i = 0; i < 5; i++) {
    g.rotate((Math.PI * 2) / 5)
    const grad = g.createRadialGradient(0, -r * .55, 0, 0, -r * .55, r * .6)
    grad.addColorStop(0, col); grad.addColorStop(1, 'rgba(0,0,0,0)')
    g.fillStyle = grad
    g.beginPath(); g.ellipse(0, -r * .55, r * .36, r * .55, 0, 0, Math.PI * 2); g.fill()
  }
  g.fillStyle = 'rgba(255,240,245,0.9)'; g.beginPath(); g.arc(0, 0, r * .12, 0, Math.PI * 2); g.fill()
  return s
}
async function init() {
  S = await load('sakura.f32'); M = (await meta()).sakura; n = S.length / 4
  const steps = 10
  for (let i = 0; i < steps; i++) {
    const t = Math.pow(i / (steps - 1), 1.2)
    petals.push(petalSprite(WHITE.map((v, k) => v * (1 - t) + PINK[k] * t), 24))
  }
}
function layout(w, h, portrait) {
  const mx = portrait ? 0.12 : 0.07, my = portrait ? 0.1 : 0.12
  // wide: room above for the month marks under the caption, and below for the controls
  const top = Math.max(h * my, 76), bot = Math.max(h * my, 68)
  return (a, b) => portrait
    ? [w * mx + b * w * (1 - 2 * mx), h * my + a * h * (1 - 2 * my)]
    : [w * mx + a * w * (1 - 2 * mx), h - bot - b * (h - top - bot)]
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
  lctx.fillStyle = '#6e6268'; lctx.textBaseline = 'middle'
  for (const [name, doy] of MONTHS) {
    if (doy < M.doy0 || doy > M.doy1) continue      // a mark past the axis would land on the counter or the controls
    const a = (doy - M.doy0) / (M.doy1 - M.doy0)
    const [x, y] = L(a, 0)
    if (portrait) { lctx.textAlign = 'left'; lctx.fillText(name, 6, y) }
    else { lctx.textAlign = 'center'; lctx.fillText(name, x, L(a, 1)[1] - 18) }    // above the plot, clear of the Pause button
  }
  lctx.fillStyle = '#8a7b82'
  for (const c of M.cities) {
    const [x, y] = L(c.a, c.b)
    if (portrait) { lctx.textAlign = 'center'; lctx.fillText(c.name, x, y - 14) }
    else { lctx.textAlign = 'right'; lctx.fillText(c.name, x - 12, y) }
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
  ctx.strokeStyle = 'rgba(255,143,191,0.35)'; ctx.lineWidth = 1
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
  <Stage :label="t('anim').sakura[0]" :duration="18" :hold="5"
         :init="init" :reset="reset" :draw="draw" :counter="counter" :caption="t('anim').sakura[1]" />
</template>
