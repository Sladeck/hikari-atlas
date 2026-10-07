<script setup>
// 30,167 earthquakes appearing in time order, 1973 -> 2026. New quakes flash, then settle
// into a persistent layer of light. M7+ send out a ring. 2011 lights up the whole trench.
import Stage from './Stage.vue'
import { load, ramp, glowSprite } from './data.js'

const depthColor = ramp([[0, [1, .86, .62]], [60, [1, .45, .18]], [150, [.9, .16, .3]], [350, [.55, .2, .85]], [650, [.25, .35, 1]]])
const Y0 = 1973, Y1 = 2026.8
let Q, n = 0, layer, lctx, idx = 0, flashes = [], rings = []
const PALETTE = 24                       // quantise depth colours so sprites can be cached
const sprites = []

async function init() {
  Q = await load('quakes.f32'); n = Q.length / 7
  for (let i = 0; i < PALETTE; i++) sprites.push(glowSprite(depthColor(i / (PALETTE - 1) * 650), 64))
}
function reset({ w, h }) {
  layer = document.createElement('canvas'); layer.width = w * 2; layer.height = h * 2
  lctx = layer.getContext('2d'); lctx.scale(2, 2); lctx.globalCompositeOperation = 'lighter'
  idx = 0; flashes = []; rings = []
}
const sprite = (d) => sprites[Math.min(PALETTE - 1, Math.round(Math.min(d, 650) / 650 * (PALETTE - 1)))]

function draw({ ctx, w, h, p, dt, map, still }) {
  const year = Y0 + (Y1 - Y0) * p
  const k = Math.min(w, h) / 700                       // size scale
  while (idx < n && Q[idx * 7 + 6] <= year) {
    const o = idx * 7
    const [x, y] = map(Q[o], Q[o + 1], Q[o + 2], Q[o + 3])
    const m = Q[o + 4], d = Q[o + 5]
    const r = Math.max(1.2, 1.5 * k * Math.pow(1.38, m - 4.5))
    lctx.globalAlpha = 0.22
    lctx.drawImage(sprite(d), x - r * 2, y - r * 2, r * 4, r * 4)
    if (!still) flashes.push({ x, y, r, d, life: 1 })
    if (m >= 7 && !still) rings.push({ x, y, m, life: 1, d })
    idx++
  }
  ctx.globalCompositeOperation = 'source-over'
  ctx.globalAlpha = 1
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h)
  ctx.drawImage(layer, 0, 0, w, h)
  ctx.globalCompositeOperation = 'lighter'
  for (const f of flashes) {                            // fresh quakes: bright, larger, fading
    const s = f.r * (2 + 4 * f.life)
    ctx.globalAlpha = 0.55 * f.life
    ctx.drawImage(sprite(f.d), f.x - s, f.y - s, s * 2, s * 2)
    f.life -= dt * 1.6
  }
  flashes = flashes.filter((f) => f.life > 0)
  for (const g of rings) {                              // M7+: an expanding ring
    const R = (1 - g.life) * 60 * k * Math.pow(1.6, g.m - 7)
    ctx.globalAlpha = 0.7 * g.life
    ctx.strokeStyle = `rgb(${depthColor(g.d).map((c) => Math.round(c * 255)).join(',')})`
    ctx.lineWidth = 1.2
    ctx.beginPath(); ctx.arc(g.x, g.y, R, 0, Math.PI * 2); ctx.stroke()
    g.life -= dt * 0.6
  }
  rings = rings.filter((g) => g.life > 0)
  ctx.globalAlpha = 1
}
const counter = (p) => String(Math.min(2026, Math.floor(Y0 + (Y1 - Y0) * p)))
</script>

<template>
  <Stage label="Animation: earthquakes around Japan appearing year by year from 1973 to 2026" :duration="26" :hold="5"
         :init="init" :reset="reset" :draw="draw" :counter="counter" caption="M4.5+ · USGS" />
</template>
