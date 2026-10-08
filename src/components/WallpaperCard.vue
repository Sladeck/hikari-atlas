<script setup>
// One wallpaper: the desktop render bleeding into the black page (no frame: the OLED idea is the
// frame), the phone render inside a phone silhouette, then the note and downloads (phone first).
import { SIZES } from '../sizes.js'
import Icon from './Icon.vue'
import { lang, t } from '../i18n.js'
defineProps({ w: { type: Object, required: true }, flip: { type: Boolean, default: false } })
defineEmits(['view'])
const base = import.meta.env.BASE_URL
</script>

<template>
  <article class="card" :class="{ flip }">
    <div class="shots">
      <button type="button" class="shot d" :aria-label="t('viewFull', w.name, t('desktop'))" @click="$emit('view', w.file, 'desktop')">
        <img :src="`${base}wallpapers/preview/${w.file}_desktop.webp`" :alt="t('alt', w.name, t('desktop'))" width="1920" height="1080" loading="lazy" />
      </button>
      <button type="button" class="shot p" :aria-label="t('viewFull', w.name, t('phone'))" @click="$emit('view', w.file, 'phone')">
        <span class="phone">
          <img :src="`${base}wallpapers/preview/${w.file}_phone.webp`" :alt="t('alt', w.name, t('phone'))" width="516" height="1118" loading="lazy" />
        </span>
      </button>
    </div>
    <div class="meta">
      <h3 :class="{ ja: lang === 'ja' }">{{ w.name }}</h3>
      <p>{{ w.note }}</p>
      <div class="dl">
        <a class="ctl" :href="`${base}wallpapers/full/${w.file}_phone.png`" :download="`hikari-${w.file}-phone.png`">
          <Icon name="download" />{{ t('phone') }} <span class="mono">1290×2796 · {{ SIZES[`${w.file}_phone`] }} MB</span>
        </a>
        <a class="ctl" :href="`${base}wallpapers/full/${w.file}_desktop.png`" :download="`hikari-${w.file}-desktop.png`">
          <Icon name="download" />{{ t('desktop') }} <span class="mono">3840×2160 · {{ SIZES[`${w.file}_desktop`] }} MB</span>
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
.shot img { width: 100%; height: auto; }
/* the pictures are never retouched on hover: they grow a little towards the visitor instead */
.d img, .phone { transition: transform .8s var(--ease-out); }
.d img { aspect-ratio: 16 / 9; }
.d:hover img, .d:focus-visible img { transform: scale(1.03); }
.p:hover .phone, .p:focus-visible .phone { transform: scale(1.05); }
.shot:focus-visible { outline: 2px solid var(--accent); outline-offset: 6px; }
/* phone silhouette: rounded glass edge, a faint rim, the wallpaper true to its ratio */
.phone { display: block; border-radius: 13% / 6%; padding: 3.5%; background: #000; box-shadow: 0 0 0 1px var(--faint), 0 18px 40px -12px rgba(0, 0, 0, .9); overflow: hidden; }
.phone img { border-radius: 10% / 4.6%; aspect-ratio: 1290 / 2796; }
.meta { display: grid; grid-template-columns: minmax(15ch, max-content) minmax(0, 60ch) auto; gap: 12px 40px; align-items: start; }
h3 { margin: 0; font-weight: 300; font-size: 26px; line-height: 1.2; text-wrap: balance; }
/* a Japanese name is set in Mincho and never breaks mid-word */
h3.ja { font-family: var(--mincho); font-weight: 500; font-size: 28px; line-height: 1.15; white-space: nowrap; }
.meta p { margin: 0; font-weight: 300; }
.dl { display: flex; flex-direction: column; gap: 8px; }
.dl .ctl { justify-content: flex-start; min-height: 44px; }
.dl .mono { color: var(--dim); font-size: 12px; margin-left: auto; padding-left: 10px; }
@container pane (max-width: 860px) {
  .meta { grid-template-columns: minmax(0, 1fr); }
  .dl { flex-direction: row; flex-wrap: wrap; }
  .dl .ctl { flex: 1 1 240px; }
}
@container pane (max-width: 520px) {
  .shots, .flip .shots { grid-template-columns: minmax(0, 1fr) minmax(0, .34fr); gap: 12px; }
  .flip .d { order: 0; }
}
</style>
