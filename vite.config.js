import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { SECTIONS } from './src/sections.js'

const SITE = 'https://hikari-atlas.com'

// sitemap.xml, written at build from the chapter list, so a new chapter is listed by itself
function sitemap() {
  return {
    name: 'sitemap',
    apply: 'build',
    generateBundle() {
      const urls = ['/', ...SECTIONS.map((s) => `/${s.id}`)]
        .map((p) => `  <url><loc>${SITE}${p}</loc></url>`)
      this.emitFile({
        type: 'asset',
        fileName: 'sitemap.xml',
        source: `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join('\n')}\n</urlset>\n`,
      })
    },
  }
}

// base '/': history routing serves chapters at /<id>, so assets and data load from the root
export default defineConfig({
  plugins: [vue(), sitemap()],
  base: '/',
})
