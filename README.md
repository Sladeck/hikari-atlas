# Hikari Atlas · 光の地図

Japan drawn only with light, from real scientific data: earthquakes, the 2011 tsunami, typhoons,
Mount Fuji, the cherry blossom front and the railways. Every image is a free OLED wallpaper:
every unlit pixel is exactly `#000000`, so OLED screens switch it off.

## Chapters

| Chapter | What it shows | Wallpapers |
|---|---|---|
| 地震 Earthquakes | 30,167 quakes of M4.5+ since 1973, size = magnitude, colour = depth | Japan + 6 regions, the plates in 3D, Tōhoku 2011 and Kumamoto 2016 sequences |
| 津波 Tsunami | The 2011 Tōhoku tsunami simulated across the Pacific from the shallow-water equations | 1 |
| 台風 Typhoons | 1,951 storms tracked by JMA, 1951 to 2025, coloured by central pressure | 4: all storms, decade by decade, Vera 1959, Hagibis 2019 |
| 富士山 Mount Fuji | 10 m contours from above, in perspective from the south, and as a 3D cloud of points | 3 |
| 桜 Sakura | The first-bloom front at 102 cities, 1953 to 2018, a map of how much earlier each city now blooms, Kyoto since 812, and stripes for every city | 4 |
| 鉄道 Railways | Every line in its official colour, Shinkansen in white | Tokyo, Kansai, Japan |

Each wallpaper comes in desktop (3840×2160) and phone (1290×2796) versions.

## The site

Vue 3 + Vite, GSAP for motion, plain WebGL for the front page.

```bash
npm install
npm run dev -- --host        # dev server, also reachable from a phone on the same Wi-Fi
npm run build                # static site in dist/ (works from any static host or folder)
npm run preview -- --host    # serve the built site
npm run sizes                # after replacing wallpaper PNGs: refresh the sizes on the download buttons
```

- **Front page** (`src/components/HomePage.vue`): a station departure board (発車標,
  `DepartureBoard.vue`) of every chapter beside one live WebGL stage (`ParticleStage.vue`).
  Choosing a row rebuilds the same 36,000 points of light (22,000 on phones) into that chapter's
  scene; Fuji is real 3D. The rows alternate Japanese and English like real station boards, and the
  board turns over by itself until touched. Falls back to still images without WebGL.
- **Chapter index** (`src/components/IndexMenu.vue`): the 目次 button in the header drops the same
  board down from any chapter page. A new chapter needs its `code`, `kind`, `record`, `scene` and
  `still` in `src/sections.js`, plus its particle scene from `export_particles.py`.
- **Loading screen** (`index.html`): inline HTML/CSS, painted before the app loads, driven by the
  real download progress of the particle data.
- **Chapters** (`src/components/SectionPage.vue`, content in `src/sections.js`): a live animation
  per chapter (`src/components/anim/`), wallpaper gallery, fullscreen viewer, method and sources.
- **Assets** (`public/`): `wallpapers/full` PNG downloads, `wallpapers/preview` and
  `wallpapers/feature` WebP previews, `data/` and `particles/` binary data for the animations,
  `video/` the pre-rendered tsunami.

## The images (`pipeline/`)

Python 3 with NumPy, SciPy, pandas, Pillow (plus `pyreadr`/`rdata`, `tifffile`, `h5py`,
`scikit-image`). Run the scripts from inside `pipeline/`: each one writes PNGs to `pipeline/out/`, and
the two `export_*` scripts write the site's data straight into `public/data` and `public/particles`.

| Script | Output | Data |
|---|---|---|
| `render_views.py` | Earthquake views | USGS ComCat CSVs, M4.5+, 1973 to today |
| `quakes_3d.py` | The plates in 3D | the same USGS CSVs |
| `sequences.py` (+ `jma_hypo.py`) | Tōhoku 2011 and Kumamoto 2016 sequences | JMA earthquake catalogue, 2011 and 2016 |
| `tsunami.py`, `tsunami_render.py` | Tsunami still (+ `--video`) | ETOPO1 10 arc-minute relief |
| `typhoons.py` | Typhoon tracks | JMA RSMC Tokyo best track (`bst_all.txt`) |
| `typhoon_decades.py` | Typhoons decade by decade | the same best track |
| `famous_typhoons.py` | Typhoon Vera (1959) and Hagibis (2019) | the same best track, Natural Earth coastline |
| `fuji.py`, `fuji_side.py`, `fuji_points.py` | Fuji from above, from the south, in 3D | 30 m elevation model of Fuji |
| `sakura.py`, `sakura_map.py` | Sakura front chart and map | JMA first-bloom dates, Natural Earth coastline |
| `sakura_stripes.py` | Sakura stripes | JMA first-bloom dates |
| `kyoto.py` | Kyoto, 1,200 years | Kyoto peak-bloom dates since 812 (Aono et al., via Our World in Data) |
| `trains.py` | Railway views | 国土数値情報 railway data |
| `export_web.py`, `export_particles.py` | Data for the site's animations | the renders and datasets above |
| `publish.py` | Copies renders to `public/` and writes the gallery previews | the renders above |

`common.py` holds the shared idea: light is *added* into a float buffer (never painted over),
blurred into a soft core and a wide glow, tone-mapped with `1 - exp(-x)`, and every unlit pixel is
forced to exactly black.

Raw datasets are not in the repo. Put them under `pipeline/dl/` (ignored by git), or point the
`HIKARI_DL` environment variable at another folder; `common.py` resolves every path from there:

| Path under `dl/` | Used by |
|---|---|
| `geovista-data/assets/rasters/fuji_dem.tif` | `fuji*.py` |
| `jma-hypo/h2011`, `h2016` (unzipped yearly files) | `sequences.py` |
| `topo/earth-topography-10arcmin.nc` | `tsunami.py` |
| `Typhoon-Search/bst_all.txt` | `typhoons.py`, `export_web.py` |
| `sakura/data/flowering.csv`, `locations.csv` | `sakura*.py` |
| `ne/land10.geojson` | `sakura_map.py` |
| `kyoto/kyoto_peak_bloom.csv` | `kyoto.py` |
| `jprailway/data/*.rda` | `trains.py` |

The earthquake CSVs from USGS go in `pipeline/usgs/`.

## Data

- Earthquakes: [USGS ANSS Comprehensive Earthquake Catalog](https://earthquake.usgs.gov/fdsnws/event/1/); for the sequences, the [JMA earthquake catalogue](https://www.data.jma.go.jp/eqev/data/bulletin/hypo.html)
- Ocean depth: [ETOPO1, NOAA](https://doi.org/10.7289/V5C8276M), via [fatiando-data/earth-topography-10arcmin](https://github.com/fatiando-data/earth-topography-10arcmin)
- Typhoons: [JMA RSMC Tokyo best track data](https://www.jma.go.jp/jma/jma-eng/jma-center/rsmc-hp-pub-eg/besttrack.html)
- Mount Fuji elevation: [bjlittle/geovista-data](https://github.com/bjlittle/geovista-data)
- Cherry blossoms: [JMA さくらの開花日](https://www.data.jma.go.jp/sakura/data/index.html), compiled by [akg314/sakura](https://github.com/akg314/sakura)
  (four misgeocoded station positions are corrected in the scripts); Kyoto since 812: Aono & Kazui (2008), Aono & Saito (2010), Katata (2026),
  via [Our World in Data](https://ourworldindata.org/grapher/date-of-the-peak-cherry-tree-blossom-in-kyoto)
- Railways: [国土数値情報 鉄道データ, MLIT](https://nlftp.mlit.go.jp/ksj/), via [paithiov909/jprailway](https://github.com/paithiov909/jprailway)
- Coastline: [Natural Earth](https://www.naturalearthdata.com/)

The tsunami starts from an idealised seafloor uplift, not the published rupture model, so wave
heights are approximate.

## Credits

The idea comes from **[Blackbody: scientific OLED wallpapers](https://alistair-roberts.co.uk/blackbody)**
by [Alistair Roberts](https://alistair-roberts.co.uk/) ([source on GitHub](https://github.com/robertsalistair-jpg/blackbody-oled)):
black wallpapers rendered in code from real scientific data and physics, each with its sources.
Hikari Atlas takes that idea to Japan with its own data, renders, design and code.
