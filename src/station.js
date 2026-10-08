// What the board and the stage share: the chosen row, and the board turning over by itself.
// The board lives in the rail on every page; it only turns over while the front page is up.
import { ref } from 'vue'
import { SECTIONS } from './sections.js'

export const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
export const DWELL = 7                                // seconds per row when the board runs by itself
const REST = 25                                       // seconds the board waits after the visitor's last touch

export const selected = ref(0)
export const auto = ref(false)
let timer = 0, resumeAt = 0, running = false

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
