import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router.js'
import './styles.css'

createApp(App).use(router).mount('#app')
// the front page's particle stage closes the loading screen itself once its data is on the GPU;
// every other page (and the no-WebGL fallback) is ready as soon as the router has rendered
router.isReady().then(() => {
  if (router.currentRoute.value.path !== '/') window.hikariLoader?.done()
})
