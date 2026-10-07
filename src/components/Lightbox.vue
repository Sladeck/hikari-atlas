<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({ items: Array, index: Number })
const emit = defineEmits(['close', 'go'])
const base = import.meta.env.BASE_URL
const src = ref('')
const loading = ref(false)
const failed = ref(false)
const showUi = ref(true)
const closeBtn = ref(null), dialog = ref(null)
let touch = window.matchMedia('(hover: none), (pointer: coarse)').matches
let timer = 0, lastFocus = null, tx = null, ty = null

const item = computed(() => props.items[props.index])

function load() {
  const it = item.value
  src.value = `${base}wallpapers/preview/${it.file}_${it.kind}.webp`     // instant
  loading.value = true; failed.value = false
  const full = `${base}wallpapers/full/${it.file}_${it.kind}.png`
  const want = props.index, img = new Image()
  img.onload = () => { if (want === props.index) { src.value = full; loading.value = false } }
  img.onerror = () => { if (want === props.index) { loading.value = false; failed.value = true } }
  img.src = full
  poke()
}
// on touch screens the controls stay; with a mouse they rest out of the way after 2.2 s
function poke() { showUi.value = true; clearTimeout(timer); if (!touch) timer = setTimeout(() => (showUi.value = false), 2200) }
const go = (d) => emit('go', (props.index + d + props.items.length) % props.items.length)
function key(e) {
  if (e.key === 'Escape') emit('close')
  else if (e.key === 'ArrowRight') go(1)
  else if (e.key === 'ArrowLeft') go(-1)
  else if (e.key === 'Tab') {               // keep focus inside the viewer
    poke()
    const f = [...dialog.value.querySelectorAll('button, a[href]')]
    const i = f.indexOf(document.activeElement)
    e.preventDefault()
    f[(i + (e.shiftKey ? -1 : 1) + f.length) % f.length]?.focus()
  }
}
watch(() => props.index, load)
onMounted(() => {
  lastFocus = document.activeElement
  document.body.style.overflow = 'hidden'
  const app = document.getElementById('app'); if (app) app.inert = true
  window.addEventListener('keydown', key)
  load()
  closeBtn.value?.focus({ preventScroll: true })
})
onBeforeUnmount(() => {
  document.body.style.overflow = ''
  const app = document.getElementById('app'); if (app) app.inert = false
  window.removeEventListener('keydown', key)
  clearTimeout(timer)
  lastFocus?.focus?.({ preventScroll: true })
})
function touchstart(e) { touch = true; tx = e.touches[0].clientX; ty = e.touches[0].clientY; poke() }
function touchend(e) {
  if (tx === null) return
  const dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty; tx = ty = null
  if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) { e.preventDefault(); go(dx < 0 ? 1 : -1) }
  else if (dy > 90) { e.preventDefault(); emit('close') }       // swipe down to close
}
function tapImage() { if (touch) showUi.value = !showUi.value; else poke() }
</script>

<template>
  <Teleport to="body">
    <div ref="dialog" class="lb" :class="{ ui: showUi }" role="dialog" aria-modal="true" :aria-label="`${item.en}, ${item.kind} wallpaper`"
         @click.self="emit('close')" @mousemove="poke" @touchstart.passive="touchstart" @touchend="touchend">
      <img :src="src" :alt="`${item.en}, ${item.kind} wallpaper`" @click="tapImage" />
      <span v-if="loading" class="status">Loading full resolution…</span>
      <span v-if="failed" class="status">The full-size file did not load; this is the preview.</span>
      <div class="bar">
        <span class="cap"><span lang="ja" class="jp">{{ item.jp }}</span>{{ item.en }} · {{ item.kind === 'phone' ? 'Phone' : 'Desktop' }} <span class="mono">{{ item.size }} · {{ index + 1 }}/{{ items.length }}</span></span>
        <div class="nav">
          <button type="button" class="ctl" aria-label="Previous image" @click="go(-1)"><Icon name="prev" /></button>
          <button type="button" class="ctl" aria-label="Next image" @click="go(1)"><Icon name="next" /></button>
          <a class="ctl" :href="`${base}wallpapers/full/${item.file}_${item.kind}.png`" :download="`hikari-${item.file}-${item.kind}.png`"><Icon name="download" />Download</a>
          <button ref="closeBtn" type="button" class="ctl" @click="emit('close')"><Icon name="close" />Close</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.lb { position: fixed; inset: 0; z-index: 50; background: #000; display: grid; place-items: center; cursor: zoom-out; touch-action: pan-y; }
.lb img { max-width: 100vw; max-height: 100vh; max-height: 100dvh; width: auto; height: auto; object-fit: contain; cursor: default; }
.bar { position: fixed; left: 0; right: 0; bottom: 0; display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
       padding: 14px clamp(16px, 3vw, 32px) calc(14px + env(safe-area-inset-bottom, 0px)); color: var(--dim); font-size: 13px;
       background: linear-gradient(transparent, rgba(0, 0, 0, .85) 40%); opacity: 0; transform: translateY(8px);
       transition: opacity .3s var(--ease-out), transform .3s var(--ease-out); pointer-events: none; cursor: default; }
.lb.ui .bar { opacity: 1; transform: none; pointer-events: auto; }
.cap { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.jp { font-family: var(--mincho); color: var(--fg); margin-right: 8px; }
.cap .mono { font-size: 12px; margin-left: 6px; }
.nav { display: flex; gap: 8px; flex-wrap: wrap; }
.status { position: fixed; top: calc(16px + env(safe-area-inset-top, 0px)); right: 20px; font-size: 13px; color: var(--dim); }
@media (max-width: 640px) { .cap { width: 100%; } .nav { width: 100%; } .nav .ctl:nth-child(3), .nav .ctl:nth-child(4) { flex: 1; } }
</style>
