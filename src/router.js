import { createRouter, createWebHashHistory } from 'vue-router'
import SectionPage from './components/SectionPage.vue'
import HomePage from './components/HomePage.vue'
import { SECTIONS } from './sections.js'

// pages cross-fade out-in, so the scroll waits until the new page is in (App calls pageEntered);
// Back and Forward return to where the visitor was, everything else starts at the top
let entered = null
export function pageEntered() { entered?.(); entered = null }

// hash history: the built site works from a plain folder or any static host, no server rewrites
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: HomePage },
    ...SECTIONS.map((s) => ({ path: `/${s.id}`, component: SectionPage, props: { section: s }, meta: { section: s } })),
    { path: '/:pathMatch(.*)*', redirect: '/' },
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
