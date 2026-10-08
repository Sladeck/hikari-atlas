---
name: Hikari Atlas
description: Japan drawn only with light, from real data, on pixels that are switched off.
colors:
  pixels-off: "#000000"
  paper-light: "#e6e0d8"
  ash: "#a39b90"
  ember-edge: "#5e564d"
  soot-hairline: "#3a3530"
  night-rule: "#1c1a18"
  quake-amber: "#ffcf8a"
  tsunami-aqua: "#5ee6ff"
  typhoon-ice: "#7fe8ff"
  fuji-red: "#ff8a4c"
  river-blue: "#8fb4ff"
  sakura-pink: "#ff8fbf"
  railway-green: "#7dff9a"
typography:
  display-kanji:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, Yu Mincho, serif"
    fontSize: "clamp(44px, 7vw, 96px)"
    fontWeight: 700
    lineHeight: 1.08
  display:
    fontFamily: "Zen Kaku Gothic New, Hiragino Sans, Yu Gothic, system-ui, sans-serif"
    fontSize: "clamp(36px, 3.6vw, 56px)"
    fontWeight: 300
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Zen Kaku Gothic New, Hiragino Sans, Yu Gothic, system-ui, sans-serif"
    fontSize: "clamp(30px, 3.6vw, 48px)"
    fontWeight: 300
    lineHeight: 1.05
    letterSpacing: "-0.015em"
  title:
    fontFamily: "Zen Kaku Gothic New, Hiragino Sans, Yu Gothic, system-ui, sans-serif"
    fontSize: "28px"
    fontWeight: 300
  title-mincho:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, Yu Mincho, serif"
    fontSize: "28px"
    fontWeight: 500
    lineHeight: 1.15
  destination-kanji:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, Yu Mincho, serif"
    fontSize: "22px"
    fontWeight: 700
    letterSpacing: "0.06em"
  lede:
    fontFamily: "Zen Kaku Gothic New, Hiragino Sans, Yu Gothic, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 300
  body:
    fontFamily: "Zen Kaku Gothic New, Hiragino Sans, Yu Gothic, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "Zen Kaku Gothic New, Hiragino Sans, Yu Gothic, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
  figure:
    fontFamily: "IBM Plex Mono, ui-monospace, SF Mono, Menlo, monospace"
    fontSize: "13px"
    fontWeight: 400
    fontFeature: "tnum"
rounded:
  none: "0px"
  badge: "6px"
spacing:
  gutter: "clamp(16px, 4vw, 56px)"
  max-width: "1360px"
  touch: "44px"
  control-min: "36px"
  board-row: "58px"
  board-row-home: "48px"
  board-row-phone: "54px"
  board-row-compact: "50px"
components:
  control:
    backgroundColor: "{colors.pixels-off}"
    textColor: "{colors.paper-light}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "6px 14px"
    height: "36px"
  control-hover:
    backgroundColor: "{colors.pixels-off}"
    textColor: "{colors.quake-amber}"
  chapter-action:
    backgroundColor: "{colors.pixels-off}"
    textColor: "{colors.quake-amber}"
    rounded: "{rounded.none}"
    padding: "0 18px"
    height: "44px"
  chapter-action-hover:
    backgroundColor: "{colors.quake-amber}"
    textColor: "{colors.pixels-off}"
  index-button:
    backgroundColor: "{colors.pixels-off}"
    textColor: "{colors.paper-light}"
    rounded: "{rounded.none}"
    padding: "0 14px"
    height: "44px"
  board-row:
    backgroundColor: "{colors.pixels-off}"
    textColor: "{colors.ash}"
    rounded: "{rounded.none}"
    padding: "0 14px"
    height: "58px"
  board-row-selected:
    textColor: "{colors.paper-light}"
  line-badge:
    backgroundColor: "{colors.pixels-off}"
    textColor: "{colors.quake-amber}"
    typography: "{typography.figure}"
    rounded: "{rounded.badge}"
    width: "40px"
    height: "30px"
  line-badge-selected:
    backgroundColor: "{colors.quake-amber}"
    textColor: "{colors.pixels-off}"
---

# Design System: Hikari Atlas

## Overview

**Creative North Star: "The Night Atlas"**

Hikari Atlas is a black page on which only light is drawn. The ground is pixels switched off (#000000), and everything that shows up is either measured light from the data or the thin, warm interface that frames it. The interface never competes with the light: it is set in hairlines, outlines and quiet paper-white text, and it borrows its single colour from whichever chapter is in view. When the visitor moves between chapters, the whole interface re-tints to that chapter's light over most of a second.

Japanese is identity, not decoration. Each chapter carries its kanji in Shippori Mincho, standing vertically (tategaki) beside its live stage on chapter pages, and the front page and chapter index are a station departure board (発車標). The site speaks one language at a time, English or Japanese, chosen with a switch beside the rail's name; in Japanese, destinations and chapter and wallpaper names are set in Mincho. Mono type appears only where something is counted or measured.

Density is calm: few elements, generous black, one live stage per view. Motion is slow and eased out (`cubic-bezier(.16, 1, .3, 1)`), pauses off-screen, and gives way to stills and side-by-side faces under reduced motion.

**Key Characteristics:**
- Pure black ground and solid black control fills; no grey surfaces.
- One accent at a time, the current chapter's light, tweened on navigation.
- Square, outlined controls; the 6px rounded line badge is the only rounded control shape.
- Depth by glow and darkness (accent halos, black veils), not by lifted cards.
- Mincho for kanji and names, light-weight Zen Kaku Gothic for text, IBM Plex Mono for figures.
- One language at a time: the board, captions and chapter text follow the language switch.

## Colors

A warm-neutral ladder of greys on pure black, lit by one chapter colour at a time.

### Primary
- **Quake Amber** (quake-amber): the default interface light and the Earthquakes chapter's own colour; also the loading screen's 光 and progress line. Whatever chapter is in view, its colour takes this role through the live `--accent` property: links, focus rings, control hover, the brand mark, section kanji, method terms.

### Secondary (chapter lights)
Each chapter owns one light, set per chapter in `src/sections.js` and used as the board row's line colour (`--lc`), the stage caption's tone (`--tone`), and the interface accent when that chapter is chosen.
- **Tsunami Aqua** (tsunami-aqua): Tsunami.
- **Typhoon Ice** (typhoon-ice): Typhoons.
- **Fuji Red** (fuji-red): Mount Fuji; in practice a red-orange sunrise tone.
- **River Blue** (river-blue): Rivers; a periwinkle kept clear of the Tsunami and Typhoon cyans, and placed between Fuji and Sakura on the board.
- **Sakura Pink** (sakura-pink): Sakura front.
- **Railway Green** (railway-green): Railways.

### Neutral
- **Pixels Off** (pixels-off): the page, every stage, every control fill, the dropped index panel, the lightbox.
- **Paper Light** (paper-light): primary text; warm, never pure white.
- **Ash** (ash): secondary text, labels, counts, idle board rows.
- **Ember Edge** (ember-edge): the border of every interactive control at rest.
- **Soot Hairline** (soot-hairline): non-interactive hairlines (board header rule, index panel border, phone-frame rim, scrollbar).
- **Night Rule** (night-rule): the faintest dividers: header and footer rules, board row separators, stage frames.

### Named Rules
**The Pixels-Off Rule.** Every unlit pixel is exactly #000000, in renders and in the UI. Controls are filled solid black so they stay legible over bright canvases; a lit tint is allowed only as light, never as a grey panel (the selected board row is the chapter colour mixed 8% into black).

**The One Light Rule.** The interface speaks in one chapter colour at a time. On navigation the accent is tweened to the new chapter's light (0.8 to 0.9 s, power2 ease-out; instant under reduced motion). Only the departure board shows several lights at once, each row in its own chapter's colour.

**The Edge, Not Hairline, Rule.** Interactive borders use Ember Edge; Soot Hairline and Night Rule are for dividers only and never outline a control.

## Typography

**Display Font:** Shippori Mincho (with Hiragino Mincho ProN, Yu Mincho, serif), weights 500 and 700
**Body Font:** Zen Kaku Gothic New (with Hiragino Sans, Yu Gothic, system-ui), weights 300, 400, 700
**Label/Mono Font:** IBM Plex Mono (with ui-monospace, SF Mono, Menlo), weights 300 and 400, tabular figures

**Character:** a brush-born Mincho carries the Japanese names with weight and glow, while a light (300) Gothic sets English headlines and prose almost whispered against black; mono is the instrument readout.

### Hierarchy
- **Display Kanji** (Mincho 700, clamp(44px, 7vw, 96px), 1.08): the chapter's vertical kanji, in the accent with a soft glow. The next-chapter link uses the same face larger, clamp(64px, 12vw, 168px), at 55% opacity until hovered.
- **Display** (Gothic 300, clamp(30px, 2.5vw, 42px), 1.1, -0.02em): the rail's name: Hikari Atlas in English, 光の地図 in Japanese (Mincho 700, +0.12em, in the accent).
- **Headline** (Gothic 300, clamp(30px, 3.6vw, 48px), 1.05, -0.015em, balanced wrap): chapter titles. The stage caption title uses the same voice at clamp(24px, 2.6vw, 40px).
- **Title** (Gothic 300, 28px): gallery and method headings. **Title Mincho** (500, 28px, 1.15) names each wallpaper; a Japanese name never breaks mid-word.
- **Destination Kanji** (Mincho 700, 22px, +0.06em): the board's Japanese destination face; the English face is Gothic 17px.
- **Lede** (Gothic 300, 18px, max 64ch) and **Body** (Gothic 400, 16px, 1.65): prose; long text runs light (300) and stays within 52 to 68ch.
- **Label** (Gothic 400, 12 to 14px, Ash): data rows, counts, board column names, scale ends.
- **Figure** (Plex Mono 400, 12 to 13px, tabular): line codes, records, the JST clock, file sizes, live counters (counters run large, clamp(28px, 5vw, 64px), weight 300).

### Named Rules
**The Mono-Is-Measurement Rule.** IBM Plex Mono is reserved for things that are counted or measured: records, sizes, scales, counters, clock, line codes. Never for prose or headings.

**The One Language Rule.** The whole site is in English or in Japanese, never both side by side. A two-option switch (EN / 日本語, each written in its own language) sits beside the rail's name on wide screens and in the header on phones; the choice is remembered per browser and first guessed from the browser's language, and `<html lang>` follows it. The vertical kanji on chapter pages stay in both languages: they are the chapter's emblem, not text to read.

## Layout

Content sits in a centred column (max 1360px) with a fluid gutter (clamp(16px, 4vw, 56px)). The sticky header is translucent black (82%) with a 10px backdrop blur and a Night Rule underline; its measured height is published as `--hdr` so full-viewport stages fit beneath it.

The site is one page in two panes. On wide screens a rail (clamp(320px, 26vw, 400px)) holds the name with the language switch, the departure board and the thesis at the left of every page; it stays put (sticky, full height, its own scroll) while the window scrolls the pane beside it, and only the pane changes on navigation. On the front page the pane is the live stage, full height and edge to edge, with no header bar anywhere on wide screens. On a chapter page the same stage waits out of sight and lifts over the pane (0.45s fade) while a board row is pointed at for 140ms or more, falling back 240ms after the pointer leaves the rail and the stage, on Escape, or on a tap outside its caption. Pages inside the pane size themselves against it through container queries, not the window. At 860px and below it becomes one column: the header returns, the front page stage sits on top at half the viewport height (min 320px) with the board directly under it, and on chapter pages the rail is hidden and the board lives in the header's index menu.

Chapter pages pair the vertical kanji with a stage column, then alternate desktop and phone wallpapers in wide, generously spaced rows (clamp(56px, 8vw, 104px) apart), then method and sources in a 220px / fluid split, then the next chapter.

The departure board sizes itself to its own container, not the window: four or five grid columns (badge, type, destination, record, arrow) with 16px column gaps, dropping the type column below 460px. Row height is set per context (58px default, 48px in the rail, 54px on phones, 50px in the header index).

Breakpoints in use: 860px (one-column switch), 640px (touch-size controls), 560px and 520px (phone refinements). Every touch target is at least 44px.

## Elevation & Depth

The system is flat black lit from within. Depth comes from light and from darkness, not from raised surfaces: kanji and chosen destinations glow with a text-shadow of their own colour mixed 40 to 45% with transparent; text over live stages is protected by black halos (`text-shadow: 0 0 14-24px #000`) and by a veil, a bottom gradient from 92% black to transparent across the lower 42% of the stage.

### Shadow Vocabulary
- **Accent glow** (`text-shadow: 0 0 18-40px color-mix(in srgb, <light> 40-45%, transparent)`): section kanji, the selected destination, the next-chapter kanji on hover.
- **Black halo** (`text-shadow: 0 0 20px #000`): any text placed over a live canvas.
- **Drop into black** (`box-shadow: 0 24px 48px -16px rgba(0, 0, 0, .9)`): the dropped index panel and, with a 1px Soot Hairline ring, the phone frame. Ambient only; it darkens, never lifts.

### Named Rules
**The Light-Not-Lift Rule.** Nothing floats on a grey card. An element gains presence by glowing in its own light or by darkening what is behind it.

## Shapes

Square corners everywhere an interface control lives: buttons, the index panel, board rows and stage frames are 0px with 1px outlines (1.5px on line badges). The one rounded control shape is the line badge (6px), modelled on a station line symbol, outlined in the chapter colour and filled when chosen; the stage caption carries the same badge at 0.42em. Phone wallpapers sit inside a phone silhouette (outer radius 13% / 6%, screen radius 10% / 4.6%) so the phone ratio reads true.

Icons are a small inline SVG set drawn at 1.5px stroke with round caps and joins; controls never rely on Unicode glyphs.

## Components

### Buttons
Outlined, black-filled and quiet until touched.
- **Shape:** square (0px), 1px Ember Edge border, solid black fill.
- **Control:** Gothic 13px, 36px minimum height (44px on touch and below 640px), 8px gap to a 14px icon; used for playback, downloads and lightbox navigation.
- **Hover / Focus:** border and text turn to the accent over 0.2s; focus is a 2px accent outline offset 3px.
- **Chapter action:** the stage caption's Open button outlines in the chosen chapter's tone and fills with it on hover (text turns black); its arrow slides 5px right.
- **Index button:** the header's 目次 / Chapters disclosure, 44px, 14px text with a Mincho 目次; the chevron turns 180 degrees when open; below 520px only 目次 shows.

### Navigation
- **Header:** the 光 mark in Mincho 22px in the accent, then Hikari Atlas at 15px with +0.04em tracking; shown only at 860px and below; the index button sits at the right on every page except the front page.
- **Index panel:** the departure board in compact form dropped under the header (max 560px wide, full width below 520px), black with a Soot Hairline border and the drop-into-black shadow; it opens with a top-down clip reveal and closes on Escape, outside click or navigation.
- **Next chapter:** each chapter ends with the next chapter's large kanji and title in that chapter's own light.

### Departure Board (signature)
The atlas as a 発車標: one ruled row per chapter, separated by Night Rule hairlines under a Soot Hairline column header (種別 Type, 行先 Destination, 記録 Record) with a JST clock above it.
- **Row:** Ash at rest; on hover or selection the text turns Paper Light and the row fills with its chapter colour mixed 8% into black; the destination turns to the chapter colour with a glow; a stroked arrow fades in from 6px left. Focus is a 2px outline in the row's colour, inset.
- **Line badge:** a 40 by 30px mono code (EQ, TS, TY, FJ, SK, RW) outlined in the chapter colour, filled when chosen.
- **Dwell line:** while the board turns over by itself, a 1px line in the chosen row's colour fills along its bottom edge over the dwell time (7s); it is hidden under reduced motion.
- **Language:** every cell shows the current language only (One Language Rule).
- **Touch:** on hover devices pointing selects; on touch the first tap previews and the second opens.

### Live Stage
A black frame (1px Night Rule border on chapter pages) holding the canvas, a top-left Ash caption at 13px, a large mono counter bottom-right in the accent, and controls bottom-left. On the front page the stage is frameless, with the veil and caption at its foot. Without WebGL it crossfades chapter stills over 1.2s.

### Wallpaper Card
A desktop shot (16:9) beside a phone silhouette, alternating sides from row to row; shots brighten (1.18) on hover and open in a pure black lightbox whose bar fades in from below. The meta row holds the wallpaper's name (Mincho in Japanese, light Gothic in English), a light note, and download controls with mono file sizes.

## Do's and Don'ts

### Do:
- **Do** keep every unlit pixel at #000000, including control fills, panels and the lightbox.
- **Do** take the accent from the chapter in view and tween it on navigation; on the board, give each row its own chapter colour.
- **Do** outline interactive controls in Ember Edge, square-cornered, with at least 44px touch targets.
- **Do** set Japanese names in Shippori Mincho, and show one language at a time.
- **Do** reserve IBM Plex Mono with tabular figures for measurements, codes, sizes and the clock.
- **Do** protect text over live light with a black halo or the veil rather than a panel.
- **Do** ease motion with `cubic-bezier(.16, 1, .3, 1)`, pause off-screen, and fall back to stills under reduced motion or without WebGL.

### Don't:
- **Don't** introduce grey or tinted panel surfaces; a lit tint is only a chapter colour mixed into black.
- **Don't** show two chapter accents in the interface at once outside the departure board.
- **Don't** outline controls with Soot Hairline or Night Rule; those are dividers.
- **Don't** set prose or headings in mono.
- **Don't** use Unicode glyphs as icons; use the 1.5px stroked SVG set.
- **Don't** raise elements with light-coloured or offset shadows; depth is glow or darkness.
