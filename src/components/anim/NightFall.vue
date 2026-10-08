<script setup>
// Nightfall across Japan on the autumn equinox: the sun sets first over Iturup and eastern Hokkaido, last
// over the Ryukyus, and every light comes on as dusk reaches it. Each pixel knows the minute its
// sun sets (NOAA's solar equations, computed in night.py); the clock is Japan time.
import Stage from './Stage.vue'
import { meta } from './data.js'
import { t } from '../../i18n.js'

const base = import.meta.env.BASE_URL
const FADE = 22                                  // minutes from sunset to full light
let M, sets = {}, frame = null

function image(src) {
  return new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src })
}
function pixels(img) {
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height
  const g = c.getContext('2d'); g.drawImage(img, 0, 0)
  return g.getImageData(0, 0, img.width, img.height).data
}
async function init() {
  M = (await meta()).night
  for (const tag of ['d', 'p']) {
    const [light, time] = await Promise.all([image(`${base}data/night_${tag}.webp`), image(`${base}data/night_${tag}_t.png`)])
    const canvas = document.createElement('canvas'); canvas.width = light.width; canvas.height = light.height
    const g = canvas.getContext('2d')
    sets[tag] = { L: pixels(light), T: pixels(time), canvas, g, out: g.createImageData(light.width, light.height),
                  t0: M[tag][0], t1: M[tag][1], w: light.width, h: light.height }
  }
}
function reset() { frame = null }
const span = (s) => [s.t0 - 8, s.t1 + FADE + 4]          // from just before the first sunset to full dark
function minute(p, s) { const [a, b] = span(s); return a + (b - a) * p }
function draw({ ctx, w, h, portrait, p }) {
  const s = sets[portrait ? 'p' : 'd']
  const now = minute(p, s), L = s.L, T = s.T, O = s.out.data, k = (s.t1 - s.t0) / 254
  for (let i = 0; i < L.length; i += 4) {
    const c = T[i]
    if (!c) { O[i + 3] = 255; O[i] = O[i + 1] = O[i + 2] = 0; continue }
    let a = (now - (s.t0 + (c - 1) * k)) / FADE
    a = a <= 0 ? 0 : a >= 1 ? 1 : a * a * (3 - 2 * a)
    O[i] = L[i] * a; O[i + 1] = L[i + 1] * a; O[i + 2] = L[i + 2] * a; O[i + 3] = 255
  }
  s.g.putImageData(s.out, 0, 0)
  ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h)
  ctx.imageSmoothingQuality = 'high'
  if (portrait) { const full = w * 2796 / 1290; ctx.drawImage(s.canvas, 0, -(full - h) / 2, w, full) }
  else ctx.drawImage(s.canvas, 0, 0, w, h)
}
function counter(p) {
  if (!M) return ''
  const m = Math.round(minute(p, sets.d || { t0: M.d[0], t1: M.d[1] }))
  return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')} JST`
}
</script>

<template>
  <Stage :label="t('anim').night[0]" :duration="20" :hold="5"
         :init="init" :reset="reset" :draw="draw" :counter="counter" :caption="t('anim').night[1]" />
</template>
