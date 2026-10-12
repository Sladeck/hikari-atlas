import { createRouter, createWebHistory } from 'vue-router'
import SectionPage from './components/SectionPage.vue'
import HomePage from './components/HomePage.vue'
import NotFound from './components/NotFound.vue'
import { SECTIONS } from './sections.js'

// pages cross-fade out-in, so the scroll waits until the new page is in (App calls pageEntered);
// Back and Forward return to where the visitor was, everything else starts at the top
let entered = null
export function pageEntered() { entered?.(); entered = null }

// links shared before history mode (hikari-atlas.com/#/fuji) still open their chapter
if (location.hash.startsWith('#/')) history.replaceState(null, '', location.hash.slice(1))

// history mode: each chapter has its own URL for search engines. The build writes a copy of
// index.html per chapter (vite.config.js); nginx serves anything else as a 404 with index.html
export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', component: HomePage },
    ...SECTIONS.map((s) => ({ path: `/${s.id}`, component: SectionPage, props: { section: s }, meta: { section: s } })),
    { path: '/:pathMatch(.*)*', component: NotFound, meta: { notFound: true } },     // nginx sends these with a 404 status
  ],
  scrollBehavior(to, from, saved) {
    const pos = saved || { top: 0 }
    if (!from.matched.length) return pos                  // first load: nothing is leaving
    return new Promise((resolve) => {
      const done = () => resolve(pos)
      entered = done
      setTimeout(done, 1200)                              // never hang if no transition runs
    })
  },
})
