<script setup>
// Small stroke icon set (1.5px, round caps) so controls never rely on unicode glyphs.
defineProps({ name: { type: String, required: true } })
const P = {
  pause: 'M9 6v12M15 6v12',
  play: 'M8 5.5v13l11-6.5z',
  replay: 'M4 12a8 8 0 1 0 2.6-5.9M4 4v5h5',
  prev: 'M15 5l-7 7 7 7',
  next: 'M9 5l7 7-7 7',
  close: 'M6 6l12 12M18 6L6 18',
  download: 'M12 4v11m0 0l-5-5m5 5l5-5M5 20h14',
  arrow: 'M5 12h14m0 0l-6-6m6 6l-6 6',
}
</script>

<template>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
    <path :d="P[name]" :fill="name === 'play' ? 'currentColor' : 'none'" />
  </svg>
</template>
