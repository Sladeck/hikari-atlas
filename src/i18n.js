// The site's two languages. One is shown at a time, chosen with the switch in the rail (or the
// header on phones), remembered per browser, and first guessed from the browser's own language.
// Interface strings live here; chapter text in English is in sections.js, in Japanese in sections.ja.js.
import { ref, watch, computed } from 'vue'
import { SECTIONS } from './sections.js'
import { JA } from './sections.ja.js'

const KEY = 'hikari-lang'
function first() {
  try { const v = localStorage.getItem(KEY); if (v === 'en' || v === 'ja') return v } catch { /* storage blocked */ }
  return /^ja\b/i.test(navigator.language || '') ? 'ja' : 'en'
}
export const lang = ref(first())
watch(lang, (v) => {
  try { localStorage.setItem(KEY, v) } catch { /* storage blocked */ }
  document.documentElement.lang = v
}, { immediate: true })

const UI = {
  en: {
    name: 'Hikari Atlas',
    language: 'Language',
    skip: 'Skip to content',
    home: 'Hikari Atlas, front page',
    homeTitle: 'Hikari Atlas: Japan drawn only with light',
    thesis: 'Japan drawn only with light, from real data. Every chapter ends in free OLED wallpapers.',
    foot1: ['Japan drawn as light on pure black, from public scientific data. Every unlit pixel is exactly ', ', so OLED screens switch it off. Wallpapers are free to use.'],
    foot2: 'Rendered in Python with NumPy, SciPy and Pillow. Animations run on the same data in the browser, with Vue and GSAP.',
    chapters: 'Chapters',
    allChapters: 'All chapters',
    heads: ['Type', 'Destination', 'Record'],
    preview: 'Chapter preview',
    open: (t) => `Open ${t}`,
    count: (n) => `${n} wallpapers`,
    wallpapers: 'Wallpapers',
    countLine: (n) => `${n} PNG · desktop 3840×2160 · phone 1290×2796`,
    jump: 'Jump to a wallpaper',
    how: "How it's made",
    sources: 'Sources',
    next: 'Next',
    scale: (label, from, to) => `${label} colour scale from ${from} to ${to}`,
    phone: 'Phone',
    desktop: 'Desktop',
    viewFull: (name, kind) => `View ${name} ${kind} wallpaper fullscreen`,
    alt: (name, kind) => `${name}, ${kind} wallpaper`,
    loadingFull: 'Loading full resolution…',
    failedFull: 'The full-size file did not load; this is the preview.',
    prevImage: 'Previous image',
    nextImage: 'Next image',
    download: 'Download',
    close: 'Close',
    play: 'Play',
    pause: 'Pause',
    playAnim: 'Play animation',
    pauseAnim: 'Pause animation',
    replay: 'Replay',
    replayAnim: 'Replay animation from the start',
    replayFuji: 'Replay the sunrise reveal',
    loadingData: 'Loading data…',
    failedData: 'The animation data could not load. The wallpapers below still work.',
    gathering: 'Gathering light',
    lighting: 'Lighting',
    anim: {
      quakes: ['Animation: earthquakes around Japan appearing year by year from 1973 to 2026', 'M4.5+ · USGS'],
      typhoons: ['Animation: every Northwest Pacific typhoon from 1951 to 2025 drawing its track, season by season', 'JMA best track · bright = below 930 hPa'],
      sakura: ['Animation: the cherry blossom front sweeping from Okinawa in January to Hokkaido in May, 1953 to 2018', 'First bloom · 102 cities · 1953 white → 2018 pink'],
      trains: ['Animation: trains moving along every railway line in central Tokyo, in official line colours', 'Central Tokyo · trains illustrative, not timetable'],
      tsunami: ['Animation: the 2011 Tōhoku tsunami spreading across the Pacific over 24 hours, simulated', 'Simulated · hours after 11 March 2011, 14:46 JST', 'Simulated tsunami spreading across the Pacific Ocean'],
      fuji: ['Animation: Mount Fuji contour lines appearing from the summit downwards like sunrise', 'Red Fuji · contours every 10 m'],
      rivers: ['Animation: every river in Japan flowing from its springs down to the sea', 'Distance from the farthest spring · HydroRIVERS'],
    },
  },
  ja: {
    name: '光の地図',
    language: '言語',
    skip: '本文へ移動',
    home: '光の地図、トップページ',
    homeTitle: '光の地図：光だけで描いた日本',
    thesis: '本物のデータから、光だけで描いた日本。どの章の最後にも、有機EL向けの無料の壁紙があります。',
    foot1: ['公開されている科学データから、日本を純粋な黒の上の光として描いています。光っていないピクセルはすべて正確に ', ' なので、有機ELの画面ではその部分が消灯します。壁紙は自由に使えます。'],
    foot2: '描画はPythonとNumPy、SciPy、Pillowで。ブラウザのアニメーションも同じデータを、VueとGSAPで動かしています。',
    chapters: '目次',
    allChapters: 'すべての章',
    heads: ['種別', '行先', '記録'],
    preview: '章のプレビュー',
    open: (t) => `${t}を開く`,
    count: (n) => `壁紙 ${n}枚`,
    wallpapers: '壁紙',
    countLine: (n) => `PNG ${n}枚 · デスクトップ 3840×2160 · スマートフォン 1290×2796`,
    jump: '壁紙へ移動',
    how: '作り方',
    sources: '出典',
    next: '次の章',
    scale: (label, from, to) => `${label}の色の目盛り、${from}から${to}まで`,
    phone: 'スマートフォン',
    desktop: 'デスクトップ',
    viewFull: (name, kind) => `${name}の${kind}用壁紙を全画面で見る`,
    alt: (name, kind) => `${name}、${kind}用の壁紙`,
    loadingFull: 'フル解像度を読み込み中…',
    failedFull: 'フルサイズのファイルを読み込めませんでした。表示しているのはプレビューです。',
    prevImage: '前の画像',
    nextImage: '次の画像',
    download: 'ダウンロード',
    close: '閉じる',
    play: '再生',
    pause: '一時停止',
    playAnim: 'アニメーションを再生',
    pauseAnim: 'アニメーションを一時停止',
    replay: 'もう一度',
    replayAnim: 'アニメーションを最初から再生',
    replayFuji: '朝焼けの演出をもう一度再生',
    loadingData: 'データを読み込み中…',
    failedData: 'アニメーションのデータを読み込めませんでした。下の壁紙はそのまま使えます。',
    gathering: '光を集めています',
    lighting: '点灯中',
    anim: {
      quakes: ['アニメーション：1973年から2026年まで、日本周辺の地震が1年ずつ現れる', 'M4.5以上 · USGS'],
      typhoons: ['アニメーション：1951年から2025年まで、北西太平洋のすべての台風がシーズンごとに進路を描く', '気象庁ベストトラック · 明るい線は930 hPa未満'],
      sakura: ['アニメーション：1953年から2018年まで、1月の沖縄から5月の北海道へと北上する桜前線', '開花日 · 102都市 · 1953年 白 → 2018年 ピンク'],
      trains: ['アニメーション：都心のすべての鉄道路線を、公式のラインカラーで走る列車', '都心 · 列車の動きはイメージで、時刻表ではありません'],
      tsunami: ['アニメーション：2011年東北地方太平洋沖地震の津波が、24時間かけて太平洋に広がるシミュレーション', 'シミュレーション · 2011年3月11日14時46分からの経過時間', '太平洋に広がる津波のシミュレーション'],
      fuji: ['アニメーション：朝焼けのように、富士山の等高線が山頂から下へ現れる', '赤富士 · 10 mごとの等高線'],
      rivers: ['アニメーション：日本のすべての川が、源流から海へと流れ下る', 'もっとも遠い源流からの距離 · HydroRIVERS'],
    },
  },
}
// the interface string for the current language: t('next'), or t('open', title) for a phrase
export function t(key, ...args) {
  const v = UI[lang.value][key]
  return typeof v === 'function' ? v(...args) : v
}
// the same, outside a component render (the loading screen, the frame loop)
export const ui = (key) => UI[lang.value][key]

// a chapter in the current language: same shape in both, with `name` and `kind` resolved to strings
function inJapanese(s) {
  const j = JA[s.id]
  return {
    ...s, ...j,
    kind: s.kind.jp,
    scene: { ...s.scene, ...j.scene },
    scale: { ...s.scale, ...j.scale },
    wallpapers: s.wallpapers.map((w) => ({ ...w, name: w.jp, note: j.notes[w.file] })),
  }
}
function inEnglish(s) {
  return { ...s, kind: s.kind.en, wallpapers: s.wallpapers.map((w) => ({ ...w, name: w.en })) }
}
const BOTH = { en: SECTIONS.map(inEnglish), ja: SECTIONS.map(inJapanese) }
export const sections = computed(() => BOTH[lang.value])
export const local = (s) => sections.value.find((x) => x.id === s.id)
