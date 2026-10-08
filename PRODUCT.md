# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Curious people who come for the beauty of the data and leave with a wallpaper: they explore Japan
through earthquakes, typhoons, cherry blossoms and the rest, and the free OLED wallpapers are the
reward for exploring. Most will arrive on a phone as often as on a desktop, since phone wallpapers
are half of what the site gives away.

## Product Purpose

Hikari Atlas (光の地図, "map of light") draws Japan only with light, from real scientific data, one
chapter per subject. Each chapter has a live animation, a gallery of desktop (3840×2160) and phone
(1290×2796) wallpapers, and a "How it's made" section with method and sources. Success is a visitor
who explores more than one chapter and downloads a wallpaper.

It is both a personal showcase of craft and a public resource meant to be found and used by anyone
interested in Japan, OLED wallpapers or data art.

## Positioning

Every image is computed from real, cited data (USGS, JMA, NOAA, MLIT, Natural Earth, Aono et al.),
never drawn by hand, and every unlit pixel is exactly #000000 so OLED screens switch it off. Japan
is the only subject. The idea comes from Blackbody by Alistair Roberts (credited in the README);
Hikari Atlas takes it to Japan with its own data, renders and code.

## Operating Context

- Vue 3 + Vite static site with hash routing, so the build works from any folder or static host.
- Wallpapers and animation data are produced offline by the Python pipeline in `pipeline/`
  (render, then `publish.py`, then `npm run sizes`), and served from `public/`.
- Chapters today: Earthquakes, Tsunami, Typhoons, Mount Fuji, Sakura front, Railways.
  Planned: Autumn leaves (紅葉前線), Volcanoes, Rivers, Japan at night, bringing it to about ten.
- Every page holds a departure board of the chapters in a rail; pointing at a row shows that
  chapter's particle scene on a live stage, clicking opens it. This scales to ten chapters.

## Capabilities and Constraints

- Pure black is the ground: no unlit pixel may be anything but #000000, in renders and in the UI.
- Each chapter: kanji name, title, lede, three facts, colour scale, live animation, wallpapers,
  method notes, sources, and its own accent colour.
- Animations must pause off-screen, respect reduced motion, and fall back to stills without WebGL.
- Bilingual: the whole site exists in English and Japanese, one language at a time, chosen by the visitor
  (Japanese is currently identity: kanji names and titles; text is English).
- Open decision: hosting and domain.

## Brand Commitments

- Name: Hikari Atlas · 光の地図. The 光 glyph is the mark (loading screen, header).
- Each chapter keeps its kanji name and its own light: amber quakes, aqua tsunami, ice typhoons,
  red Fuji, pink sakura, line-colour railways.
- Voice: plain, precise English; honest about method (approximations and exaggerations are stated,
  as with the tsunami source model and the ×2 depth of the 3D plates).
- Credit to Blackbody / Alistair Roberts stays.

## Evidence on Hand

- 25 wallpapers (desktop + phone each) in `public/wallpapers/full`, previews in `preview/`,
  front-page stills in `feature/`.
- Animation data in `public/data`, front-page particles in `public/particles`, tsunami video in
  `public/video`.
- No testimonials, users, press or traffic numbers exist; none may be invented.

## Product Principles

1. The data is the picture: nothing decorative that is not measured.
2. Black is free light: every element earns its pixels on an OLED screen.
3. Wonder first, then the download: the animations draw visitors in, the wallpapers reward them.
4. Every claim is cited and every approximation is stated.
5. Japan only.

## Accessibility & Inclusion

Reduced motion is honoured everywhere (stills instead of animation); controls meet 44 px touch
targets; text contrast on black is kept legible; animations have text alternatives.
