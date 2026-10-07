import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// base './' so the built site works from any folder or static host
export default defineConfig({
  plugins: [vue()],
  base: './',
})
