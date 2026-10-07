// Loads the pre-projected binary data exported by export_web.py (cached per page load).
const base = import.meta.env.BASE_URL
const cache = {}

export function load(name, Type = Float32Array) {
  cache[name] ||= fetch(`${base}data/${name}`).then((r) => {
    if (!r.ok) throw new Error(`${name}: ${r.status}`)
    return r.arrayBuffer()
  }).then((b) => new Type(b))
  return cache[name]
}
export function meta() {
  cache.meta ||= fetch(`${base}data/meta.json`).then((r) => r.json())
  return cache.meta
}

// interpolate a list of [stop, [r,g,b]] (0..1 colours) -> css rgb string
export function ramp(stops) {
  return (v) => {
    if (v <= stops[0][0]) return stops[0][1]
    for (let i = 1; i < stops.length; i++) {
      if (v <= stops[i][0]) {
        const [a, ca] = stops[i - 1], [b, cb] = stops[i], t = (v - a) / (b - a)
        return ca.map((c, k) => c + (cb[k] - c) * t)
      }
    }
    return stops[stops.length - 1][1]
  }
}
export const rgba = (c, a = 1) => `rgba(${Math.round(c[0] * 255)},${Math.round(c[1] * 255)},${Math.round(c[2] * 255)},${a})`

// soft round glow sprite in a given colour, for fast additive drawing
const spriteCache = new Map()
export function glowSprite(c, size = 32) {
  const key = c.join(',') + size
  if (spriteCache.has(key)) return spriteCache.get(key)
  const s = document.createElement('canvas'); s.width = s.height = size
  const g = s.getContext('2d'), r = size / 2
  const grad = g.createRadialGradient(r, r, 0, r, r, r)
  grad.addColorStop(0, rgba(c, 1)); grad.addColorStop(0.25, rgba(c, 0.55)); grad.addColorStop(1, rgba(c, 0))
  g.fillStyle = grad; g.fillRect(0, 0, size, size)
  spriteCache.set(key, s)
  return s
}
