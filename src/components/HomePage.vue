<script setup>
// Front page. Its picture is the shell's live stage (StageLayer) beside the rail's board, so this
// page only names the atlas and sets the board turning over by itself while it is up (station.js).
import { onMounted, onBeforeUnmount } from 'vue'
import { start, stop } from '../station.js'

onMounted(() => { document.title = 'Hikari Atlas'; start() })
onBeforeUnmount(stop)
</script>

<template>
  <main id="main" class="home" tabindex="-1">
    <h1 class="visually-hidden">Hikari Atlas, <span lang="ja">光の地図</span>: Japan drawn only with light</h1>
  </main>
</template>

<style scoped>
.home:focus { outline: none; }
</style>
