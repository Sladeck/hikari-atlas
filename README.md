# Hikari Atlas · 光の地図

Japan drawn only with light, from real scientific data: earthquakes, volcanoes, the 2011 tsunami,
typhoons, Mount Fuji, the rivers, the cherry blossom front, the autumn leaves, the railways and the
islands' own lights at night. Every image is a free OLED wallpaper:
every unlit pixel is exactly `#000000`, so OLED screens switch it off.

## Chapters

| Chapter | What it shows | Wallpapers |
|---|---|---|
| 富士山 Mount Fuji and other summits | 10 m contours from above, as a 3D cloud of points and as ridge lines; beside it Kita-dake and Oku-hotaka-dake, the next highest | 7: Fuji ×3, Kita-dake and Oku-hotaka from the east and in ridge lines |
| 地震 Earthquakes | 30,167 quakes of M4.5+ since 1973, size = magnitude, colour = depth | Japan + 6 regions, the plates in 3D, Tōhoku 2011 and Kumamoto 2016 sequences |
| 火山 Volcanoes | 116 volcanoes and their eruptions from the Smithsonian GVP, coloured by time since the last one | 3: Japan, above the sinking plate, eruption stripes since 1600 |
| 津波 Tsunami | The 2011 Tōhoku tsunami simulated across the Pacific from the shallow-water equations, and the marks it left on Japan's coast | 3: the Pacific, how high it reached, how far inland on the Sendai plain |
| 台風 Typhoons | 1,951 storms tracked by JMA, 1951 to 2025, coloured by central pressure | 4: all storms, decade by decade, Vera 1959, Hagibis 2019 |
| 川 Rivers | 42,984 river reaches from HydroRIVERS, each as bright as its average flow | 4: Japan, river systems, Kantō, Hokkaido |
| 桜 Sakura | The first-bloom front at 102 cities, 1953 to 2018, a map of how much earlier each city now blooms, Kyoto since 812, and stripes for every city | 4 |
| 紅葉 Autumn leaves | The first red maple at 90 JMA cities, 1953 to 2025, and the ginkgo's first yellow; both now come later | 4: the leaf front, ginkgo gold, a map of how much later, stripes |
| 鉄道 Railways | Every line in its official colour, Shinkansen in white | Tokyo, Kansai, Japan |
| 夜 Japan at night | Japan's own lights from NASA's Black Marble 2016, Korea, China and Russia switched off | 3: Japan, the Tōkaidō corridor, light and rivers |

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

- **One page, two panes** (`src/App.vue`): a rail (`StationRail.vue`) holds the name and a station
  departure board (発車標, `DepartureBoard.vue`) of every chapter at the left of every page; only
  the pane beside it changes. Pages size themselves against the pane (container queries on `pane`),
  not the window.
- **Live stage** (`src/components/StageLayer.vue`, `ParticleStage.vue`): two phases. On the front
  page (`HomePage.vue`) the stage is the page: pointing at a board row shows that chapter's
  animation, rebuilding the same 36,000 points of light (22,000 on phones) into its scene (Fuji is
  real 3D), and the board turns over by itself until touched (`src/station.js`). Clicking opens the
  chapter's details. On a chapter page the board is plain navigation, and an arrow at the top left
  of the content returns to the front page, which opens on that chapter. Without WebGL the stage
  shows the chapters' still images instead.
- **Languages** (`src/i18n.js`): the whole site in English or Japanese, one at a time, from the
  EN / 日本語 switch (`LangSwitch.vue`) in the rail, or in the header on phones. Interface strings
  live in `i18n.js`; chapter text is in `src/sections.js` (English) and `src/sections.ja.js`
  (Japanese, same fields, wallpaper notes under `notes`). A new chapter needs both.
- **Phones**: the stage sits on top with the board under it; on chapter pages the board moves into
  the header's 目次 button (`IndexMenu.vue`). A new chapter needs its `code`, `kind`, `record`,
  `scene` and `still` in `src/sections.js`, plus its particle scene from `export_particles.py`.
- **Loading screen** (`index.html`): inline HTML/CSS, painted before the app loads, driven by the
  real download progress of the particle data.
- **Chapters** (`src/components/SectionPage.vue`, content in `src/sections.js`): a live animation
  per chapter (`src/components/anim/`), wallpaper gallery, fullscreen viewer, method and sources.
- **Assets** (`public/`): `wallpapers/full` PNG downloads, `wallpapers/preview` and
  `wallpapers/feature` WebP previews, `data/` and `particles/` binary data for the animations,
  `video/` the pre-rendered tsunami.

## The images (`pipeline/`)

Python 3 with NumPy, SciPy, pandas, Pillow (plus `pyreadr`/`rdata`, `tifffile`, `h5py`,
`scikit-image`, `pyshp`). Run the scripts from inside `pipeline/`: each one writes PNGs to `pipeline/out/`, and
the two `export_*` scripts write the site's data straight into `public/data` and `public/particles`.

| Script | Output | Data |
|---|---|---|
| `render_views.py` | Earthquake views | USGS ComCat CSVs, M4.5+, 1973 to today |
| `quakes_3d.py` | The plates in 3D | the same USGS CSVs |
| `sequences.py` (+ `jma_hypo.py`) | Tōhoku 2011 and Kumamoto 2016 sequences | JMA earthquake catalogue, 2011 and 2016 |
| `tsunami.py`, `tsunami_render.py` | Tsunami still (+ `--video`) | ETOPO1 10 arc-minute relief |
| `tsunami_coast.py` | Tsunami heights and inland reach on the coast | 2011 Tohoku Earthquake Tsunami Joint Survey, HydroRIVERS (land), Natural Earth (shore) |
| `typhoons.py` | Typhoon tracks | JMA RSMC Tokyo best track (`bst_all.txt`) |
| `typhoon_decades.py` | Typhoons decade by decade | the same best track |
| `famous_typhoons.py` | Typhoon Vera (1959) and Hagibis (2019) | the same best track, Natural Earth coastline |
| `fuji.py`, `fuji_points.py` | Fuji from above, in 3D | 30 m elevation model of Fuji |
| `fuji_ridges.py` | Fuji's summit cone in ridge lines (works for any mountain) | the same model |
| `mountains.py` | Kita-dake and Oku-hotaka-dake as layered skylines and ridge lines | Copernicus DEM GLO-30 |
| `sakura.py`, `sakura_map.py` | Sakura front chart and map | JMA first-bloom dates, Natural Earth coastline |
| `sakura_stripes.py` | Sakura stripes | JMA first-bloom dates |
| `kyoto.py` | Kyoto, 1,200 years | Kyoto peak-bloom dates since 812 (Aono et al., via Our World in Data) |
| `volcanoes.py` | Volcano views and eruption stripes (first run fetches and caches `dl/gvp/`) | Smithsonian GVP web service, HydroRIVERS (land), USGS CSVs (plate) |
| `rivers.py` | River views (first run caches Japan's reaches in `dl/hydrorivers/japan.npz`) | HydroRIVERS v1.0 Asia, Natural Earth land |
| `momiji.py` | Autumn leaf front, ginkgo, map and stripes | JMA phenology CSVs (かえで紅葉, いちょう黄葉), sakura station positions |
| `trains.py` | Railway views | 国土数値情報 railway data |
| `night.py` | Japan at night views, and the nightfall layers for the animation | NASA Black Marble 2016 tile D1, the rivers.py land mask |
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
| `copdem/Copernicus_DSM_COG_10_{N35_00_E138_00,N36_00_E137_00}_DEM.tif`, rewritten once to `*_raw.tif` with `gdal_translate -co COMPRESS=NONE` | `mountains.py` |
| `jma-hypo/h2011`, `h2016` (unzipped yearly files) | `sequences.py` |
| `topo/earth-topography-10arcmin.nc` | `tsunami.py` |
| `tsunami/ttjt_survey_29-Dec-2012_tidecorrected_web.csv` (Shift-JIS) | `tsunami_coast.py` |
| `Typhoon-Search/bst_all.txt` | `typhoons.py`, `export_web.py` |
| `sakura/data/flowering.csv`, `locations.csv` | `sakura*.py` |
| `ne/land10.geojson` | `sakura_map.py`, `rivers.py`, `night.py` |
| `kyoto/kyoto_peak_bloom.csv` | `kyoto.py` |
| `gvp/volcanoes.json`, `eruptions.json`, and `volcanoes_nt.json`, `eruptions_nt.json` for the Northern Territories (fetched by `volcanoes.py`) | `volcanoes.py`, `export_web.py` |
| `hydrorivers/raw/HydroRIVERS_v10_as_shp/` (unzipped Asia shapefile) | `rivers.py`, `export_web.py` |
| `jma-phenology/015.csv`, `013.csv` (JMA 生物季節観測累年値) | `momiji.py`, `export_web.py` |
| `jprailway/data/*.rda` | `trains.py` |
| `blackmarble/BlackMarble_2016_D1_geo_gray.tif` (cut to `japan_2016.png` on first run) | `night.py`, `export_web.py` |

The earthquake CSVs from USGS go in `pipeline/usgs/`.

## Sources

Every image is made from public data. Each provider keeps its own terms; the table gives them as
the providers state them, and the credit to use.

| Data | Provider | Terms | Used for |
|---|---|---|---|
| [ANSS Comprehensive Earthquake Catalog](https://earthquake.usgs.gov/fdsnws/event/1/) | U.S. Geological Survey | Public domain (U.S. Government work) | Earthquakes, Volcanoes (plate) |
| [震源データ, JMA earthquake catalogue](https://www.data.jma.go.jp/eqev/data/bulletin/hypo.html) | Japan Meteorological Agency (気象庁) | [JMA content terms](https://www.jma.go.jp/jma/kishou/info/coment.html), 公共データ利用規約 第1.0版: credit required, edits stated | Tōhoku and Kumamoto sequences |
| [ETOPO1 Global Relief Model](https://doi.org/10.7289/V5C8276M) | NOAA National Centers for Environmental Information | Public domain | Tsunami |
| [Earth topography grid, 10 arc-minutes](https://github.com/fatiando-data/earth-topography-10arcmin) ([doi:10.5281/zenodo.5882203](https://doi.org/10.5281/zenodo.5882203)) | Fatiando a Terra, from ETOPO1 | CC BY 4.0 | Tsunami |
| [Tsunami field survey, release 20121229](https://coastal.jp/ttjt/) | 2011 Tohoku Earthquake Tsunami Joint Survey Group (Mori et al. 2012) | Free to use, citing the group, the site and the release date | Tsunami (coast) |
| [RSMC Tokyo best track data](https://www.jma.go.jp/jma/jma-eng/jma-center/rsmc-hp-pub-eg/besttrack.html) | Japan Meteorological Agency | JMA content terms | Typhoons |
| [Fuji elevation model](https://github.com/bjlittle/geovista-data) | bjlittle/geovista-data | BSD 3-Clause | Mount Fuji |
| [Copernicus DEM GLO-30](https://registry.opendata.aws/copernicus-dem/) | European Union and ESA, Copernicus programme (TanDEM-X, DLR and Airbus) | Licence for the Copernicus WorldDEM-30: free reproduction, distribution and adaptation, notices below required | Kita-dake, Oku-hotaka-dake |
| [HydroRIVERS v1.0](https://www.hydrosheds.org/products/hydrorivers) | WWF, HydroSHEDS (Lehner & Grill 2013) | HydroSHEDS v1 licence agreement: free for non-commercial and commercial use, statement below required | Rivers; the land in Volcanoes, Night and the tsunami coast |
| [さくらの開花日](https://www.data.jma.go.jp/sakura/data/index.html) | Japan Meteorological Agency, compiled by [akg314/sakura](https://github.com/akg314/sakura) | JMA content terms | Sakura |
| [Kyoto peak bloom since 812](https://ourworldindata.org/grapher/date-of-the-peak-cherry-tree-blossom-in-kyoto) | Aono & Kazui (2008), Aono & Saito (2010), Katata (2026), via Our World in Data | CC BY 4.0 (Our World in Data) | Sakura (Kyoto) |
| [生物季節観測累年値](https://www.data.jma.go.jp/sakura/data/download_ruinenchi.html) (かえでの紅葉, いちょうの黄葉) | Japan Meteorological Agency | JMA content terms | Autumn leaves |
| [Volcanoes of the World](https://volcano.si.edu/) | Global Volcanism Program, Smithsonian Institution (accessed October 2026) | Credit required | Volcanoes |
| [国土数値情報 鉄道データ](https://nlftp.mlit.go.jp/ksj/) | Ministry of Land, Infrastructure, Transport and Tourism (国土交通省), via [paithiov909/jprailway](https://github.com/paithiov909/jprailway) | MLIT terms (CC BY 4.0 for 2020 and later, 商用可 before); jprailway CC BY 4.0 | Railways |
| [Black Marble 2016](https://science.nasa.gov/earth/earth-observatory/earth-at-night/maps/) (Suomi NPP VIIRS) | NASA Earth Observatory | NASA imagery, credit requested | Japan at night |
| [Solar position equations](https://gml.noaa.gov/grad/solcalc/solareqns.PDF) | NOAA Global Monitoring Laboratory | Public domain | Japan at night (nightfall) |
| [Natural Earth](https://www.naturalearthdata.com/) coastline | Natural Earth | Public domain | Coastlines, the land mask |

Credits in the providers' own form:

- **Japan Meteorological Agency:** 出典：気象庁ホームページ. 気象庁の震源データ、台風ベストトラック、
  さくらの開花日、生物季節観測累年値を加工して作成.
- **MLIT:** 「国土数値情報（鉄道データ）」（国土交通省）（https://nlftp.mlit.go.jp/ksj/）をもとに
  Moulin Guillaume 作成・加工.
- **Tsunami survey:** Data are from the 2011 Tohoku Earthquake Tsunami Joint Survey Group, release
  20121229, http://www.coastal.jp/ttjt/.
- **Copernicus DEM:** produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved. The organisations in charge of the Copernicus programme by law or by
  delegation do not incur any liability for any use of the Copernicus WorldDEM-30.
- **Global Volcanism Program:** Global Volcanism Program, Smithsonian Institution, *Volcanoes of the
  World*, https://volcano.si.edu/ (accessed October 2026).
- **HydroSHEDS:** This product Hikari Atlas incorporates data from the HydroSHEDS version 1 database
  which is © World Wildlife Fund, Inc. (2006-2022) and has been used herein under license. WWF has
  not evaluated the data as altered and incorporated within Hikari Atlas, and therefore gives no
  warranty regarding its accuracy, completeness, currency or suitability for any particular
  purpose. Portions of the HydroSHEDS v1 database incorporate data which are the intellectual
  property rights of © USGS (2006-2008), NASA (2000-2005), ESRI (1992-1998), CIAT (2004-2006),
  UNEP-WCMC (1993), WWF (2004), Commonwealth of Australia (2007), and Her Royal Majesty and the
  British Crown and are used under license. The HydroSHEDS v1 database and more information are
  available at https://www.hydrosheds.org.
- **Scientific citations:** Lehner, B., Grill, G. (2013), Global river hydrography and network
  routing, *Hydrological Processes* 27(15): 2171-2186, https://doi.org/10.1002/hyp.9740.
  Lehner, B., Verdin, K., Jarvis, A. (2008), New global hydrography derived from spaceborne
  elevation data, *Eos* 89(10): 93-94. Amante, C., Eakins, B. W. (2009), ETOPO1 1 Arc-Minute
  Global Relief Model, NOAA, https://doi.org/10.7289/V5C8276M. Mori, N., Takahashi, T., and The
  2011 Tohoku Earthquake Tsunami Joint Survey Group (2012), Nationwide survey of the 2011 Tohoku
  earthquake tsunami, *Coastal Engineering Journal* 54(1): 1-27,
  https://doi.org/10.1142/S0578563412500015.

None of the providers has evaluated or endorsed these images. The tsunami starts from an idealised
seafloor uplift, not the published rupture model, so its wave heights are approximate.

## Credits

- **Idea:** [Blackbody: scientific OLED wallpapers](https://alistair-roberts.co.uk/blackbody) by
  [Alistair Roberts](https://alistair-roberts.co.uk/): black wallpapers rendered in code from real
  scientific data and physics, each with its sources. Hikari Atlas takes that idea to Japan with
  its own data, renders, design and code.
- **Fonts:** [Shippori Mincho](https://fonts.google.com/specimen/Shippori+Mincho),
  [Zen Kaku Gothic New](https://fonts.google.com/specimen/Zen+Kaku+Gothic+New) and
  [IBM Plex Mono](https://fonts.google.com/specimen/IBM+Plex+Mono), all SIL Open Font License,
  served by Google Fonts. Captions on the images use Noto Sans CJK (SIL Open Font License) or the
  system's Hiragino Sans.
- **Libraries:** [Vue](https://vuejs.org/) and [Vue Router](https://router.vuejs.org/) (MIT),
  [GSAP](https://gsap.com/) ([standard no-charge licence](https://gsap.com/standard-license)),
  [Vite](https://vite.dev/) (MIT); in the pipeline NumPy, SciPy, pandas, Pillow, scikit-image,
  h5py, tifffile, rdata and pyshp.

## Licence

Hikari Atlas by [Moulin Guillaume](https://gmmoulin.com).

- **Images, videos and data files** (`public/wallpapers`, `public/video`, `public/data`,
  `public/particles`, and the renders in `pipeline/out/`):
  [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Share and adapt them freely for
  non-commercial use, crediting "Hikari Atlas by Moulin Guillaume (https://gmmoulin.com), CC BY-NC
  4.0" and keeping the data credits above. See [LICENSE-IMAGES.md](LICENSE-IMAGES.md).
- **Code:** [PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0).
  Free to use, modify and share for any non-commercial purpose. See [LICENSE](LICENSE).

For commercial use, ask the author.
