<script setup>
// Front page: the strongest stills, one plate per chapter, full bleed, no video.
// Each still is uncovered by its own logic as it scrolls in (the "develop" effect):
//   tsunami   a wavefront ring spreading from the epicentre
//   fuji      light stepping down from the summit, ring by ring
//   izu       a sweep along the trench
//   typhoons  a sweep up from the tropics toward Japan
//   tokyo     light radiating from Tokyo Station
//   sakura    the calendar, January to May
// Driven by CSS scroll timelines (animation-timeline: view()) on a registered --p (0..1);
// browsers without them get the same --p from a tiny scroll handler; reduced motion gets --p = 1.
// As each plate takes the screen, the interface takes on that plate's light.
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import gsap from 'gsap'
import Icon from './Icon.vue'
import ParticleJourney from './ParticleJourney.vue'
import { SECTIONS } from '../sections.js'

const base = import.meta.env.BASE_URL
const S = Object.fromEntries(SECTIONS.map((s) => [s.id, s]))

// origin / direction of each reveal, in fractions of the image (desktop, then phone render)
const PLATES = [
  { img: 'tsunami', sec: 'tsunami', kind: 'wave', o: [0.152, 0.209], op: [0.339, 0.237],
    title: 'The 2011 tsunami crossing the Pacific',
    line: 'Undersea ridges bend the wave into beams aimed at Hawaii, Chile and New Zealand. Computed from the physics, not drawn.' },
  { img: 'fuji_side', sec: 'fuji', kind: 'rings', dir: 'to bottom', dirp: 'to bottom',
    title: 'Fuji, ring by ring',
    line: 'Contour lines every 10 metres, lifted to their true height and seen from 30 km south. The notch on the right flank is the 1707 crater.' },
  { img: 'izu', sec: 'earthquakes', kind: 'sweep', dir: 'to right', dirp: 'to bottom',
    title: 'A plate sinking 680 km',
    line: 'Along the Izu–Bonin Trench, the amber quakes are the surface. The violet ones beside them are the same ocean floor, hundreds of kilometres down.' },
  { img: 'typhoons', sec: 'typhoons', kind: 'sweep', dir: 'to top right', dirp: 'to top',
    title: 'Seventy years of typhoons',
    line: 'Born in the tropics, they drift west, then curve north toward Japan. The white arcs fell below 930 hPa.' },
  { img: 'trains_tokyo', sec: 'railways', kind: 'radial', o: [0.556, 0.495], op: [0.703, 0.497],
    title: 'Tokyo, every line in its own colour',
    line: 'The green Yamanote loop, the orange Chūō line cutting through it, the Shinkansen in white. Light spreads from Tokyo Station.' },
  { img: 'sakura', sec: 'sakura', kind: 'sweep', dir: 'to right', dirp: 'to bottom',
    title: 'The cherry blossom front',
    line: 'Sixty-six springs at 102 cities. The front leaves Okinawa in January and reaches Wakkanai in late May.' },
]
const vars = (p) => ({
  '--tone': S[p.sec].accent,
  ...(p.o ? { '--ox': p.o[0] * 100 + '%', '--oy': p.o[1] * 100 + '%', '--oxp': p.op[0] * 100 + '%', '--oyp': p.op[1] * 100 + '%' } : {}),
  ...(p.dir ? { '--dir': p.dir, '--dirp': p.dirp } : {}),
})

const root = ref(null)
let io, raf = 0, onScroll
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
const fallback = ref(reduce)
const native = typeof CSS !== 'undefined' && CSS.supports?.('animation-timeline: view()')

function tint(id) {
  const s = S[id]
  gsap.to(document.documentElement, { '--accent': s.accent, '--accent2': s.accent2, duration: reduce ? 0 : 0.8, ease: 'power2.out' })
}

onMounted(() => {
  document.title = 'Hikari Atlas'
  tint('earthquakes')
  io = new IntersectionObserver((entries) => {
    for (const e of entries) if (e.isIntersecting) tint(e.target.dataset.sec)
  }, { rootMargin: '-45% 0px -45% 0px' })
  root.value.querySelectorAll('[data-sec]').forEach((el) => io.observe(el))

  if (!fallback.value) return
  window.hikariLoader?.done()
  startFallback()
})

function startFallback() {
  const media = [...root.value.querySelectorAll('.plate .develop')]
  if (reduce) { media.forEach((m) => m.style.setProperty('--p', 1)); return }

  // fallback for browsers without scroll timelines: same curve, computed on scroll
  if (!native) {
    const update = () => {
      raf = 0
      const vh = innerHeight
      for (const m of media) {
        const r = m.getBoundingClientRect()
        const p = Math.min(1, Math.max(0, (vh - r.top) / (vh * 0.35 + r.height * 0.6)))
        m.style.setProperty('--p', p.toFixed(3))
      }
    }
    onScroll = () => { if (!raf) raf = requestAnimationFrame(update) }
    addEventListener('scroll', onScroll, { passive: true }); addEventListener('resize', onScroll)
    update()
  }

  // the opening: the map develops along the arc while the name surfaces out of the dark
  const hero = root.value.querySelector('.home-hero .develop')
  gsap.timeline({ defaults: { ease: 'expo.out' } })
    .fromTo(hero, { '--p': 0 }, { '--p': 1, duration: 2.6, ease: 'power2.inOut' })
    .from('.hero-name', { opacity: 0, y: 16, filter: 'blur(8px)', duration: 1.2 }, 0.9)
    .from('.hero-thesis, .hero-go', { opacity: 0, y: 10, duration: 0.9, stagger: 0.12 }, 1.4)
}
async function noWebGL() { window.hikariLoader?.done(); fallback.value = true; await nextTick(); root.value.querySelectorAll('[data-sec]').forEach((el) => io.observe(el)); startFallback() }
onBeforeUnmount(() => {
  io?.disconnect()
  if (onScroll) { removeEventListener('scroll', onScroll); removeEventListener('resize', onScroll) }
  cancelAnimationFrame(raf)
})
</script>

<template>
  <main id="main" ref="root" class="home" tabindex="-1">
    <ParticleJourney v-if="!fallback" @unsupported="noWebGL" />
    <template v-else>
    <section class="home-hero" data-sec="earthquakes" aria-labelledby="home-title">
      <span class="develop sweep timed" style="--dir: to right; --dirp: to bottom">
        <picture>
          <source media="(max-width: 700px)" :srcset="`${base}wallpapers/feature/japan_p.webp`" />
          <img :src="`${base}wallpapers/feature/japan_d.webp`" alt="About 30,000 earthquakes around Japan drawn as points of light, tracing the island arc" width="2560" height="1440" fetchpriority="high" />
        </picture>
      </span>
      <div class="hero-copy wrap">
        <h1 id="home-title" class="hero-name"><span lang="ja">光の地図</span>Hikari Atlas</h1>
        <p class="hero-thesis">Japan drawn only with light, from real data: 30,167 earthquakes, 1,784 typhoons, a tsunami, 5,843 cherry blossoms and every railway line. Every unlit pixel is pure black, made for OLED screens. All wallpapers are free.</p>
        <router-link to="/earthquakes" class="hero-go">Start with the earthquakes <Icon name="arrow" /></router-link>
      </div>
    </section>

    <router-link v-for="p in PLATES" :key="p.img" :to="`/${p.sec}`" class="plate" :data-sec="p.sec" :style="vars(p)">
      <span class="develop" :class="p.kind">
        <picture>
          <source media="(max-width: 700px)" :srcset="`${base}wallpapers/feature/${p.img}_p.webp`" />
          <img :src="`${base}wallpapers/feature/${p.img}_d.webp`" :alt="`${p.title}: ${S[p.sec].title} wallpaper`" width="2560" height="1440" loading="lazy" />
        </picture>
      </span>
      <span class="plate-copy wrap">
        <span class="plate-kanji" lang="ja" aria-hidden="true"><span v-for="(c, i) in S[p.sec].kanji" :key="i">{{ c }}</span></span>
        <span class="plate-text">
          <span class="plate-title">{{ p.title }}</span>
          <span class="plate-line">{{ p.line }}</span>
          <span class="plate-go">{{ S[p.sec].title }} <Icon name="arrow" /></span>
        </span>
      </span>
    </router-link>
    </template>

    <nav class="chapters wrap" aria-label="All chapters">
      <h2>Six chapters</h2>
      <ul>
        <li v-for="s in SECTIONS" :key="s.id">
          <router-link :to="`/${s.id}`" :style="{ '--tone': s.accent }">
            <span class="ch-kanji" lang="ja" aria-hidden="true">{{ s.kanji }}</span>
            <span class="ch-title">{{ s.title }}</span>
            <span class="ch-count">{{ s.wallpapers.length * 2 }} wallpapers</span>
          </router-link>
        </li>
      </ul>
    </nav>
  </main>
</template>

<style>
/* registered so it can be animated and inherited by the wavefront ring */
@property --p { syntax: '<number>'; inherits: true; initial-value: 1; }
@keyframes develop { from { --p: 0; } to { --p: 1; } }
</style>

<style scoped>
.home { overflow-x: clip; }
.home:focus { outline: none; }
picture, img { display: block; width: 100%; }
img { height: auto; }

/* ---------- develop: each still is uncovered by its own logic ---------- */
.develop { display: block; position: relative; --p: 1; --soft: 14%; }
.develop picture { -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat; }
/* linear sweeps (arc, trench, tropics to Japan, the calendar) */
.sweep picture {
  -webkit-mask-image: linear-gradient(var(--dir), #000 calc(var(--p) * 130% - var(--soft)), transparent calc(var(--p) * 130%));
          mask-image: linear-gradient(var(--dir), #000 calc(var(--p) * 130% - var(--soft)), transparent calc(var(--p) * 130%)); }
/* Fuji: the line of light steps down in bands, like contour rings catching the sun */
.rings { --q: round(down, var(--p) * 24, 1) / 24; }
.rings picture {
  -webkit-mask-image: linear-gradient(var(--dir), #000 calc(var(--q) * 120% - 4%), transparent calc(var(--q) * 120%));
          mask-image: linear-gradient(var(--dir), #000 calc(var(--q) * 120% - 4%), transparent calc(var(--q) * 120%)); }
/* radial: Tokyo Station; wave: the epicentre, with a bright wavefront at the edge */
.radial picture, .wave picture {
  -webkit-mask-image: radial-gradient(circle at var(--ox) var(--oy), #000 calc(var(--p) * 150% - 10%), transparent calc(var(--p) * 150%));
          mask-image: radial-gradient(circle at var(--ox) var(--oy), #000 calc(var(--p) * 150% - 10%), transparent calc(var(--p) * 150%)); }
.wave::after { content: ''; position: absolute; inset: 0; pointer-events: none; mix-blend-mode: screen;
  background: radial-gradient(circle at var(--ox) var(--oy), transparent calc(var(--p) * 150% - 2.2%),
    color-mix(in srgb, var(--tone) 70%, transparent) calc(var(--p) * 150% - .6%), transparent calc(var(--p) * 150% + .4%));
  opacity: calc(1 - var(--p) * var(--p)); }
/* scroll-linked where the browser can; .timed (the hero) is driven by GSAP instead */
@supports (animation-timeline: view()) {
  .plate .develop { animation: develop linear both; animation-timeline: view(); animation-range: entry 0% cover 52%; }
}
@media (max-width: 700px) {
  .sweep, .rings { --dir: var(--dirp) !important; }
  .radial, .wave { --ox: var(--oxp); --oy: var(--oyp); }
}
@media (prefers-reduced-motion: reduce) {
  .develop { --p: 1 !important; animation: none !important; }
  .wave::after { display: none; }
}

/* ---------- opening plate ---------- */
.home-hero { position: relative; }
.home-hero img { aspect-ratio: 16 / 9; object-fit: cover; }
.hero-copy { position: relative; margin-top: clamp(-260px, -18vw, -120px); padding-bottom: clamp(40px, 6vw, 88px);
  display: grid; gap: 20px; justify-items: start; }
.hero-copy::before { content: ''; position: absolute; inset: -80px -100vw 0; z-index: -1;
  background: linear-gradient(to bottom, transparent, rgba(0, 0, 0, .78) 45%, #000 80%); }
.hero-name { margin: 0; font-weight: 300; font-size: clamp(44px, 7vw, 104px); line-height: .95; letter-spacing: -.02em; }
.hero-name span { display: block; font-family: var(--mincho); font-weight: 700; font-size: .42em; letter-spacing: .3em; color: var(--accent); margin-bottom: .5em; }
.hero-thesis { margin: 0; max-width: 58ch; font-weight: 300; font-size: clamp(17px, 1.5vw, 20px); color: var(--fg); }
.hero-go { display: inline-flex; align-items: center; gap: 12px; min-height: 48px; padding: 0 20px; border: 1px solid var(--edge);
  color: var(--fg); text-decoration: none; transition: border-color .3s, color .3s; }
.hero-go:hover { border-color: var(--accent); color: var(--accent); }
.hero-go svg, .plate-go svg { width: 18px; height: 18px; transition: transform .5s var(--ease-out); }
.hero-go:hover svg, .plate:hover .plate-go svg { transform: translateX(6px); }

/* ---------- plates ---------- */
.plate { display: block; position: relative; text-decoration: none; color: var(--fg); margin-top: clamp(48px, 9vw, 140px); }
.plate img { aspect-ratio: 16 / 9; object-fit: cover; transition: filter 1s var(--ease-out); }
.plate:hover img { filter: brightness(1.12); }
.plate:focus-visible { outline: none; }
.plate:focus-visible img { outline: 2px solid var(--tone); outline-offset: -2px; }
.plate-copy { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: clamp(16px, 3vw, 40px); align-items: start;
  padding-top: clamp(20px, 2.5vw, 32px); }
.plate-kanji { font-family: var(--mincho); font-weight: 700; font-size: clamp(40px, 5vw, 72px); line-height: 1.05; color: var(--tone);
  display: flex; flex-direction: column; align-items: center; }
.plate-text { display: grid; gap: 10px; max-width: 64ch; }
.plate-title { font-weight: 300; font-size: clamp(24px, 3vw, 40px); line-height: 1.15; text-wrap: balance; }
.plate-line { font-weight: 300; color: var(--dim); }
.plate-go { display: inline-flex; align-items: center; gap: 10px; color: var(--tone); padding-block: 8px; }

/* ---------- closing index ---------- */
.chapters { margin-top: clamp(72px, 12vw, 180px); padding-block: 40px 24px; border-top: 1px solid var(--line); }
.chapters h2 { margin: 0 0 24px; font-weight: 300; font-size: 28px; }
.chapters ul { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; background: var(--line); }
.chapters li { background: #000; }
.chapters a { display: grid; gap: 4px; padding: clamp(20px, 3vw, 36px); min-height: 100%; text-decoration: none; color: var(--fg); transition: background .4s; }
.chapters a:hover { background: color-mix(in srgb, var(--tone) 7%, #000); }
.ch-kanji { font-family: var(--mincho); font-weight: 700; font-size: clamp(40px, 5vw, 64px); line-height: 1.1; color: var(--tone); }
.ch-title { font-size: 18px; }
.ch-count { font-size: 14px; color: var(--dim); }

@media (max-width: 700px) {
  .home-hero img, .plate img { aspect-ratio: 860 / 1864; max-height: 88vh; max-height: 88svh; object-fit: cover; object-position: 50% 40%; }
  .hero-copy { margin-top: -16vh; }
  .plate-kanji { flex-direction: row; font-size: 40px; }
  .plate-copy { grid-template-columns: minmax(0, 1fr); gap: 8px; }
  .chapters ul { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (prefers-reduced-motion: reduce) { .plate img, .hero-go svg, .plate-go svg { transition: none; } }
</style>
