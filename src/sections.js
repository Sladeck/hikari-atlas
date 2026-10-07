// Content for every section: copy, colours, wallpapers, method notes and sources.
// Wallpaper files live in public/wallpapers/{preview,full}/<file>_{desktop,phone}.{webp,png}

export const SECTIONS = [
  {
    id: 'earthquakes',
    short: 'Quakes',
    kanji: '地震',
    kana: 'じしん',
    title: 'Earthquakes',
    accent: '#ffcf8a',
    accent2: '#8c33d9',
    anim: 'quakes',
    lede:
      'Every earthquake of magnitude 4.5 or more recorded around Japan since 1973. Each point of light is one quake: size is magnitude, colour is depth. No coastline is drawn. The plates draw Japan by themselves.',
    facts: [
      ['30,167', 'earthquakes'],
      ['M9.1', 'largest, 11 March 2011'],
      ['683 km', 'deepest, Izu–Bonin slab'],
    ],
    scale: { label: 'Hypocentre depth', from: '0 km', to: '650 km', stops: ['#ffdb9e', '#ff7330', '#e6294d', '#8c33d9', '#4059ff'] },
    wallpapers: [
      { file: 'japan', jp: '日本', en: 'Japan', note: 'Four plates meet under Japan. The bright band is the Japan Trench; the violet branch hanging below is the Pacific plate sinking towards 680 km under the Izu–Bonin arc. The frame holds 27,900 of the 30,167 quakes; the rest lie in the faded tails.' },
      { file: 'quakes_3d', jp: '沈み込み', en: 'The plates in 3D', note: 'The 22,141 quakes east of 136°E lifted out of the map, each at its real depth, seen from above the Pacific. The bright arc is the trench; beneath it the Pacific plate hangs as a sheet of light, and under the Izu–Bonin arc it plunges almost straight down to 680 km. Depth is stretched twice so the slab can be seen.' },
      { file: 'tohoku', jp: '東北', en: 'Tōhoku', note: 'The densest glow offshore is the aftershock zone of the 2011 Great Tōhoku earthquake: more than 3,700 quakes of M4.5+ in the following twelve months.' },
      { file: 'tokyo', jp: '東京・関東', en: 'Tokyo & Kantō', note: 'Off the Bōsō Peninsula, three plates meet at one of the few trench-trench-trench triple junctions on Earth.' },
      { file: 'kurils', jp: '北海道・千島', en: 'Hokkaido & Kurils', note: 'The Kuril Trench runs from Hokkaido to Kamchatka. Red and violet flecks are quakes inside the slab, hundreds of kilometres down.' },
      { file: 'izu', jp: '伊豆・小笠原', en: 'Izu–Bonin Trench', note: 'Subduction in one picture: the amber line is the shallow arc, the violet line beside it is the same plate seen 600 km deeper.' },
      { file: 'ryukyu', jp: '琉球', en: 'Ryūkyū Arc', note: 'The Philippine Sea plate dives under the Ryūkyū islands. Behind the arc, the Okinawa Trough is slowly rifting open.' },
      { file: 'west', jp: '西日本', en: 'Western & Central Japan', note: 'Quieter inland, which makes its big events stand out: Kobe 1995, Kumamoto 2016 and Noto 2024.' },
      { file: 'tohoku_2011', jp: '東日本大震災', en: 'The week after the M9', note: 'Every quake of M2.5 and up that JMA located in the seven days after 14:46 on 11 March 2011: 7,138 of them, filling a zone 500 km long within hours. White marks the first hours, amber the days after; the brightest star is the M9.0 itself.' },
      { file: 'kumamoto_2016', jp: '熊本地震', en: 'Kumamoto 2016', note: 'An M6.5 on 14 April, then an M7.3 on the same fault 28 hours later. The 13,445 quakes of M1.5 and up to the end of 2016 trace the Futagawa and Hinagu faults, white where the first hours struck, then run north-east past Aso towards Ōita as later bursts cool to red.' },
    ],
    method: [
      ['Data', 'USGS earthquake catalogue (ComCat), magnitude 4.5 and up, 1973 to October 2026, box 121–150°E, 23–47°N. Nuclear tests and landslides are filtered out.'],
      ['Light', 'Each quake is a Gaussian glow added into a float buffer, never painted over, so dense trenches build up light on their own. Quakes of M7+ get four faint rings.'],
      ['Rotation', 'The national view is rotated along its main axis (found with PCA) so the arc fills the long side of the screen. A small arrow marks north.'],
      ['Sequences', 'The Tōhoku and Kumamoto pictures use the JMA earthquake catalogue, which records far smaller quakes than the USGS one. Colour there is time since the first big shock, on a log scale, from white to deep red.'],
      ['3D view', 'Each quake is placed at its longitude, latitude and depth in kilometres, depth stretched twice, and seen through a perspective camera from above the Pacific. West of 136°E the quakes fade out, so the view holds the Pacific plate alone.'],
    ],
    sources: [
      ['USGS ANSS Comprehensive Earthquake Catalog', 'https://earthquake.usgs.gov/fdsnws/event/1/'],
      ['JMA earthquake catalogue (震源データ)', 'https://www.data.jma.go.jp/eqev/data/bulletin/hypo.html'],
    ],
  },
  {
    id: 'tsunami',
    short: 'Tsunami',
    kanji: '津波',
    kana: 'つなみ',
    title: 'Tsunami',
    accent: '#5ee6ff',
    accent2: '#0a3a8c',
    anim: 'tsunami',
    lede:
      'The 2011 Tōhoku tsunami crossing the Pacific, simulated from the shallow-water equations on the real depth of the ocean. The bright beams are not drawn by hand: undersea ridges act like lenses and channel the energy towards Hawaii, Chile and New Zealand.',
    facts: [
      ['24 h', 'of ocean simulated'],
      ['~700 km/h', 'wave speed over deep ocean'],
      ['1,051 × 745', 'grid cells, 10 arc-minutes'],
    ],
    scale: { label: 'Highest wave', from: '5 cm', to: '4 m', stops: ['#06123d', '#004d8c', '#00b3cc', '#8cf2ff', '#ffffff'] },
    wallpapers: [
      { file: 'tsunami', jp: '津波', en: 'Tōhoku tsunami, 2011', note: 'The highest wave reached at every point of the Pacific in the 24 hours after the earthquake. Faint rings mark each hour of travel time.' },
    ],
    method: [
      ['Physics', 'Linear shallow-water equations on a sphere, solved on a staggered grid every 12.5 seconds of simulated time. Land is a wall; the open edges absorb the wave.'],
      ['Source', 'An idealised seafloor uplift along the Japan Trench: about +5 m on the trench side and −2 m landward, 400 by 150 km. Close to the real event, not the published rupture model, so heights are approximate.'],
      ['Ocean depth', 'ETOPO1 bathymetry resampled to 10 arc-minutes (about 18 km).'],
    ],
    sources: [
      ['ETOPO1 Global Relief Model (NOAA)', 'https://doi.org/10.7289/V5C8276M'],
      ['Earth topography grid, 10 arc-minutes (Fatiando a Terra)', 'https://github.com/fatiando-data/earth-topography-10arcmin'],
    ],
  },
  {
    id: 'typhoons',
    short: 'Typhoons',
    kanji: '台風',
    kana: 'たいふう',
    title: 'Typhoons',
    accent: '#7fe8ff',
    accent2: '#0d38f2',
    anim: 'typhoons',
    lede:
      'Every typhoon tracked by the Japan Meteorological Agency from 1951 to 2019. Storms are born in the warm tropics, drift west, then curve north and east towards Japan. The violent ones, below 930 hPa at their peak, burn white.',
    facts: [
      ['1,784', 'storms'],
      ['326', 'below 930 hPa'],
      ['69', 'seasons'],
    ],
    scale: { label: 'Central pressure', from: '1006 hPa', to: '905 hPa', stops: ['#0d38f2', '#008cff', '#1ae6ff', '#b3ffff', '#ffffff'] },
    wallpapers: [
      { file: 'typhoons', jp: '台風', en: 'Northwest Pacific typhoons', note: 'Every storm is a faint line; those that reached 930 hPa or lower are drawn bright, whitest where they peaked. The fan opening north-east is the recurve that brings typhoons to Japan.' },
    ],
    method: [
      ['Data', 'JMA RSMC Tokyo best track: 6-hourly position, grade and central pressure of every storm since 1951.'],
      ['Colour', 'Lower pressure means a stronger storm: deep blue at birth, cyan as it deepens, white at its peak. Extratropical tails fade to violet.'],
    ],
    sources: [['JMA RSMC Tokyo best track data', 'https://www.jma.go.jp/jma/jma-eng/jma-center/rsmc-hp-pub-eg/besttrack.html']],
  },
  {
    id: 'fuji',
    short: 'Fuji',
    kanji: '富士山',
    kana: 'ふじさん',
    title: 'Mount Fuji',
    accent: '#ff8a4c',
    accent2: '#4d1a8c',
    anim: 'fuji',
    lede:
      'Mount Fuji as glowing contour lines, one every 10 metres, coloured like the red Fuji of a summer sunrise: indigo at the foot, crimson on the slopes, white at the 3,776 m summit. The notch on the south-east flank is the Hōei crater of 1707, the last eruption.',
    facts: [
      ['3,776 m', 'summit'],
      ['10 m', 'between contours'],
      ['30 m', 'elevation grid'],
    ],
    scale: { label: 'Elevation', from: '0 m', to: '3,776 m', stops: ['#291a73', '#731a8c', '#d91f4d', '#ff6b2e', '#ffcc8c', '#ffffff'] },
    wallpapers: [
      { file: 'fuji', jp: '富士山', en: 'Mount Fuji', note: 'Contours bunch together where the cone is steepest. The flat ring at the base is the old lava plain that surrounds the mountain.' },
      { file: 'fuji_side', jp: '南から', en: 'Fuji from the south', note: 'The same contour rings seen in perspective from 30 km south and 3 km up, at true vertical scale. Lines behind the slope are hidden with a depth buffer built from the terrain. The dark gash on the right flank is the Hōei crater.' },
      { file: 'fuji_points', jp: '光の富士', en: 'Fuji in light', note: 'The 3D view from the front page as a wallpaper: 640,000 points along every 10 m contour from 1,000 m to the summit, each at its real position, seen in perspective. The lower slopes dissolve into the dark; the crater notch sits on top.' },
    ],
    method: [
      ['Data', 'A 1 arc-second (about 30 m) elevation model of the Fuji area.'],
      ['Lines', 'Contours traced every 10 m with marching squares; every 100 m slightly brighter. Low hills are dimmed so the cone stays the subject.'],
      ['Side view', 'The rings are lifted to their real height and projected through a virtual camera. A depth buffer rendered from the elevation model decides which parts of each ring are hidden behind the mountain.'],
    ],
    sources: [['geovista-data: Fuji DEM', 'https://github.com/bjlittle/geovista-data']],
  },
  {
    id: 'sakura',
    short: 'Sakura',
    kanji: '桜',
    kana: 'さくら',
    title: 'Sakura front',
    accent: '#ff8fbf',
    accent2: '#fff5f8',
    anim: 'sakura',
    lede:
      'The first cherry blossom of the year at 102 cities, from 1953 to 2018. Each flower is one city in one year. The front sweeps from Okinawa in January to Wakkanai in late May. Older years are white, recent years pink, and pink tends to bloom first.',
    facts: [
      ['5,843', 'first-bloom dates'],
      ['102', 'cities'],
      ['~4 months', 'from Okinawa to Hokkaido'],
    ],
    scale: { label: 'Year', from: '1953', to: '2018', stops: ['#fff7fa', '#ff6ba8'] },
    wallpapers: [
      { file: 'sakura', jp: '桜前線', en: 'The sakura front', note: 'Left to right is the calendar, bottom to top is latitude. The isolated row in April at the bottom is a southern island station; Okinawa\'s January blooms are a different, early cherry.' },
      { file: 'sakura_map', jp: '桜の地図', en: 'Cherry blossom map', note: 'Every JMA observation city as a blossom. The deeper the pink, the earlier that city\'s first bloom now comes compared with the 1950s: 81 of 100 cities bloom earlier, the median city by about 5 days over 66 years. Pale blossoms have barely moved.' },
    ],
    method: [
      ['Data', 'JMA phenological observations: first-bloom date of the reference cherry tree at each station.'],
      ['Flowers', 'Each bloom is a five-petal sprite, randomly turned, blended additively so busy weeks glow.'],
      ['Map', 'For each city with 30+ years of records, the trend of its first-bloom day is fitted with a Theil–Sen slope, which ignores odd years. Four station positions that were geocoded to towns abroad in the source file are corrected to their JMA sites.'],
    ],
    sources: [
      ['JMA さくらの開花日', 'https://www.data.jma.go.jp/sakura/data/index.html'],
      ['Dataset compiled by akg314/sakura', 'https://github.com/akg314/sakura'],
    ],
  },
  {
    id: 'railways',
    short: 'Rail',
    kanji: '鉄道',
    kana: 'てつどう',
    title: 'Railways',
    accent: '#7dff9a',
    accent2: '#ff9c33',
    anim: 'trains',
    lede:
      'Every railway line in Japan in its official line colour, with the Shinkansen in white. Tokyo is the densest tangle on Earth: the green ring of the Yamanote line, the orange Chūō line cutting straight through it, and dozens of private lines fanning out to the suburbs.',
    facts: [
      ['603', 'lines in service'],
      ['8,989', 'stations'],
      ['1964', 'first Shinkansen'],
    ],
    scale: { label: 'Official line colours', from: 'JR', to: 'Shinkansen', stops: ['#00b261', '#ff8c00', '#e6334d', '#1a80e6', '#ffffff'] },
    wallpapers: [
      { file: 'trains_tokyo', jp: '東京', en: 'Tokyo', note: 'The Yamanote loop with every line that crosses it. The white lines are the Tōhoku, Jōetsu and Tōkaidō Shinkansen meeting at Tokyo Station.' },
      { file: 'trains_kansai', jp: '関西', en: 'Osaka, Kyoto & Kobe', note: 'Three cities joined by competing parallel lines: JR, Hankyu, Hanshin and Keihan all race between Osaka, Kyoto and Kobe.' },
      { file: 'trains_japan', jp: '日本', en: 'Japan', note: 'The whole network, rotated so the islands run along the screen. The Shinkansen is the white spine from Kagoshima to Hokkaido.' },
    ],
    method: [
      ['Data', 'National Land Numerical Information (国土数値情報) railway data, via the jprailway package: track geometry, official line colours, stations.'],
      ['Colour', 'Each line keeps its official colour, slightly lifted so dark colours still glow. Lines without one are a dim warm white. Closed lines are left out.'],
    ],
    sources: [
      ['国土数値情報 鉄道データ (MLIT)', 'https://nlftp.mlit.go.jp/ksj/'],
      ['jprailway (paithiov909)', 'https://github.com/paithiov909/jprailway'],
    ],
  },
]
