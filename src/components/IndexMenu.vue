<script setup>
// The header's index (目次): one button that drops the departure board down under the header,
// so every chapter is one tap away from any page without a bar of ten tabs.
// A disclosure, not a modal: it closes on Escape, a click outside, or any navigation.
import { ref, watch, onBeforeUnmount, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import DepartureBoard from './DepartureBoard.vue'
import { lang, t } from '../i18n.js'

defineProps({ sections: { type: Array, required: true } })           // chapters in the current language
const route = useRoute()
const open = ref(false)
const root = ref(null), button = ref(null)

function close(focus = false) { open.value = false; if (focus) button.value?.focus() }
function key(e) { if (e.key === 'Escape') close(true) }
function outside(e) { if (root.value && !root.value.contains(e.target)) close() }
watch(open, async (v) => {
  if (v) {
    addEventListener('keydown', key); addEventListener('pointerdown', outside)
    await nextTick()
    const r = root.value; (r?.querySelector('.row.router-link-active') || r?.querySelector('.row'))?.focus({ preventScroll: true })
  } else { removeEventListener('keydown', key); removeEventListener('pointerdown', outside) }
})
watch(() => route.fullPath, () => close())
onBeforeUnmount(() => { removeEventListener('keydown', key); removeEventListener('pointerdown', outside) })
</script>

<template>
  <div ref="root" class="index">
    <button ref="button" type="button" class="index-btn" :aria-expanded="open" aria-controls="index-panel" @click="open = !open">
      <span :class="{ jp: lang === 'ja' }">{{ t('chapters') }}</span>
      <svg class="chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
    </button>
    <Transition name="drop">
      <div v-show="open" id="index-panel" class="panel">
        <DepartureBoard :sections="sections" compact />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.index-btn { display: inline-flex; align-items: center; gap: 10px; min-height: 44px; padding: 0 14px; background: #000;
  border: 1px solid var(--edge); color: var(--fg); font-size: 14px; cursor: pointer; transition: border-color .25s, color .25s; }
.index-btn:hover, .index-btn[aria-expanded="true"] { border-color: var(--accent); color: var(--accent); }
.jp { font-family: var(--mincho); font-size: 17px; }
.chev { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round;
  transition: transform .35s var(--ease-out); }
[aria-expanded="true"] .chev { transform: rotate(180deg); }
/* the board drops down under the header, flush with the page's right gutter */
.panel { position: absolute; right: var(--gutter); top: calc(100% + 1px); width: min(560px, calc(100vw - 2 * var(--gutter)));
  max-height: calc(100vh - var(--hdr, 72px) - 24px); max-height: calc(100svh - var(--hdr, 72px) - 24px); overflow-y: auto;
  background: #000; border: 1px solid var(--faint); border-top: 0; box-shadow: 0 24px 48px -16px rgba(0, 0, 0, .9); }
.drop-enter-active, .drop-leave-active { transition: opacity .3s var(--ease-out), transform .4s var(--ease-out), clip-path .45s var(--ease-out); }
.drop-enter-from, .drop-leave-to { opacity: 0; transform: translateY(-6px); clip-path: inset(0 0 100% 0); }
@media (max-width: 520px) { .panel { right: 0; width: 100vw; border-inline: 0; } }
</style>
