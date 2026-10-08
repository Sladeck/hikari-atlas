<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import gsap from 'gsap'
import WallpaperCard from './WallpaperCard.vue'
import Lightbox from './Lightbox.vue'
import Icon from './Icon.vue'
import QuakeTimelapse from './anim/QuakeTimelapse.vue'
import TyphoonTracks from './anim/TyphoonTracks.vue'
import SakuraFront from './anim/SakuraFront.vue'
import TokyoTrains from './anim/TokyoTrains.vue'
import TsunamiVideo from './anim/TsunamiVideo.vue'
import FujiRise from './anim/FujiRise.vue'
import RiverFlow from './anim/RiverFlow.vue'
import VolcanoEruptions from './anim/VolcanoEruptions.vue'
import { sections, local, lang, t } from '../i18n.js'

const props = defineProps({ section: { type: Object, required: true } })
const sec = computed(() => local(props.section))                 // this chapter in the current language
const ANIMS = { quakes: QuakeTimelapse, typhoons: TyphoonTracks, sakura: SakuraFront, trains: TokyoTrains, tsunami: TsunamiVideo, fuji: FujiRise, rivers: RiverFlow, volcanoes: VolcanoEruptions }
const anim = computed(() => ANIMS[props.section.anim])
const next = computed(() => sections.value[(sections.value.findIndex((s) => s.id === props.section.id) + 1) % sections.value.length])
const nextLine = computed(() => (lang.value === 'ja' ? next.value.lede.split('。')[0] + '。' : next.value.lede.split('. ')[0] + '.'))

// fullscreen viewer: every image of this section, desktop then phone
const items = computed(() =>
  sec.value.wallpapers.flatMap((w) => [
    { ...w, kind: 'desktop', size: '3840×2160' },
    { ...w, kind: 'phone', size: '1290×2796' },
  ]),
)
const open = ref(-1)
function view(file, kind) { open.value = items.value.findIndex((i) => i.file === file && i.kind === kind) }
function jump(file) {
  const el = document.getElementById(`wp-${file}`)
  el?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' })
  el?.querySelector('button')?.focus({ preventScroll: true })
}

const root = ref(null)
onMounted(async () => {
  await nextTick()
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  // the one authored entrance: the vertical title writes itself downward out of a blur
  gsap.from(root.value.querySelectorAll('.tate-char'), { opacity: 0, y: -24, filter: 'blur(8px)', duration: 0.9, stagger: 0.14, ease: 'expo.out' })
})
</script>

<template>
  <main id="main" ref="root" class="section" tabindex="-1">
    <!-- the way back to the front page's live stage, which opens on this chapter -->
    <div class="wrap back-row">
      <router-link to="/" class="back" :aria-label="t('back')" :title="t('back')"><Icon name="back" /></router-link>
    </div>
    <section class="hero wrap" :aria-labelledby="`${sec.id}-title`">
      <div class="tate" lang="ja" aria-hidden="true">
        <p class="tate-word"><span v-for="(c, i) in sec.kanji" :key="i" class="tate-char">{{ c }}</span></p>
        <p class="tate-kana"><span v-for="(c, i) in sec.kana" :key="i">{{ c }}</span></p>
      </div>
      <div class="stage-col">
        <component :is="anim" class="stage" />
        <div class="intro">
          <div class="intro-text">
            <h1 :id="`${sec.id}-title`">{{ sec.title }}</h1>
            <p class="lede">{{ sec.lede }}</p>
            <p class="data mono">
              <span v-for="f in sec.facts" :key="f[0] + f[1]"><b>{{ f[0] }}</b> {{ f[1] }}</span>
            </p>
          </div>
          <div class="scale" role="img" :aria-label="t('scale', sec.scale.label, sec.scale.from, sec.scale.to)">
            <span class="scale-label">{{ sec.scale.label }}</span>
            <span class="bar" :style="{ background: `linear-gradient(90deg, ${sec.scale.stops.join(',')})` }"></span>
            <span class="ends mono"><span>{{ sec.scale.from }}</span><span>{{ sec.scale.to }}</span></span>
          </div>
        </div>
      </div>
    </section>

    <section class="wrap gallery" :aria-labelledby="`${sec.id}-wp`">
      <header class="gallery-head">
        <h2 :id="`${sec.id}-wp`">{{ t('wallpapers') }} <span class="count">{{ t('countLine', sec.wallpapers.length * 2) }}</span></h2>
        <nav v-if="sec.wallpapers.length > 2" class="jump" :class="{ ja: lang === 'ja' }" :aria-label="t('jump')">
          <button v-for="w in sec.wallpapers" :key="w.file" type="button" @click="jump(w.file)">
            {{ w.name }}
          </button>
        </nav>
      </header>
      <WallpaperCard v-for="(w, i) in sec.wallpapers" :id="`wp-${w.file}`" :key="w.file" :w="w" :flip="i % 2 === 1" @view="view" />
    </section>

    <section class="wrap method" :aria-labelledby="`${sec.id}-how`">
      <h2 :id="`${sec.id}-how`">{{ t('how') }}</h2>
      <dl>
        <div v-for="m in sec.method" :key="m[0]"><dt>{{ m[0] }}</dt><dd>{{ m[1] }}</dd></div>
      </dl>
      <p class="sources">
        <span class="sources-label">{{ t('sources') }}</span>
        <a v-for="s in sec.sources" :key="s[1]" :href="s[1]" target="_blank" rel="noopener">{{ s[0] }}</a>
      </p>
    </section>

    <router-link :to="`/${next.id}`" class="next" :style="{ '--next': next.accent }">
      <span class="next-kanji" lang="ja" aria-hidden="true">{{ next.kanji }}</span>
      <span class="next-text">
        <span class="next-label">{{ t('next') }}</span>
        <span class="next-title">{{ next.title }} <Icon name="arrow" class="next-arrow" /></span>
        <span class="next-line">{{ nextLine }}</span>
      </span>
    </router-link>

    <Lightbox v-if="open >= 0" :items="items" :index="open" @close="open = -1" @go="(i) => (open = i)" />
  </main>
</template>

<style scoped>
.section:focus { outline: none; }
.back-row { padding-top: clamp(16px, 2.4vw, 28px); }
.back { display: inline-grid; place-items: center; width: 44px; height: 44px; border: 1px solid var(--edge); background: #000;
  color: var(--fg); transition: border-color .25s, color .25s; }
.back svg { width: 20px; height: 20px; transition: transform .4s var(--ease-out); }
.back:hover, .back:focus-visible { border-color: var(--accent); color: var(--accent); }
.back:hover svg { transform: translateX(-3px); }
.back:focus-visible { outline-offset: 3px; }
.hero { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: clamp(16px, 3vw, 40px); padding-block: clamp(12px, 2vw, 24px) 32px; }
/* tategaki: kanji stacked top to bottom, kana in a thin column beside them */
.tate { display: flex; gap: 12px; align-items: flex-start; padding-top: 4px; }
.tate p { margin: 0; display: flex; flex-direction: column; align-items: center; }
.tate-word { font-family: var(--mincho); font-weight: 700; font-size: clamp(44px, 7vw, 96px); line-height: 1.08; color: var(--accent); text-shadow: 0 0 28px color-mix(in srgb, var(--accent) 40%, transparent); }
.tate-kana { font-family: var(--sans); font-weight: 300; font-size: 13px; line-height: 1.5; color: var(--dim); padding-top: .5em; }
.stage-col { min-width: 0; display: grid; gap: clamp(24px, 3vw, 40px); }
.stage { width: 100%; }
.intro { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 280px); gap: 24px 56px; align-items: end; }
.intro-text { display: grid; gap: 16px; }
h1 { margin: 0; font-family: var(--sans); font-weight: 300; font-size: clamp(30px, 3.6vw, 48px); line-height: 1.05; letter-spacing: -.015em; text-wrap: balance; }
.lede { margin: 0; max-width: 64ch; font-weight: 300; font-size: 18px; }
.data { margin: 0; display: flex; flex-wrap: wrap; gap: 6px 28px; font-size: 13px; color: var(--dim); }
.data b { color: var(--fg); font-weight: 400; }
.scale { display: grid; gap: 8px; padding-bottom: 6px; }
.scale-label { font-size: 13px; color: var(--dim); }
.scale .bar { height: 4px; display: block; }
.scale .ends { display: flex; justify-content: space-between; font-size: 12px; color: var(--dim); }

.gallery { display: grid; gap: clamp(56px, 8vw, 104px); padding-block: 56px 72px; }
.gallery-head { display: grid; gap: 16px; }
.gallery h2 { margin: 0; font-weight: 300; font-size: 28px; display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 20px; }
.count { font-size: 14px; color: var(--dim); }
.jump { display: flex; flex-wrap: wrap; gap: 8px; }
.jump button { background: #000; border: 1px solid var(--edge); color: var(--dim); padding: 8px 14px; min-height: 44px; cursor: pointer; font-size: 14px; transition: color .2s, border-color .2s; }
.jump button:hover { color: var(--accent); border-color: var(--accent); }
.jump.ja button { font-family: var(--mincho); font-weight: 500; }

.method { padding-block: 48px 40px; border-top: 1px solid var(--line); display: grid; grid-template-columns: minmax(0, 220px) minmax(0, 1fr); gap: 20px 48px; }
.method h2 { margin: 0; font-weight: 300; font-size: 28px; }
.method dl { margin: 0; display: grid; gap: 20px; max-width: 68ch; }
.method dt { font-weight: 700; color: var(--accent); }
.method dd { margin: 4px 0 0; font-weight: 300; }
.sources { grid-column: 2; display: flex; flex-wrap: wrap; gap: 4px 20px; margin: 8px 0 0; font-size: 14px; align-items: baseline; }
.sources a { display: inline-block; padding-block: 10px; }
.sources-label { color: var(--dim); }

/* the end of every page: the next chapter's own light */
.next { display: grid; grid-template-columns: auto minmax(0, 1fr); align-items: center; gap: clamp(20px, 4vw, 56px);
  max-width: var(--maxw); margin: 24px auto 0; padding: clamp(32px, 6vw, 72px) var(--gutter); text-decoration: none; color: var(--fg);
  border-top: 1px solid var(--line); }
.next-kanji { font-family: var(--mincho); font-weight: 700; font-size: clamp(64px, 12vw, 168px); line-height: 1; color: var(--next);
  opacity: .55; transition: opacity .6s var(--ease-out), text-shadow .6s var(--ease-out); }
.next:hover .next-kanji, .next:focus-visible .next-kanji { opacity: 1; text-shadow: 0 0 40px color-mix(in srgb, var(--next) 45%, transparent); }
.next-text { display: grid; gap: 6px; min-width: 0; }
.next-label { font-size: 14px; color: var(--dim); }
.next-title { font-weight: 300; font-size: clamp(28px, 4vw, 48px); line-height: 1.1; color: var(--next); display: inline-flex; align-items: center; gap: 14px; }
.next-arrow { width: .7em; height: .7em; transition: transform .5s var(--ease-out); }
.next:hover .next-arrow { transform: translateX(8px); }
.next-line { color: var(--dim); font-weight: 300; max-width: 60ch; }

@container pane (max-width: 860px) {
  .intro, .method { grid-template-columns: minmax(0, 1fr); }
  .scale { max-width: 320px; }
  .sources { grid-column: 1; }
}
@container pane (max-width: 560px) {
  .hero { grid-template-columns: minmax(0, 1fr); padding-top: 16px; }
  .tate { align-items: baseline; }
  .tate p { flex-direction: row; }
  .tate-word { font-size: 48px; }
  .tate-kana { padding: 0; letter-spacing: .2em; }
  .next { grid-template-columns: minmax(0, 1fr); }
}
</style>
