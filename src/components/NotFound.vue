<script setup>
// Any address that is not a chapter. nginx answers it with a real 404 status and index.html as the
// body (nginx.conf), so the app can say so instead of quietly showing the front page.
import Icon from './Icon.vue'
import { sections, t } from '../i18n.js'
</script>

<template>
  <main id="main" class="lost wrap" tabindex="-1">
    <p class="code mono" aria-hidden="true">404</p>
    <h1>{{ t('notFound').title }}</h1>
    <p class="text">{{ t('notFound').text }}</p>
    <p><router-link to="/" class="ctl"><Icon name="back" />{{ t('notFound').home }}</router-link></p>
    <h2>{{ t('notFound').chapters }}</h2>
    <ul class="list">
      <li v-for="s in sections" :key="s.id">
        <router-link :to="`/${s.id}`" :style="{ '--tone': s.accent }"><span class="badge mono" aria-hidden="true">{{ s.code }}</span>{{ s.title }}</router-link>
      </li>
    </ul>
  </main>
</template>

<style scoped>
.lost { padding-block: clamp(48px, 12vh, 140px) 24px; max-width: 760px; margin-inline: 0; }
.lost:focus { outline: none; }
.code { margin: 0 0 8px; font-size: clamp(48px, 7vw, 88px); font-weight: 300; line-height: 1; color: var(--accent); }
h1 { margin: 0 0 12px; font-weight: 300; font-size: clamp(26px, 3vw, 40px); line-height: 1.15; }
.text { margin: 0 0 24px; max-width: 46ch; color: var(--dim); font-weight: 300; }
.ctl svg { width: 16px; height: 16px; }
h2 { margin: 48px 0 12px; font-size: 13px; font-weight: 400; letter-spacing: .12em; text-transform: uppercase; color: var(--dim); }
.list { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 2px 24px; }
.list a { display: flex; align-items: center; gap: 12px; min-height: 44px; color: var(--fg); text-decoration: none; font-weight: 300; transition: color .2s; }
.list a:hover { color: var(--tone); }
.badge { display: inline-grid; place-items: center; min-width: 2.6em; height: 1.7em; border: 1px solid var(--tone); border-radius: 5px;
  color: var(--tone); font-size: 11px; letter-spacing: .06em; }
</style>
