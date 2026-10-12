import { copyFileSync } from 'node:fs'
import { resolve } from 'node:path'
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

// a copy of index.html per chapter (dist/fuji.html), so nginx answers the chapters with 200 and
// every other page address with a real 404 (nginx.conf), without a second list of chapters
function chapterPages() {
  let out
  return {
    name: 'chapter-pages',
    apply: 'build',
    configResolved(c) { out = resolve(c.root, c.build.outDir) },
    closeBundle() {
      for (const s of SECTIONS) copyFileSync(resolve(out, 'index.html'), resolve(out, `${s.id}.html`))
    },
  }
}

// base '/': history routing serves chapters at /<id>, so assets and data load from the root
export default defineConfig({
  plugins: [vue(), sitemap(), chapterPages()],
  base: '/',
})
