<script setup>
// Front page: the atlas as a departure board beside one live stage. Choosing a row (pointing at
// it, focusing it, or the first tap on a phone) sends the cloud of light to that chapter's scene;
// opening it goes to the chapter. Left alone, the board moves on one row every few seconds, like a
// station board turning over, and stops for a while whenever the visitor touches it.
// Without WebGL the stage crossfades between the chapters' stills.
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import gsap from 'gsap'
import Icon from './Icon.vue'
import DepartureBoard from './DepartureBoard.vue'
import ParticleStage from './ParticleStage.vue'
import { SECTIONS } from '../sections.js'

const base = import.meta.env.BASE_URL
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
const DWELL = 7                                       // seconds per row when the board runs by itself
const REST = 25                                       // seconds the board waits after the visitor's last touch

const selected = ref(0)
const webgl = ref(true)
const en = ref(false)                                 // the board's face: Japanese or English, title included
const auto = ref(!reduce)
const s = computed(() => SECTIONS[selected.value])
const scenes = SECTIONS.map((x) => x.scene)
let timer = 0, resumeAt = 0, flip = 0

function tint(sec) {
  gsap.to(document.documentElement, { '--accent': sec.accent, '--accent2': sec.accent2, duration: reduce ? 0 : 0.8, ease: 'power2.out' })
}
watch(selected, (i) => tint(SECTIONS[i]))

// the board turning over on its own
function schedule() {
  clearTimeout(timer)
  if (reduce) return
  timer = setTimeout(() => {
    if (document.visibilityState === 'visible' && performance.now() >= resumeAt) {
      selected.value = (selected.value + 1) % SECTIONS.length
      auto.value = true
    }
    schedule()
  }, DWELL * 1000)
}
function touched() {
  resumeAt = performance.now() + REST * 1000
  auto.value = false
  schedule()
}
function select(i) { touched(); selected.value = i }
function noWebGL() { webgl.value = false; window.hikariLoader?.done() }

onMounted(() => {
  document.title = 'Hikari Atlas'
  tint(s.value)
  schedule()
  if (!reduce) flip = setInterval(() => { en.value = !en.value }, 4200)
})
onBeforeUnmount(() => { clearTimeout(timer); clearInterval(flip) })
</script>

<template>
  <main id="main" class="home" tabindex="-1">
    <section class="station" aria-labelledby="home-title" @pointerdown="touched" @keydown="touched">
      <div class="side">
        <div class="intro">
          <h1 id="home-title" class="title" :class="{ en, still: reduce }">
            <span class="visually-hidden">Hikari Atlas, <span lang="ja">光の地図</span></span>
            <span class="face jp" lang="ja" aria-hidden="true">光の地図</span><span class="face" aria-hidden="true">Hikari Atlas</span>
          </h1>
          <p class="thesis">Japan drawn only with light, from real data. Pick a destination and the light rebuilds itself; every chapter ends in free OLED wallpapers.</p>
        </div>
        <DepartureBoard :sections="SECTIONS" :selected="selected" :dwell="auto ? DWELL : 0" :face="reduce ? null : en" @select="select" />
      </div>

      <div class="stage" :style="{ '--tone': s.accent }">
        <ParticleStage v-if="webgl" :scenes="scenes" :index="selected" @unsupported="noWebGL" />
        <template v-else>
          <Transition name="still">
            <picture :key="s.still" class="still">
              <source media="(max-width: 860px)" :srcset="`${base}wallpapers/feature/${s.still}_p.webp`" />
              <img :src="`${base}wallpapers/feature/${s.still}_d.webp`" alt="" width="2560" height="1440" />
            </picture>
          </Transition>
        </template>
        <div class="veil" aria-hidden="true"></div>
        <Transition name="cap" mode="out-in">
          <div :key="s.id" class="caption" aria-live="polite">
            <p class="cap-title"><span class="cap-badge mono" aria-hidden="true">{{ s.code }}</span>{{ s.scene.title }}</p>
            <p class="cap-line">{{ s.scene.line }}</p>
            <p class="cap-act">
              <router-link :to="`/${s.id}`" class="cap-go">Open {{ s.title }} <Icon name="arrow" /></router-link>
              <span class="cap-count">{{ s.wallpapers.length * 2 }} wallpapers</span>
            </p>
          </div>
        </Transition>
      </div>
    </section>
  </main>
</template>

<style scoped>
.home:focus { outline: none; }
.station { display: grid; grid-template-columns: minmax(440px, 40%) minmax(0, 1fr);
  height: calc(100vh - var(--hdr, 0px)); height: calc(100svh - var(--hdr, 0px)); min-height: 560px; }

/* ---------- the board side ---------- */
.side { display: flex; flex-direction: column; gap: clamp(16px, 3vh, 32px); min-height: 0; overflow-y: auto;
  padding: clamp(24px, 4.5vh, 48px) clamp(16px, 2.5vw, 40px) 24px var(--gutter); scrollbar-width: thin; }
.intro { display: grid; gap: 12px; }
/* the name turns over with the board: 光の地図 and Hikari Atlas share one line */
.title { position: relative; display: grid; margin: 0; height: 1.1em; overflow: hidden;
  font-weight: 300; font-size: clamp(36px, 3.6vw, 56px); line-height: 1.1; letter-spacing: -.02em; }
.face { grid-area: 1 / 1; white-space: nowrap; transition: transform .7s var(--ease-out), opacity .7s var(--ease-out); }
.face.jp { font-family: var(--mincho); font-weight: 700; letter-spacing: .12em; color: var(--accent); }
.face:not(.jp) { transform: translateY(100%); opacity: 0; }
.title.en .face.jp { transform: translateY(-100%); opacity: 0; }
.title.en .face:not(.jp) { transform: none; opacity: 1; }
.title.still { height: auto; display: flex; flex-wrap: wrap; gap: 0 .4em; }
.title.still .face { transform: none; opacity: 1; }
.thesis { margin: 0; max-width: 52ch; font-weight: 300; font-size: 16px; color: var(--dim); }
.side .board { --row: 48px; }

/* ---------- the stage ---------- */
.stage { position: relative; overflow: hidden; background: #000; border-left: 1px solid var(--line); }
.still { position: absolute; inset: 0; }
.still img { width: 100%; height: 100%; object-fit: cover; }
.still-enter-active, .still-leave-active { transition: opacity 1.2s var(--ease-out); }
.still-enter-from, .still-leave-to { opacity: 0; }
/* a floor of darkness where the words sit, so text never fights the light */
.veil { position: absolute; inset: auto 0 0 0; height: 42%; pointer-events: none;
  background: linear-gradient(to top, rgba(0, 0, 0, .92), rgba(0, 0, 0, .55) 45%, transparent); }
.caption { position: absolute; left: clamp(20px, 3vw, 48px); right: clamp(20px, 3vw, 48px); bottom: clamp(20px, 4vh, 44px);
  display: grid; gap: 10px; max-width: 760px; }
.cap-title { margin: 0; font-weight: 300; font-size: clamp(24px, 2.6vw, 40px); line-height: 1.1; text-wrap: balance; text-shadow: 0 0 20px #000; }
/* the chosen row's line badge, carried onto the stage */
.cap-badge { display: inline-grid; place-items: center; min-width: 2.6em; height: 1.6em; padding: 0 .45em; margin-right: .6em;
  vertical-align: .35em; border-radius: 6px; background: var(--tone); color: #000; font-size: .42em; letter-spacing: .06em; }
.cap-line { margin: 0; font-weight: 300; color: var(--fg); opacity: .78; max-width: 58ch; text-shadow: 0 0 14px #000; }
.cap-act { margin: 4px 0 0; display: flex; align-items: center; flex-wrap: wrap; gap: 8px 22px; }
.cap-go { display: inline-flex; align-items: center; gap: 12px; min-height: 44px; padding: 0 18px; border: 1px solid var(--tone);
  color: var(--tone); text-decoration: none; background: #000; transition: background-color .3s, color .3s; }
.cap-go:hover { background: var(--tone); color: #000; }
.cap-go svg { width: 18px; height: 18px; transition: transform .5s var(--ease-out); }
.cap-go:hover svg { transform: translateX(5px); }
.cap-count { font-size: 14px; color: var(--dim); }
.cap-enter-active { transition: opacity .7s var(--ease-out) .35s, transform .7s var(--ease-out) .35s, filter .7s var(--ease-out) .35s; }
.cap-leave-active { transition: opacity .3s ease, filter .3s ease; }
.cap-enter-from { opacity: 0; transform: translateY(10px); filter: blur(6px); }
.cap-leave-to { opacity: 0; filter: blur(4px); }

/* ---------- phones and narrow windows: the stage on top, the board below ---------- */
@media (max-width: 860px) {
  .station { display: flex; flex-direction: column; height: auto; min-height: 0; }
  .stage { order: -1; height: 50vh; height: 50svh; min-height: 320px; border-left: 0; border-bottom: 1px solid var(--line); }
  .side { overflow: visible; padding: 18px var(--gutter) 8px; }
  .intro { order: 2; padding-top: 16px; }                      /* the board comes first, right under the stage */
  .thesis { display: none; }                                   /* the footer says the same just below */
  .side .board { --row: 54px; }
  .caption { gap: 6px; }
  .cap-line { font-size: 14px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
}
@media (prefers-reduced-motion: reduce) {
  .cap-enter-active, .cap-leave-active, .still-enter-active, .still-leave-active { transition: none; }
}
</style>
