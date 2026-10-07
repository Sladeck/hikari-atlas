// Regenerates src/sizes.js (download sizes shown on the buttons) from public/wallpapers/full.
// Run after replacing any wallpaper PNG: npm run sizes
import { readdirSync, statSync, writeFileSync } from 'node:fs'

const dir = new URL('../public/wallpapers/full/', import.meta.url)
const rows = readdirSync(dir)
  .filter((f) => f.endsWith('.png'))
  .sort()
  .map((f) => ` "${f.slice(0, -4)}": ${(statSync(new URL(f, dir)).size / 1e6).toFixed(1)}`)

writeFileSync(new URL('../src/sizes.js', import.meta.url),
  `// PNG sizes in MB, generated from public/wallpapers/full by scripts/sizes.mjs (npm run sizes)\nexport const SIZES = {\n${rows.join(',\n')}\n}\n`)
console.log(`src/sizes.js: ${rows.length} files`)
