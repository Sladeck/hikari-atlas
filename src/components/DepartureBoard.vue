<script setup>
// The atlas as a station departure board (発車標): one row per chapter, a line badge in the
// chapter's own colour, its category (種別), destination and headline record (sources live on
// each chapter page). Like the boards in Japanese stations, the rows alternate between Japanese
// and English every few seconds. Rows are links. In preview mode (the front page), pointing at a row
// selects it and the stage follows; on touch, the first tap selects and the second opens.
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  sections: { type: Array, required: true },
  selected: { type: Number, default: -1 },
  compact: { type: Boolean, default: false },     // the header's index menu: rows only
  dwell: { type: Number, default: 0 },            // seconds until the board moves on by itself (0 = still)
  face: { type: Boolean, default: null },         // English face when true; null = the board keeps its own time
  preview: { type: Boolean, default: false },     // rows preview a scene before opening (the front page's stage)
})
const emit = defineEmits(['select'])

const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
const hover = window.matchMedia('(hover: hover)').matches
const own = ref(false)                               // false = Japanese face, true = English face
const en = computed(() => props.face ?? own.value)
const clock = ref('')
let flip = 0, tick = 0

function now() { clock.value = new Date().toLocaleTimeString('en-GB', { timeZone: 'Asia/Tokyo', hour: '2-digit', minute: '2-digit' }) + ' JST' }
onMounted(() => {
  if (!reduce && props.face === null) flip = setInterval(() => { own.value = !own.value }, 4200)
  if (!props.compact) { now(); tick = setInterval(now, 15000) }      // Japan time, like every board in Japan
})
onBeforeUnmount(() => { clearInterval(flip); clearInterval(tick) })

const heads = [['種別', 'Type'], ['行先', 'Destination'], ['記録', 'Record']]
function point(i) { if (hover && props.preview) emit('select', i) }
// on touch, whether a tap previews or opens is decided when the finger lands: browsers that focus
// links on tap would otherwise mark the row selected before the click arrives
let press = null
function down(e, i) { press = e.pointerType === 'mouse' ? null : { i, was: i === props.selected } }
function focused(i) { if (!press && props.preview) emit('select', i) }                 // keyboard focus follows along
function tap(e, i) {
  const p = press; press = null
  if (hover || !props.preview || !p || p.i !== i || p.was) return    // the link opens the chapter
  e.preventDefault(); emit('select', i)                              // touch: first tap previews the scene
}
</script>

<template>
  <nav class="board" :class="{ compact, en, still: reduce }" :aria-label="compact ? 'All chapters' : 'Chapters'">
    <div v-if="!compact" class="board-head" aria-hidden="true">
      <span></span>
      <span v-for="(h, i) in heads" :key="i" class="flipcell" :class="`h${i}`"><span lang="ja">{{ h[0] }}</span><span>{{ h[1] }}</span></span>
      <span class="clock mono">{{ clock }}</span>
    </div>
    <ol class="rows">
      <li v-for="(s, i) in sections" :key="s.id" :style="{ '--lc': s.accent }">
        <router-link :to="`/${s.id}`" class="row" :class="{ on: i === selected }"
                     @pointerenter="point(i)" @pointerdown="down($event, i)" @focus="focused(i)" @click.capture="tap($event, i)">
          <span class="badge mono" aria-hidden="true">{{ s.code }}</span>
          <span class="kind flipcell" aria-hidden="true"><span lang="ja">{{ s.kind.jp }}</span><span>{{ s.kind.en }}</span></span>
          <span class="dest flipcell" aria-hidden="true"><span lang="ja" class="jp">{{ s.kanji }}</span><span class="enname">{{ s.title }}</span></span>
          <span class="record mono" aria-hidden="true">{{ s.record }}</span>
          <span class="visually-hidden">{{ s.title }} (<span lang="ja">{{ s.kanji }}</span>), {{ s.kind.en }}: {{ s.record }}</span>
          <svg class="go" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14m0 0l-6-6m6 6l-6 6" /></svg>
          <span v-if="dwell && i === selected && !reduce" :key="`dwell-${selected}`" class="dwell" :style="{ animationDuration: dwell + 's' }" aria-hidden="true"></span>
        </router-link>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
/* the board sizes itself to its own width (front page column or header panel), not the window's */
.board { container-type: inline-size; overflow-x: clip; --row: 58px; }
.board-head, .row { --cols: 42px 60px minmax(0, 1fr) auto 18px; }
@container (min-width: 520px) { .board-head, .row { --cols: 46px 70px minmax(0, 1fr) auto 20px; } }
@container (max-width: 460px) { .board-head, .row { --cols: 40px minmax(0, 1fr) auto 16px; }
  .row .kind, .board-head .h0 { display: none; } }
.board-head { position: relative; display: grid; grid-template-columns: var(--cols); column-gap: 16px; align-items: end;
  margin-top: 26px; padding: 0 14px 10px; border-bottom: 1px solid var(--faint); color: var(--dim); font-size: 12px; letter-spacing: .04em; }
/* the board's own clock, in Japan time, on the line above the column names */
.clock { position: absolute; right: 14px; bottom: calc(100% + 6px); font-size: 12px; color: var(--fg); white-space: nowrap; }
.rows { list-style: none; margin: 0; padding: 0; }
.rows li { border-bottom: 1px solid var(--line); }

.row { position: relative; display: grid; grid-template-columns: var(--cols); column-gap: 16px; align-items: center;
  min-height: var(--row); padding: 0 14px; color: var(--dim); text-decoration: none;
  transition: background-color .35s var(--ease-out), color .35s var(--ease-out); }
.row:hover, .row.on { color: var(--fg); background: color-mix(in srgb, var(--lc) 8%, #000); }
.row:focus-visible { outline: 2px solid var(--lc); outline-offset: -2px; }
.row.router-link-active { color: var(--fg); }

/* the line symbol: an outlined square in the chapter's colour, filled when it is the chosen row */
.badge { display: grid; place-items: center; width: 40px; height: 30px; border: 1.5px solid var(--lc); border-radius: 6px;
  color: var(--lc); font-size: 13px; font-weight: 400; letter-spacing: .04em; transition: background-color .35s, color .35s; }
.row.on .badge { background: var(--lc); color: #000; }
.kind { font-size: 12px; color: var(--dim); }
.dest { font-size: 17px; color: inherit; }
.dest .jp { font-family: var(--mincho); font-weight: 700; font-size: 22px; letter-spacing: .06em; }
.row.on .dest { color: var(--lc); text-shadow: 0 0 18px color-mix(in srgb, var(--lc) 45%, transparent); }
.record { font-size: 13px; color: inherit; white-space: nowrap; }
.go { width: 18px; height: 18px; fill: none; stroke: var(--lc); stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round;
  opacity: 0; transform: translateX(-6px); transition: opacity .3s, transform .4s var(--ease-out); }
.row.on .go, .row:hover .go { opacity: 1; transform: none; }
/* how long until the board moves on by itself */
.dwell { position: absolute; left: 0; bottom: -1px; height: 1px; width: 100%; background: var(--lc); transform-origin: left;
  animation: dwell linear both; opacity: .8; }
@keyframes dwell { from { transform: scaleX(0); } to { transform: scaleX(1); } }

/* Japanese and English faces share one cell and roll past each other, as on a station board */
.flipcell { position: relative; display: grid; overflow: hidden; height: 1.6em; line-height: 1.6em; }
.flipcell > span { grid-area: 1 / 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  transition: transform .6s var(--ease-out), opacity .6s var(--ease-out); }
.flipcell > span:last-child { transform: translateY(100%); opacity: 0; }
.en .flipcell > span:first-child { transform: translateY(-100%); opacity: 0; }
.en .flipcell > span:last-child { transform: none; opacity: 1; }
.dest.flipcell { height: 1.7em; line-height: 1.7em; }
/* reduced motion: no rolling; both faces side by side */
.still .flipcell { display: flex; gap: .6em; height: auto; }
.still .flipcell > span { transform: none !important; opacity: 1 !important; }
.still .flipcell > span:last-child { color: var(--dim); font-size: .8em; }

.compact { --row: 50px; }
.compact .row { padding: 0 12px; }

@container (max-width: 460px) { .board-head, .row { column-gap: 12px; padding-inline: 10px; } }
@media (prefers-reduced-motion: reduce) { .dwell { display: none; } }
</style>
