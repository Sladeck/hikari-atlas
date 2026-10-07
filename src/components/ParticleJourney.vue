<script setup>
// The front page stage: one pinned WebGL canvas, the same N points of light for every scene.
// Flat scenes are importance-sampled from the wallpapers (export_particles.py); Fuji is real 3D.
// Scroll position chooses the scene; between scenes each particle flies, with its own delay and
// a swirl, from its place in one dataset to its place in the next.
import { ref, onMounted, onBeforeUnmount } from 'vue'
import gsap from 'gsap'
import Icon from './Icon.vue'
import { SECTIONS } from '../sections.js'

const emit = defineEmits(['unsupported'])
const base = import.meta.env.BASE_URL
const S = Object.fromEntries(SECTIONS.map((s) => [s.id, s]))

const SCENES = [
  { file: 'japan', sec: 'earthquakes', title: 'Every earthquake since 1973',
    line: '30,167 quakes of magnitude 4.5 and up. No coastline is drawn: the plates draw Japan by themselves.' },
  { file: 'tsunami', sec: 'tsunami', title: 'The 2011 tsunami crossing the Pacific',
    line: 'Undersea ridges bend the wave into beams aimed at Hawaii, Chile and New Zealand. Computed from the physics, not drawn.' },
  { file: 'typhoons', sec: 'typhoons', title: 'Seventy years of typhoons',
    line: 'Born in the tropics, they drift west, then curve north toward Japan. The white arcs fell below 930 hPa.' },
  { file: 'fuji3d', sec: 'fuji', threeD: true, title: 'Mount Fuji, built from light',
    line: 'Every point sits at its real place on the mountain, from 1,000 m up to the 3,776 m summit, slowly turning.' },
  { file: 'sakura', sec: 'sakura', title: 'The cherry blossom front',
    line: 'Sixty-six springs at 102 cities. The front leaves Okinawa in January and reaches Wakkanai in late May.' },
  { file: 'trains_tokyo', sec: 'railways', title: 'Tokyo, every line in its own colour',
    line: 'The green Yamanote loop, the orange Chūō line cutting through it, the Shinkansen in white.' },
]

const track = ref(null), canvas = ref(null)
const active = ref(0), loaded = ref(false), cueOut = ref(false), cueText = ref(true)
const alphas = ref(SCENES.map((_, i) => (i === 0 ? 1 : 0)))
let gl, prog, raf = 0, io, ro, visible = true, tPrev = 0, sCur = -1, intro = 0, startT = 0
let N = 0, set = 'd', buffers = [], randBuf, aspectFrame = 16 / 9, W = 0, H = 0, dpr = 1
let alive = true, uni = {}, attr = {}
const abort = new AbortController()

const VS = `
attribute vec3 aPos; attribute vec4 aCol; attribute vec3 bPos; attribute vec4 bCol; attribute float aRnd;
uniform float uT, uTime, uCanvas, uFrame, uA3, uB3, uRot, uPx, uIntro;
varying vec4 vCol;
const float PI = 3.14159265;
vec2 fitFlat(vec2 p) {                 // cover-fit the scene frame into the canvas, in clip space
  return uCanvas > uFrame ? vec2(p.x, p.y * uCanvas / uFrame) : vec2(p.x * uFrame / uCanvas, p.y);
}
vec3 project(vec3 p, float is3d) {     // returns clip xy + a size factor
  if (is3d < 0.5) return vec3(fitFlat(p.xy), 1.0);
  float c = cos(uRot), s = sin(uRot);
  vec2 r = vec2(p.x * c - p.y * s, p.x * s + p.y * c);
  float depth = r.y;                                   // + = away from the camera
  float persp = 1.0 / (1.0 + depth * 0.28);
  vec2 q = vec2(r.x, p.z * 1.6 + depth * 0.20 - 0.10) * persp;
  q *= 0.92;
  vec2 clip = uCanvas >= 1.0 ? vec2(q.x / uCanvas, q.y) : vec2(q.x, q.y * uCanvas);
  return vec3(clip * (uCanvas >= 1.0 ? 1.0 : 1.35), persp);
}
float ease(float t) { return t < 0.5 ? 4.0 * t * t * t : 1.0 - pow(-2.0 * t + 2.0, 3.0) / 2.0; }
void main() {
  // each particle leaves with its own delay so the cloud streams rather than jumps
  float t = ease(clamp(uT * 1.7 - aRnd * 0.7, 0.0, 1.0));
  vec3 A = project(aPos * 2.0 - 1.0, uA3), B = project(bPos * 2.0 - 1.0, uB3);
  vec2 p = mix(A.xy, B.xy, t);
  float swirl = sin(PI * t);
  float ang = aRnd * 6.2831 + uTime * 0.35;
  p += vec2(cos(ang), sin(ang)) * swirl * (0.18 + 0.35 * fract(aRnd * 7.31));
  // opening: everything converges out of a wide ring of darkness
  float it = ease(clamp(uIntro * 1.5 - aRnd * 0.5, 0.0, 1.0));
  vec2 start = vec2(cos(aRnd * 91.0), sin(aRnd * 57.0)) * (1.6 + fract(aRnd * 13.0));
  p = mix(start, p, it);
  vec4 col = mix(aCol, bCol, t);
  float tw = 0.86 + 0.14 * sin(uTime * 1.7 + aRnd * 60.0);
  vCol = vec4(col.rgb, col.a * tw * it);
  gl_Position = vec4(p, 0.0, 1.0);
  gl_PointSize = uPx * (0.75 + 1.35 * col.a) * mix(A.z, B.z, t) * (1.0 + swirl * 0.6);
}`
const FS = `
precision mediump float;
varying vec4 vCol;
uniform float uGain;
void main() {
  vec2 d = gl_PointCoord - 0.5;
  float r = dot(d, d) * 4.0;
  float a = exp(-r * 3.2);
  gl_FragColor = vec4(vCol.rgb * vCol.a * a * uGain, 1.0);
}`

function compile(type, src) {
  const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s)
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s))
  return s
}
function setup() {
  gl = canvas.value.getContext('webgl', { antialias: false, alpha: false, premultipliedAlpha: false, powerPreference: 'high-performance' })
  if (!gl) return false
  prog = gl.createProgram()
  gl.attachShader(prog, compile(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FS))
  gl.linkProgram(prog)
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog))
  gl.useProgram(prog)
  gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE)       // light adds up, never paints over
  gl.clearColor(0, 0, 0, 1)
  // looked up once: the frame loop sets ten uniforms and rebinds two scenes 60 times a second
  for (const n of ['uT', 'uTime', 'uCanvas', 'uFrame', 'uA3', 'uB3', 'uRot', 'uPx', 'uIntro', 'uGain']) uni[n] = gl.getUniformLocation(prog, n)
  for (const n of ['aPos', 'aCol', 'bPos', 'bCol', 'aRnd']) attr[n] = gl.getAttribLocation(prog, n)
  return true
}
function bindScene(buf, posName, colName) {
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  const p = attr[posName], c = attr[colName]
  gl.enableVertexAttribArray(p); gl.vertexAttribPointer(p, 3, gl.UNSIGNED_SHORT, true, 10, 0)
  gl.enableVertexAttribArray(c); gl.vertexAttribPointer(c, 4, gl.UNSIGNED_BYTE, true, 10, 6)
}
// stored as uint16 (-1..1 mapped to 0..65535); the shader reads 0..1 and remaps with * 2 - 1
function upload(ab) {
  const src = new Uint16Array(ab)
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(gl.ARRAY_BUFFER, src, gl.STATIC_DRAW)
  return buf
}

function size() {
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  W = canvas.value.clientWidth; H = canvas.value.clientHeight
  canvas.value.width = Math.round(W * dpr); canvas.value.height = Math.round(H * dpr)
  gl?.viewport(0, 0, canvas.value.width, canvas.value.height)
}

const hdr = () => parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--hdr')) || 0
function progress() {
  const r = track.value.getBoundingClientRect(), top = hdr()
  const span = r.height - (innerHeight - top)
  return Math.min(1, Math.max(0, (top - r.top) / Math.max(span, 1))) * (SCENES.length - 1)
}

function frame(now) {
  raf = requestAnimationFrame(frame)
  if (!visible || !loaded.value) return
  const dt = tPrev ? Math.min((now - tPrev) / 1000, 0.05) : 0.016; tPrev = now
  const target = progress()
  if (sCur < 0) sCur = target                             // first frame: start where the page is (Back restores mid-journey)
  sCur += (target - sCur) * Math.min(1, dt * 5)          // a little inertia: the cloud follows the scroll
  if (Math.abs(target - sCur) < 1e-4) sCur = target
  const time = (now - startT) / 1000
  intro = Math.min(1, Math.max(0, time / 2.8))

  const k = Math.min(Math.floor(sCur), SCENES.length - 2)
  const f = sCur - k
  const t = Math.min(1, Math.max(0, (f - 0.22) / 0.56))  // hold, fly, hold
  bindScene(buffers[k], 'aPos', 'aCol'); bindScene(buffers[k + 1], 'bPos', 'bCol')
  gl.uniform1f(uni.uT, t); gl.uniform1f(uni.uTime, time)
  gl.uniform1f(uni.uCanvas, W / H); gl.uniform1f(uni.uFrame, aspectFrame)
  gl.uniform1f(uni.uA3, SCENES[k].threeD ? 1 : 0); gl.uniform1f(uni.uB3, SCENES[k + 1].threeD ? 1 : 0)
  gl.uniform1f(uni.uRot, time * 0.22 + 0.6)
  gl.uniform1f(uni.uPx, Math.max(1.4, Math.min(W, H) / 640 * 1.5) * dpr)
  gl.uniform1f(uni.uIntro, intro)
  gl.uniform1f(uni.uGain, set === 'd' ? 0.5 : 0.6)
  gl.clear(gl.COLOR_BUFFER_BIT)
  gl.drawArrays(gl.POINTS, 0, N)

  // captions: each scene's words are fully present only while its picture holds still
  // (only handed to Vue when they change, so a resting page does not re-render every frame)
  const a = SCENES.map((_, i) => 1 - Math.min(1, Math.max(0, (Math.abs(sCur - i) - 0.14) / 0.2)))
  if (a.some((v, i) => Math.abs(v - alphas.value[i]) > 1e-3)) alphas.value = a
  // cue: shown while a scene rests (hidden mid-morph and on the last scene); text only on the first
  const near = Math.round(sCur)
  cueOut.value = Math.abs(sCur - near) > 0.12 || near >= SCENES.length - 1
  cueText.value = near === 0
  if (near !== active.value) { active.value = near; tint(SCENES[near].sec) }
}

function tint(id) {
  const s = S[id]
  gsap.to(document.documentElement, { '--accent': s.accent, '--accent2': s.accent2, duration: 0.8, ease: 'power2.out' })
}
// rail jumps glide at the pace of the morphs (~1.6 s per scene) so you watch the light re-form;
// any wheel, touch or key from the visitor takes control back immediately
let glide
function jump(i) {
  const r = track.value.getBoundingClientRect()
  const span = r.height - (innerHeight - hdr())
  const target = scrollY + r.top - hdr() + span * (i / (SCENES.length - 1))
  const scenes = Math.abs(i - progress())
  glide?.kill()
  const o = { y: scrollY }
  glide = gsap.to(o, { y: target, duration: Math.min(6, 0.9 + scenes * 1.6), ease: 'power2.inOut',
    onUpdate: () => window.scrollTo(0, o.y) })
}
const stopGlide = () => glide?.kill()

async function get(url) {
  const r = await fetch(url, { signal: abort.signal })
  if (!r.ok) throw new Error(`${url}: ${r.status}`)
  return r
}
// stream each scene so the loader shows real bytes, not a guess
async function loadScenes() {
  const meta = await (await get(`${base}particles/meta.json`)).json()
  N = meta.sets[set].n; aspectFrame = meta.sets[set].aspect
  const L = window.hikariLoader
  const total = N * 10 * SCENES.length, got = new Array(SCENES.length).fill(0)
  const report = () => L?.set(0.12 + 0.83 * got.reduce((a, b) => a + b, 0) / total,
    `Gathering light · ${Math.round(100 * got.reduce((a, b) => a + b, 0) / total)}%`)
  return Promise.all(SCENES.map(async (s, i) => {
    const r = await get(`${base}particles/${s.file}_${set}.bin`)
    let buf
    if (!r.body?.getReader) { buf = await r.arrayBuffer(); got[i] = buf.byteLength; report() }
    else {
      const reader = r.body.getReader(), parts = []
      for (;;) { const { done, value } = await reader.read(); if (done) break; parts.push(value); got[i] += value.length; report() }
      const out = new Uint8Array(got[i]); let o = 0; for (const p of parts) { out.set(p, o); o += p.length }
      buf = out.buffer
    }
    if (buf.byteLength !== N * 10) throw new Error(`${s.file}_${set}.bin: ${buf.byteLength} bytes, expected ${N * 10}`)
    return buf
  }))
}
// the cloud converges only once the loading screen has lifted, so the opening is seen
function begin() { startT = performance.now(); gsap.from('.j-hero > *', { opacity: 0, y: 14, filter: 'blur(6px)', duration: 1.2, stagger: 0.15, delay: 1.1, ease: 'expo.out' }) }
// a lost context (GPU reset, too many tabs) or missing data falls back to the still plates
const lost = (e) => { e.preventDefault(); if (alive) emit('unsupported') }

onMounted(async () => {
  try { if (!setup()) return emit('unsupported') } catch (e) { console.error(e); return emit('unsupported') }
  canvas.value.addEventListener('webglcontextlost', lost)
  window.hikariLoader?.set(0.1, 'Gathering light')
  size()
  set = W / H < 0.9 ? 'p' : 'd'
  let bins
  try { bins = await loadScenes() } catch (e) {
    if (alive) { console.error(e); emit('unsupported') }
    return
  }
  if (!alive) return                                     // left the page while the data was arriving
  const L = window.hikariLoader
  L?.set(0.97, 'Lighting')
  buffers = bins.map(upload)
  const rnd = new Float32Array(N); for (let i = 0; i < N; i++) rnd[i] = Math.random()
  randBuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, randBuf); gl.bufferData(gl.ARRAY_BUFFER, rnd, gl.STATIC_DRAW)
  gl.enableVertexAttribArray(attr.aRnd); gl.vertexAttribPointer(attr.aRnd, 1, gl.FLOAT, false, 0, 0)
  loaded.value = true
  tint('earthquakes')
  if (!L || L.closed) begin(); else { startT = Infinity; addEventListener('hikari:revealed', begin, { once: true }); L.done() }
  raf = requestAnimationFrame(frame)
  io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; tPrev = 0 }, { threshold: 0 })
  io.observe(track.value)
  ro = new ResizeObserver(size); ro.observe(canvas.value)
  for (const ev of ['wheel', 'touchstart', 'keydown']) addEventListener(ev, stopGlide, { passive: true })
})
onBeforeUnmount(() => {
  alive = false; abort.abort()
  cancelAnimationFrame(raf); io?.disconnect(); ro?.disconnect(); glide?.kill()
  for (const ev of ['wheel', 'touchstart', 'keydown']) removeEventListener(ev, stopGlide)
  removeEventListener('hikari:revealed', begin)
  // free the GPU now: browsers cap live WebGL contexts, and every visit to the front page makes one
  canvas.value?.removeEventListener('webglcontextlost', lost)
  if (gl) { for (const b of [...buffers, randBuf]) if (b) gl.deleteBuffer(b); gl.getExtension('WEBGL_lose_context')?.loseContext() }
})
</script>

<template>
  <section ref="track" class="journey" :style="{ height: `${SCENES.length * 125 + 25}svh` }" aria-label="Six views of Japan made of light">
    <div class="stage">
      <canvas ref="canvas" aria-hidden="true"></canvas>
      <div class="veil" aria-hidden="true"></div>

      <div class="j-hero" :style="{ opacity: alphas[0] }" :aria-hidden="alphas[0] < 0.5">
        <h1><span lang="ja">光の地図</span>Hikari Atlas</h1>
        <p>Japan drawn only with light, from real data. Every point you see is a measurement. Scroll, and the same light rebuilds itself as a tsunami, typhoons, Mount Fuji, cherry blossoms and Tokyo's railways.</p>
      </div>

      <template v-for="(s, i) in SCENES" :key="s.file">
        <router-link v-if="i > 0" :to="`/${s.sec}`" class="j-cap" :style="{ opacity: alphas[i], '--tone': S[s.sec].accent, pointerEvents: alphas[i] > 0.6 ? 'auto' : 'none' }" :tabindex="alphas[i] > 0.6 ? 0 : -1" :aria-hidden="alphas[i] < 0.5">
          <span class="j-kanji" lang="ja" aria-hidden="true"><span v-for="(c, k) in S[s.sec].kanji" :key="k">{{ c }}</span></span>
          <span class="j-text">
            <span class="j-title">{{ s.title }}</span>
            <span class="j-line">{{ s.line }}</span>
            <span class="j-go">Open {{ S[s.sec].title }} <Icon name="arrow" /></span>
          </span>
        </router-link>
      </template>

      <button type="button" class="cue" :class="{ out: cueOut }" aria-label="Scroll to the next scene" @click="jump(Math.min(active + 1, SCENES.length - 1))">
        <span class="cue-line" aria-hidden="true"><span class="cue-dot"></span></span>
        <span class="cue-text" :class="{ hide: !cueText }"><span class="wide">Scroll</span><span class="narrow">Swipe up</span></span>
      </button>

      <nav class="rail" aria-label="Jump to a scene">
        <button v-for="(s, i) in SCENES" :key="s.file" type="button" :class="{ on: active === i }" :style="{ '--tone': S[s.sec].accent }"
                :aria-label="`Show ${s.title}`" :aria-current="active === i ? 'step' : undefined" @click="jump(i)">
          <span lang="ja" aria-hidden="true">{{ S[s.sec].kanji[0] }}</span>
        </button>
      </nav>
      <p v-if="!loaded" class="loading">Gathering light…</p>
    </div>
  </section>
</template>

<style scoped>
.journey { position: relative; }
.stage { position: sticky; top: var(--hdr, 0px); height: calc(100vh - var(--hdr, 0px)); height: calc(100svh - var(--hdr, 0px)); overflow: hidden; background: #000; }
canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
/* a soft floor of darkness where the words sit, so text never fights the light */
.veil { position: absolute; inset: auto 0 0 0; height: 46%; pointer-events: none;
  background: linear-gradient(to top, rgba(0, 0, 0, .94), rgba(0, 0, 0, .7) 40%, transparent); }

.j-hero { position: absolute; left: var(--gutter); right: var(--gutter); bottom: clamp(32px, 8vh, 96px); display: grid; gap: 18px; max-width: 760px; }
.j-hero h1 { margin: 0; font-weight: 300; font-size: clamp(48px, 8vw, 120px); line-height: .92; letter-spacing: -.025em; }
.j-hero h1 span { display: block; font-family: var(--mincho); font-weight: 700; font-size: .36em; letter-spacing: .32em; color: var(--accent); margin-bottom: .55em; }
.j-hero p { margin: 0; max-width: 56ch; font-weight: 300; font-size: clamp(16px, 1.4vw, 19px); text-shadow: 0 0 18px #000; }
.j-hero { padding-bottom: 72px; }
/* scroll cue: a drop of light falling down a thin line, centred at the foot of the screen */
.cue { position: absolute; left: 50%; bottom: clamp(16px, 4vh, 40px); translate: -50% 0; z-index: 2;
  display: grid; justify-items: center; gap: 10px; background: none; border: 0; cursor: pointer; color: var(--fg);
  transition: opacity .6s var(--ease-out), translate .6s var(--ease-out); }
.cue.out { opacity: 0; translate: -50% 12px; pointer-events: none; }
.cue-line { position: relative; width: 1px; height: 64px; overflow: hidden;
  background: linear-gradient(to top, transparent, color-mix(in srgb, var(--accent) 45%, transparent)); }
.cue-dot { position: absolute; left: -2px; bottom: -8px; width: 5px; height: 14px; border-radius: 3px; background: var(--accent);
  box-shadow: 0 0 10px var(--accent), 0 0 22px var(--accent); animation: rise 1.9s cubic-bezier(.55, 0, .45, 1) infinite; }
@keyframes rise { 0% { transform: translateY(0); opacity: 0; } 15% { opacity: 1; } 85% { opacity: 1; } 100% { transform: translateY(-72px); opacity: 0; } }
.cue-text { font-size: 13px; letter-spacing: .22em; text-transform: uppercase; color: var(--fg); }
.cue .narrow { display: none; }
.cue-text { transition: opacity .5s var(--ease-out); }
.cue-text.hide { opacity: 0; }
@media (hover: none) { .cue .wide { display: none; } .cue .narrow { display: inline; } }
@media (prefers-reduced-motion: reduce) { .cue-dot { animation: none; bottom: 50%; } }

.j-cap { position: absolute; left: var(--gutter); right: calc(var(--gutter) + 56px); bottom: clamp(28px, 7vh, 88px);
  display: grid; grid-template-columns: auto minmax(0, 1fr); gap: clamp(16px, 3vw, 36px); align-items: end;
  text-decoration: none; color: var(--fg); max-width: 920px; }
.j-kanji { font-family: var(--mincho); font-weight: 700; font-size: clamp(64px, 10vw, 150px); line-height: 1; color: var(--tone);
  display: flex; flex-direction: column; text-shadow: 0 0 40px color-mix(in srgb, var(--tone) 35%, transparent); }
.j-text { display: grid; gap: 10px; padding-bottom: .4em; }
.j-title { font-weight: 300; font-size: clamp(26px, 3.4vw, 46px); line-height: 1.08; text-wrap: balance; text-shadow: 0 0 20px #000; }
.j-line { font-weight: 300; color: var(--fg); opacity: .78; max-width: 58ch; text-shadow: 0 0 14px #000; }
.j-go { display: inline-flex; align-items: center; gap: 10px; color: var(--tone); min-height: 44px; }
.j-go svg { width: 18px; height: 18px; transition: transform .5s var(--ease-out); }
.j-cap:hover .j-go svg { transform: translateX(6px); }
.j-cap:focus-visible { outline: 2px solid var(--tone); outline-offset: 8px; }

.rail { position: absolute; right: clamp(10px, 2vw, 28px); top: 50%; translate: 0 -50%; display: grid; gap: 4px; }
.rail button { width: 44px; height: 44px; display: grid; place-items: center; background: transparent; border: 0; cursor: pointer;
  font-family: var(--mincho); font-size: 17px; color: var(--edge); transition: color .4s, transform .4s var(--ease-out); }
.rail button:hover { color: var(--fg); }
.rail button.on { color: var(--tone); transform: scale(1.25); text-shadow: 0 0 16px color-mix(in srgb, var(--tone) 60%, transparent); }
.loading { position: absolute; inset: 0; display: grid; place-items: center; margin: 0; color: var(--dim); font-size: 14px; }

@media (max-width: 700px) {
  .j-cap { grid-template-columns: minmax(0, 1fr); gap: 4px; right: calc(var(--gutter) + 40px); }
  .j-kanji { flex-direction: row; font-size: 52px; }
  .j-line { font-size: 15px; }
  .rail { right: 4px; }
  .rail button { width: 40px; height: 44px; font-size: 15px; }
  .veil { height: 58%; }
  .j-hero { gap: 12px; padding-bottom: 96px; }
  .j-hero p { font-size: 15px; }
}
</style>
