<script setup>
// The front page's live stage: one WebGL canvas, the same N points of light for every scene.
// Flat scenes are importance-sampled from the wallpapers (export_particles.py); Fuji is real 3D.
// `index` chooses the scene; on a change every particle flies, with its own delay and a swirl,
// from its place in the current scene to its place in the chosen one.
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import gsap from 'gsap'
import { ui } from '../i18n.js'

const props = defineProps({
  scenes: { type: Array, required: true },      // [{ file, threeD }]
  index: { type: Number, default: 0 },
  active: { type: Boolean, default: true },     // false while the stage is hidden: no frames drawn
})
const emit = defineEmits(['unsupported', 'ready'])
const base = import.meta.env.BASE_URL
const canvas = ref(null)

let gl, prog, raf = 0, io, ro, visible = true, intro = 0, startT = 0, loaded = false
let N = 0, set = 'd', buffers = [], randBuf, aspectFrame = 16 / 9, W = 0, H = 0, dpr = 1
let alive = true, uni = {}, attr = {}, morph, from = 0, to = 0
const m = { t: 1 }                                         // 0 = scene `from`, 1 = scene `to`
const abort = new AbortController()
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches

const VS = `
attribute vec3 aPos; attribute vec4 aCol; attribute vec3 bPos; attribute vec4 bCol; attribute float aRnd;
uniform float uT, uTime, uCanvas, uFrame, uFit, uA3, uB3, uRot, uPx, uIntro;
varying vec4 vCol;
const float PI = 3.14159265;
vec2 fitFlat(vec2 p) {                 // fit the scene frame into the canvas, between cover (0) and contain (1)
  vec2 cover = uCanvas > uFrame ? vec2(p.x, p.y * uCanvas / uFrame) : vec2(p.x * uFrame / uCanvas, p.y);
  vec2 contain = uCanvas > uFrame ? vec2(p.x * uFrame / uCanvas, p.y) : vec2(p.x, p.y * uCanvas / uFrame);
  return mix(cover, contain, uFit);
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
  for (const n of ['uT', 'uTime', 'uCanvas', 'uFrame', 'uFit', 'uA3', 'uB3', 'uRot', 'uPx', 'uIntro', 'uGain']) uni[n] = gl.getUniformLocation(prog, n)
  for (const n of ['aPos', 'aCol', 'bPos', 'bCol', 'aRnd']) attr[n] = gl.getAttribLocation(prog, n)
  return true
}
function bindScene(buf, posName, colName) {
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.enableVertexAttribArray(attr[posName]); gl.vertexAttribPointer(attr[posName], 3, gl.UNSIGNED_SHORT, true, 10, 0)
  gl.enableVertexAttribArray(attr[colName]); gl.vertexAttribPointer(attr[colName], 4, gl.UNSIGNED_BYTE, true, 10, 6)
}
// stored as uint16 (-1..1 mapped to 0..65535); the shader reads 0..1 and remaps with * 2 - 1
function upload(ab) {
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(gl.ARRAY_BUFFER, new Uint16Array(ab), gl.STATIC_DRAW)
  return buf
}
function size() {
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  W = canvas.value.clientWidth; H = canvas.value.clientHeight
  canvas.value.width = Math.round(W * dpr); canvas.value.height = Math.round(H * dpr)
  gl?.viewport(0, 0, canvas.value.width, canvas.value.height)
}

function frame(now) {
  raf = requestAnimationFrame(frame)
  if (!visible || !props.active || !loaded || !W || !H) return
  const time = (now - startT) / 1000
  intro = reduce ? 1 : Math.min(1, Math.max(0, time / 2.8))
  bindScene(buffers[from], 'aPos', 'aCol'); bindScene(buffers[to], 'bPos', 'bCol')
  gl.uniform1f(uni.uT, m.t); gl.uniform1f(uni.uTime, reduce ? 0 : time)
  gl.uniform1f(uni.uCanvas, W / H); gl.uniform1f(uni.uFrame, aspectFrame)
  gl.uniform1f(uni.uFit, 0.5)                             // the stage is near square: show most of each wide scene
  gl.uniform1f(uni.uA3, props.scenes[from].threeD ? 1 : 0); gl.uniform1f(uni.uB3, props.scenes[to].threeD ? 1 : 0)
  gl.uniform1f(uni.uRot, (reduce ? 0 : time * 0.22) + 0.6)
  gl.uniform1f(uni.uPx, Math.max(1.4, Math.min(W, H) / 640 * 1.5) * dpr)
  gl.uniform1f(uni.uIntro, intro)
  gl.uniform1f(uni.uGain, set === 'd' ? 0.5 : 0.6)
  gl.clear(gl.COLOR_BUFFER_BIT)
  gl.drawArrays(gl.POINTS, 0, N)
}

// a new destination: the cloud leaves from whichever scene it shows most of right now
function go(i) {
  if (i === to && m.t >= 1) return
  from = m.t < 0.5 ? from : to
  to = i
  morph?.kill()
  if (reduce) { m.t = 1; from = to; return }
  m.t = 0
  morph = gsap.to(m, { t: 1, duration: 1.9, ease: 'none' })
}
watch(() => props.index, (i) => { if (loaded) go(i) })

async function get(url) {
  const r = await fetch(url, { signal: abort.signal })
  if (!r.ok) throw new Error(`${url}: ${r.status}`)
  return r
}
// stream each scene so the loading screen shows real bytes, not a guess
async function loadScenes() {
  const meta = await (await get(`${base}particles/meta.json`)).json()
  N = meta.sets[set].n; aspectFrame = meta.sets[set].aspect
  const L = window.hikariLoader
  const total = N * 10 * props.scenes.length, got = new Array(props.scenes.length).fill(0)
  const report = () => L?.set(0.12 + 0.83 * got.reduce((a, b) => a + b, 0) / total,
    `${ui('gathering')} · ${Math.round(100 * got.reduce((a, b) => a + b, 0) / total)}%`)
  return Promise.all(props.scenes.map(async (s, i) => {
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
function begin() { startT = performance.now() }
// a lost context (GPU reset, too many tabs) or missing data falls back to the stills
const lost = (e) => { e.preventDefault(); if (alive) emit('unsupported') }

onMounted(async () => {
  try { if (!setup()) return emit('unsupported') } catch (e) { console.error(e); return emit('unsupported') }
  canvas.value.addEventListener('webglcontextlost', lost)
  window.hikariLoader?.set(0.1, ui('gathering'))
  size()
  set = W / H < 0.9 ? 'p' : 'd'
  let bins
  try { bins = await loadScenes() } catch (e) {
    if (alive) { console.error(e); emit('unsupported') }
    return
  }
  if (!alive) return                                     // left the page while the data was arriving
  const L = window.hikariLoader
  L?.set(0.97, ui('lighting'))
  buffers = bins.map(upload)
  const rnd = new Float32Array(N); for (let i = 0; i < N; i++) rnd[i] = Math.random()
  randBuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, randBuf); gl.bufferData(gl.ARRAY_BUFFER, rnd, gl.STATIC_DRAW)
  gl.enableVertexAttribArray(attr.aRnd); gl.vertexAttribPointer(attr.aRnd, 1, gl.FLOAT, false, 0, 0)
  from = to = props.index; m.t = 1
  loaded = true
  emit('ready')
  if (!L || L.closed) begin(); else { startT = Infinity; addEventListener('hikari:revealed', begin, { once: true }); L.done() }
  raf = requestAnimationFrame(frame)
  io = new IntersectionObserver(([e]) => { visible = e.isIntersecting }, { threshold: 0 })
  io.observe(canvas.value)
  ro = new ResizeObserver(size); ro.observe(canvas.value)
})
onBeforeUnmount(() => {
  alive = false; abort.abort()
  cancelAnimationFrame(raf); io?.disconnect(); ro?.disconnect(); morph?.kill()
  removeEventListener('hikari:revealed', begin)
  // free the GPU now: browsers cap live WebGL contexts, and every visit to the front page makes one
  canvas.value?.removeEventListener('webglcontextlost', lost)
  if (gl) { for (const b of [...buffers, randBuf]) if (b) gl.deleteBuffer(b); gl.getExtension('WEBGL_lose_context')?.loseContext() }
})
</script>

<template>
  <canvas ref="canvas" class="particle-stage" aria-hidden="true"></canvas>
</template>

<style scoped>
.particle-stage { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
</style>
