<script setup>
// Every confirmed eruption in Japan since 1600, year by year, over the faint land of the wallpapers.
// Each eruption bursts at its start, as bright and as wide as its VEI, glows for as long as it lasted
// and cools to an ember afterwards; a volcano that has never erupted in the record stays dark.
import Stage from './Stage.vue'
import { meta, rgba, glowSprite } from './data.js'
import { t } from '../../i18n.js'

const base = import.meta.env.BASE_URL
// VEI -> colour, as on the stripes: deep red for small eruptions, white for the largest
const VEI = [[.70, .12, .10], [.95, .30, .12], [1, .55, .20], [1, .78, .42], [1, .93, .78], [1, 1, 1]]
const col = (v) => VEI[Math.min(Math.max(v < 0 ? 1 : v, 0), VEI.length - 1)]
let V = [], E = [], Y0 = 1600, Y1 = 2026, land = { d: null, p: null }
const sprites = VEI.map((c) => glowSprite(c, 48))
const core = glowSprite([1, .97, .9], 24)
let heat = []                                    // per volcano: the ember left by its last eruption

function image(src) {
  return new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src })
}
async function init() {
  const m = (await meta()).volcanoes
  V = m.v; E = m.e; Y0 = m.y0; Y1 = m.y1
  ;[land.d, land.p] = await Promise.all([image(`${base}data/volcano_land_d.webp`), image(`${base}data/volcano_land_p.webp`)])
}
function reset() { heat = V.map(() => ({ t: -1e9, v: 0 })) }
function draw({ ctx, w, h, portrait, p, map }) {
  const year = Y0 + (Y1 + 1 - Y0) * p
  ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h)
  ctx.globalAlpha = 0.28                           // the land stays a whisper under the fire
  if (portrait) { const full = w * 2796 / 1290; ctx.drawImage(land.p, 0, -(full - h) / 2, w, full) }
  else ctx.drawImage(land.d, 0, 0, w, h)
  ctx.globalCompositeOperation = 'lighter'
  const k = Math.min(w, h) / 600
  for (const [vi, s, f, vei] of E) {                // eruptions under way this year leave their heat
    if (s > year) break
    if (f >= heat[vi].t) heat[vi] = { t: Math.min(f, year), v: Math.max(vei, 0), end: f }
  }
  for (let i = 0; i < V.length; i++) {
    const [x, y] = map(V[i][0], V[i][1], V[i][2], V[i][3])
    const hh = heat[i]
    // every volcano with eruptions since 1600 keeps a faint coal; recent ones glow, then cool over ~25 years
    const since = year - hh.t
    const live = hh.end >= year
    const glow = live ? 1 : Math.exp(-Math.max(since, 0) / 25)
    const r = (live ? 10 + 4.5 * hh.v : 5 + 2 * hh.v) * k * (0.5 + 0.5 * glow)
    ctx.globalAlpha = 0.12 + 0.88 * glow
    ctx.drawImage(sprites[Math.min(hh.v, 5)], x - r, y - r, r * 2, r * 2)
    if (live) { ctx.globalAlpha = 1; const c = 3.2 * k; ctx.drawImage(core, x - c, y - c, c * 2, c * 2) }
  }
  // the burst at the start of each eruption: a ring of light spreading for a couple of years
  for (const [vi, s, , vei] of E) {
    if (s > year) break
    const age = year - s
    if (age > 2.5) continue
    const [x, y] = map(V[vi][0], V[vi][1], V[vi][2], V[vi][3])
    const r = (6 + 7 * Math.max(vei, 0)) * k * (0.3 + age / 2.5)
    ctx.globalAlpha = 0.5 * (1 - age / 2.5)
    ctx.strokeStyle = rgba(col(vei), 1); ctx.lineWidth = 1.2 * k
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke()
  }
  ctx.globalAlpha = 1
}
const counter = (p) => String(Math.min(Y1, Math.floor(Y0 + (Y1 + 1 - Y0) * p)))
</script>

<template>
  <Stage :label="t('anim').volcanoes[0]" :duration="28" :hold="5"
         :init="init" :reset="reset" :draw="draw" :counter="counter" :caption="t('anim').volcanoes[1]" />
</template>
