// What the board and the stage share: the chosen row, and the board turning over by itself.
// The board lives in the rail on every page; it only turns over while the front page is up.
// On a chapter page, pointing at a row lifts the stage over the chapter (a peek) until the pointer
// leaves the rail and the stage, so every chapter can be previewed from anywhere.
import { ref } from 'vue'
import { SECTIONS } from './sections.js'

export const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
export const DWELL = 7                                // seconds per row when the board runs by itself
const REST = 25                                       // seconds the board waits after the visitor's last touch

export const selected = ref(0)
export const auto = ref(false)
export const peeking = ref(false)                     // a chapter page with the stage lifted over it
let timer = 0, resumeAt = 0, running = false, shut = 0

function schedule() {
  clearTimeout(timer)
  if (reduce || !running) return
  timer = setTimeout(() => {
    if (document.visibilityState === 'visible' && performance.now() >= resumeAt) {
      selected.value = (selected.value + 1) % SECTIONS.length
      auto.value = true
    }
    schedule()
  }, DWELL * 1000)
}
export function start() { running = true; auto.value = !reduce && performance.now() >= resumeAt; schedule() }
export function stop() { running = false; auto.value = false; clearTimeout(timer) }
export function touched() {
  resumeAt = performance.now() + REST * 1000
  auto.value = false
  schedule()
}
export function select(i) { touched(); selected.value = i }

export function peek(i) { clearTimeout(shut); selected.value = i; peeking.value = true }
export function hold() { clearTimeout(shut) }
export function unpeek(delay = 0) { clearTimeout(shut); shut = setTimeout(() => { peeking.value = false }, delay) }
