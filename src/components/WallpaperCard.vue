<script setup>
// One wallpaper: the desktop render bleeding into the black page (no frame: the OLED idea is the
// frame), the phone render inside a phone silhouette, then the note and downloads (phone first).
import { SIZES } from '../sizes.js'
import Icon from './Icon.vue'
defineProps({ w: { type: Object, required: true }, flip: { type: Boolean, default: false } })
defineEmits(['view'])
const base = import.meta.env.BASE_URL
</script>

<template>
  <article class="card" :class="{ flip }">
    <div class="shots">
      <button type="button" class="shot d" :aria-label="`View ${w.en} desktop wallpaper fullscreen`" @click="$emit('view', w.file, 'desktop')">
        <img :src="`${base}wallpapers/preview/${w.file}_desktop.webp`" :alt="`${w.en}, desktop wallpaper`" width="1920" height="1080" loading="lazy" />
      </button>
      <button type="button" class="shot p" :aria-label="`View ${w.en} phone wallpaper fullscreen`" @click="$emit('view', w.file, 'phone')">
        <span class="phone">
          <img :src="`${base}wallpapers/preview/${w.file}_phone.webp`" :alt="`${w.en}, phone wallpaper`" width="516" height="1118" loading="lazy" />
        </span>
      </button>
    </div>
    <div class="meta">
      <h3><span lang="ja">{{ w.jp }}</span><small>{{ w.en }}</small></h3>
      <p>{{ w.note }}</p>
      <div class="dl">
        <a class="ctl" :href="`${base}wallpapers/full/${w.file}_phone.png`" :download="`hikari-${w.file}-phone.png`">
          <Icon name="download" />Phone <span class="mono">1290×2796 · {{ SIZES[`${w.file}_phone`] }} MB</span>
        </a>
        <a class="ctl" :href="`${base}wallpapers/full/${w.file}_desktop.png`" :download="`hikari-${w.file}-desktop.png`">
          <Icon name="download" />Desktop <span class="mono">3840×2160 · {{ SIZES[`${w.file}_desktop`] }} MB</span>
        </a>
      </div>
    </div>
  </article>
</template>

<style scoped>
.card { display: grid; gap: 24px; scroll-margin-top: calc(var(--hdr, 72px) + 24px); }
.shots { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, .26fr); gap: clamp(16px, 3vw, 48px); align-items: center; }
.flip .shots { grid-template-columns: minmax(0, .26fr) minmax(0, 1fr); }
.flip .d { order: 2; }
.shot { all: unset; display: block; cursor: zoom-in; min-width: 0; position: relative; }
.shot img { width: 100%; height: auto; transition: transform .8s var(--ease-out), filter .8s var(--ease-out); }
.d img { aspect-ratio: 16 / 9; }
.shot:hover img { filter: brightness(1.18); }
.shot:focus-visible { outline: 2px solid var(--accent); outline-offset: 6px; }
/* phone silhouette: rounded glass edge, a faint rim, the wallpaper true to its ratio */
.phone { display: block; border-radius: 13% / 6%; padding: 3.5%; background: #000; box-shadow: 0 0 0 1px var(--faint), 0 18px 40px -12px rgba(0, 0, 0, .9); overflow: hidden; }
.phone img { border-radius: 10% / 4.6%; aspect-ratio: 1290 / 2796; }
.meta { display: grid; grid-template-columns: minmax(0, 15ch) minmax(0, 60ch) auto; gap: 12px 40px; align-items: start; }
h3 { margin: 0; font-family: var(--mincho); font-weight: 500; font-size: 28px; line-height: 1.15; }
h3 small { display: block; font-family: var(--sans); font-size: 14px; color: var(--dim); margin-top: 6px; font-weight: 400; }
.meta p { margin: 0; font-weight: 300; }
.dl { display: flex; flex-direction: column; gap: 8px; }
.dl .ctl { justify-content: flex-start; min-height: 44px; }
.dl .mono { color: var(--dim); font-size: 12px; margin-left: auto; padding-left: 10px; }
@media (max-width: 860px) {
  .meta { grid-template-columns: minmax(0, 1fr); }
  .dl { flex-direction: row; flex-wrap: wrap; }
  .dl .ctl { flex: 1 1 240px; }
}
@media (max-width: 520px) {
  .shots, .flip .shots { grid-template-columns: minmax(0, 1fr) minmax(0, .34fr); gap: 12px; }
  .flip .d { order: 0; }
}
</style>
