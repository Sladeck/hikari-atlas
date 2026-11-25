import { copyFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
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

// Content-Security-Policy as a <meta>, written at build: the hashes of index.html's inline loader
// script and of the fonts link's onload are computed here, so editing either never needs a hand
// update. nginx.conf sends the one rule a <meta> cannot carry (frame-ancestors) as a header.
// Cloudflare injects its Web Analytics beacon (static.cloudflareinsights.com) at the edge.
function csp() {
  const sha = (s) => `'sha256-${createHash('sha256').update(s).digest('base64')}'`
  return {
    name: 'csp',
    apply: 'build',
    transformIndexHtml: {
      order: 'post',
      handler(html) {
        // the browser hashes the parsed text: line endings normalised to \n, entities decoded
        html = html.replace(/\r\n?/g, '\n')
        const scripts = [...html.matchAll(/<script(?![^>]*\bsrc=)(?![^>]*application\/ld\+json)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => sha(m[1]))
        const handlers = [...html.matchAll(/\son[a-z]+=(["'])(.*?)\1/g)].map((m) => {
          if (m[2].includes('&')) throw new Error(`csp: decode the entities in inline handler ${m[0]} before hashing`)
          return sha(m[2])
        })
        if (!scripts.length) throw new Error('csp: no inline script found in index.html, check the hashing still matches it')
        const policy = [
          "default-src 'self'",
          `script-src 'self' ${scripts.join(' ')}${handlers.length ? ` 'unsafe-hashes' ${handlers.join(' ')}` : ''} https://static.cloudflareinsights.com`,
          "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
          "font-src 'self' https://fonts.gstatic.com",
          "img-src 'self'",
          "media-src 'self'",
          "connect-src 'self' https://cloudflareinsights.com",
          "object-src 'none'",
          "base-uri 'self'",
          "form-action 'none'",
        ].join('; ')
        if (!/<meta charset[^>]*>/.test(html)) throw new Error('csp: no <meta charset> in index.html to place the policy after')
        return html.replace(/(<meta charset[^>]*>)/, `$1\n    <meta http-equiv="Content-Security-Policy" content="${policy}" />`)
      },
    },
  }
}

// base '/': history routing serves chapters at /<id>, so assets and data load from the root
export default defineConfig({
  plugins: [vue(), sitemap(), chapterPages(), csp()],
  base: '/',
})
