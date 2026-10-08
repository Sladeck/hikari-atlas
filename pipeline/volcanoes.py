"""Volcanoes of Japan as light, from the Smithsonian Global Volcanism Program.

Data: Volcanoes of the World (Global Volcanism Program, Smithsonian Institution), fetched from its
public web service on first run and cached in dl/gvp/: every Holocene volcano listed for Japan, and
every eruption recorded at them (start and end dates, VEI explosivity 0..8).

    python volcanoes.py                 # every view, desktop and phone, into out/
    python volcanoes.py japan stripes   # some of them (japan, slab, stripes)
    python volcanoes.py --info          # what the cache holds
"""
import os
import sys
import json
import urllib.parse
import urllib.request
import numpy as np
from PIL import ImageDraw, ImageFont
from common import Canvas, caption, save, EquiProj, dl, DESKTOP, PHONE, F_LIGHT

WFS = ("https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows?service=WFS&version=1.0.0"
       "&request=GetFeature&outputFormat=application%2Fjson")


def _get(type_name, cql):
    u = f"{WFS}&typeName=GVP-VOTW:{type_name}&CQL_FILTER={urllib.parse.quote(cql)}"
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "hikari-atlas"}), timeout=120) as r:
        return json.load(r)["features"]


def fetch():
    os.makedirs(dl("gvp"), exist_ok=True)
    v = _get("Smithsonian_VOTW_Holocene_Volcanoes", "Country='Japan'")
    nums = ",".join(str(f["properties"]["Volcano_Number"]) for f in v)
    e = _get("Smithsonian_VOTW_Holocene_Eruptions", f"Volcano_Number IN ({nums})")
    json.dump([f["properties"] for f in v], open(dl("gvp", "volcanoes.json"), "w"), ensure_ascii=False)
    json.dump([f["properties"] for f in e], open(dl("gvp", "eruptions.json"), "w"), ensure_ascii=False)
    print(f"{len(v)} volcanoes, {len(e)} eruptions -> {dl('gvp')}")


def load():
    if not os.path.exists(dl("gvp", "eruptions.json")):
        fetch()
    return json.load(open(dl("gvp", "volcanoes.json"))), json.load(open(dl("gvp", "eruptions.json")))


NOW = 2026
BOX = (123.3, 146.3, 22.6, 45.9)            # every volcano, Yonaguni to Shiretoko, Ogasawara to Rishiri

# years since the last confirmed eruption -> ember colour: white-hot this century, cooling to deep red
EMBER = [(0, (1.00, 0.97, 0.90)), (1.4, (1.00, 0.86, 0.55)), (2.0, (1.00, 0.62, 0.25)),
         (2.7, (1.00, 0.36, 0.14)), (3.4, (0.88, 0.14, 0.12)), (4.2, (0.55, 0.06, 0.12))]


def ember(years):
    t = np.log10(np.maximum(np.asarray(years, float), 1))
    ks = np.array([k for k, _ in EMBER]); cs = np.array([c for _, c in EMBER])
    return np.stack([np.interp(t, ks, cs[:, i]) for i in range(3)], -1)


def table():
    """One row per volcano: lon, lat, confirmed eruptions, years since the last one (None = undated)."""
    V, E = load()
    out = []
    for v in V:
        conf = [e for e in E if e["Volcano_Number"] == v["Volcano_Number"] and e["Activity_Type"] == "Confirmed Eruption"]
        last = max((e["EndDateYear"] or e["StartDateYear"] for e in conf if e["StartDateYear"] is not None), default=None)
        out.append(dict(name=v["Volcano_Name"], lon=v["Longitude"], lat=v["Latitude"], n=len(conf),
                        since=None if last is None else max(NOW - last, 0), elev=v["Elevation"], sub=v["Subregion"]))
    return out


def splat(buf, x, y, sigma, rgb, amp):
    H, W, _ = buf.shape
    r = int(np.ceil(3.2 * sigma))
    x0, x1, y0, y1 = max(int(x) - r, 0), min(int(x) + r + 1, W), max(int(y) - r, 0), min(int(y) + r + 1, H)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * sigma * sigma)) * amp
    buf[y0:y1, x0:x1] += g[..., None] * np.asarray(rgb, np.float32)


def draw_volcanoes(cv, P, z, core=1.0):
    for v in sorted(table(), key=lambda v: v["n"]):
        x, y = P(v["lon"], v["lat"])
        c = ember(v["since"] if v["since"] is not None else 20000)
        k = 0.5 + np.log1p(v["n"]) / np.log1p(172)          # 0.5 .. 1.5, Aso the brightest
        splat(cv.buf, x, y, 13 * z * k, c, 0.05 * k)          # the warm halo
        splat(cv.buf, x, y, 3.6 * z * k, c, 0.75 * k * core)  # the glowing vent
        splat(cv.buf, x, y, 1.3 * z, (1, 1, 1), 1.1 * k * core)


def land(cv, P, rgb, w):
    """Japan's land drawn faintly by its rivers (HydroRIVERS, as in rivers.py): no coastline line."""
    import rivers
    R = rivers.load()
    x, y = P(R["pts"][:, 0], R["pts"][:, 1])
    off = R["off"]
    for i in range(len(off) - 1):
        cv.add_polyline(x[off[i]:off[i + 1]], y[off[i]:off[i + 1]], rgb, w, step=0.8)


def slab(cv, P, z):
    """The earthquakes of the Earthquakes chapter, cool blue, brightest where the plate is 90-160 km down."""
    import render_views as rv
    q = rv.load()
    d = q.depth.values
    band = np.exp(-((d - 125) / 40) ** 2)
    col = np.where(d[:, None] < 125, [0.30, 0.55, 1.00], [0.55, 0.40, 1.00]) * (0.25 + 0.75 * band)[:, None]
    x, y = P(q.lon.values, q.lat.values)
    cv.add_points(x, y, col, 1.2 + 4.0 * band)


VIEWS = {
    "japan": dict(jp="日本の火山", en="Volcanoes of Japan", back="land"),
    "slab": dict(jp="沈み込む板の上", en="Above the sinking plate", back="slab"),
}


def projection(W, H):
    """North up on every screen: the Izu-Ogasawara chain hangs straight south from Tokyo, as it does.
    On a desktop screen the black sides are pixels switched off."""
    return EquiProj(W, H, *BOX, margin=0.03 if H > W else 0.04, mode="fit")


def render(name, v, W, H, out):
    phone = H > W
    P = projection(W, H)
    z = min(W, H) / 2160 if not phone else W / 1290 * 0.75
    cv = Canvas(W, H)
    if v["back"] == "land":
        land(cv, P, (0.62, 0.58, 0.55), 0.05)
    else:
        slab(cv, P, z)
    draw_volcanoes(cv, P, z)
    im = cv.finish(core=0.7, glow=6 * max(z, 0.6), glow_amt=0.4, gain=2.4, black=1.2e-2)
    t = table()
    if v["back"] == "land":
        text = f"{v['jp']}  {v['en']}  ·  {len(t)} volcanoes, colour = years since the last eruption, brightness = eruptions on record  ·  Smithsonian GVP"
    else:
        text = f"{v['jp']}  {v['en']}  ·  volcanoes over the earthquakes of the sinking plates, brightest 90 to 160 km down  ·  Smithsonian GVP, USGS"
    caption(im, text, ramp=[c for _, c in EMBER][::-1] if v["back"] == "land" else [(0.30, 0.55, 1.0), (0.55, 0.40, 1.0)])
    save(im, out)


# ---------------------------------------------------------------- eruption stripes since 1600
Y0, Y1 = 1600, NOW + 1
# the threads that stand out, named as Japan knows them (the GVP files Sakurajima under Aira, Tarumae under Shikotsu)
LABELS = {"Asosan": ("阿蘇山", "Aso"), "Asamayama": ("浅間山", "Asama"), "Izu-Oshima": ("伊豆大島", "Izu-Ōshima"),
          "Kirishimayama": ("霧島山", "Kirishima"), "Aira": ("桜島", "Sakurajima"), "Suwanosejima": ("諏訪之瀬島", "Suwanosejima"),
          "Fujisan": ("富士山", "Fuji"), "Shikotsu": ("樽前山", "Tarumae")}
VEI_RGB = [(0.70, 0.12, 0.10), (0.95, 0.30, 0.12), (1.00, 0.55, 0.20), (1.00, 0.78, 0.42), (1.00, 0.93, 0.78), (1, 1, 1)]


def stripes_rows():
    V, E = load()
    lat = {v["Volcano_Number"]: v["Latitude"] for v in V}
    name = {v["Volcano_Number"]: v["Volcano_Name"] for v in V}
    conf = [e for e in E if e["Activity_Type"] == "Confirmed Eruption" and e["StartDateYear"] is not None and e["StartDateYear"] >= Y0]
    vols = sorted({e["Volcano_Number"] for e in conf}, key=lambda n: lat[n])          # south first
    return vols, conf, name


def render_stripes(W, H, out):
    phone = H > W
    vols, conf, name = stripes_rows()
    row = {n: i for i, n in enumerate(vols)}
    cv = Canvas(W, H)
    z = min(W, H) / 2160 if not phone else W / 1290 * 0.8
    # time runs left to right on a desktop, top to bottom on a phone; volcanoes south to north
    if phone:
        a0, a1, b0, b1 = H * 0.08, H * 0.86, W * 0.08, W * 0.92
    else:
        a0, a1, b0, b1 = W * 0.06, W * 0.86, H * 0.90, H * 0.08
    def at(year, i):
        t = a0 + (year - Y0) / (Y1 - Y0) * (a1 - a0)
        r = b0 + (i + 0.5) / len(vols) * (b1 - b0)
        return (r, t) if phone else (t, r)
    for i in range(len(vols)):                                   # each volcano's thread, faint
        (x0, y0), (x1, y1) = at(Y0, i), at(Y1, i)
        cv.add_polyline(np.array([x0, x1]), np.array([y0, y1]), (0.55, 0.20, 0.16), 0.035, step=1.0)
    for e in sorted(conf, key=lambda e: e["ExplosivityIndexMax"] or 0):
        i = row[e["Volcano_Number"]]
        s = e["StartDateYear"] + ((e["StartDateMonth"] or 1) - 1) / 12
        end = e["EndDateYear"]
        f = (end + ((e["EndDateMonth"] or 12) - 0.5) / 12) if end is not None else s + 0.4
        f = max(f, s + 0.4)
        vei = e["ExplosivityIndexMax"]
        k = 1 if vei is None else int(vei)
        c = VEI_RGB[min(k, len(VEI_RGB) - 1)]
        (x0, y0), (x1, y1) = at(s, i), at(f, i)
        cv.add_polyline(np.array([x0, x1]), np.array([y0, y1]), c, 0.8 + 0.3 * k, step=0.6)
        xm, ym = at(s, i)
        splat(cv.buf, xm, ym, (2.4 + 0.8 * k) * z, c, 0.08 + 0.045 * k)       # the burst at its start
    im = cv.finish(core=0.8, glow=5 * max(z, 0.6), glow_amt=0.35, gain=2.2, black=1.2e-2)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F_LIGHT, int(20 * z))
    for n, (jp, en) in (LABELS.items() if not phone else []):    # 61 phone columns are too narrow to name
        hit = [v for v in vols if name[v] == n]
        if not hit:
            continue
        x, y = at(Y1, row[hit[0]])
        if phone:
            d.text((x, y + 14 * z), jp, font=f, fill=(120, 110, 104), anchor="mt")
        else:
            d.text((x + 18 * z, y), f"{jp}  {en}", font=f, fill=(120, 110, 104), anchor="lm")
    ticks = [1600, 1700, 1800, 1900, 2000]
    for yr in ticks:
        x, y = at(yr, -1.6) if not phone else at(yr, -1.2)
        d.text((x, y), str(yr), font=f, fill=(85, 85, 85), anchor="mm" if not phone else "rm")
    caption(im, f"噴火の縞  Eruption stripes  ·  {len(conf)} eruptions at {len(vols)} volcanoes since 1600, south at the "
                f"{'left' if phone else 'bottom'}, brighter for larger eruptions (VEI)  ·  Smithsonian GVP", ramp=VEI_RGB)
    save(im, out)


def land_backdrop(W, H, path):
    """The faint land alone, for the eruption animation to draw over (same frame as the wallpapers)."""
    P = projection(W, H)
    cv = Canvas(W, H)
    land(cv, P, (0.62, 0.58, 0.55), 0.09)
    cv.finish(core=0.6, glow=3, glow_amt=0.3, gain=2.4, black=1.2e-2).save(path, quality=80)


if __name__ == "__main__" and "--info" in sys.argv:
    V, E = load()
    import collections
    print(len(V), "volcanoes;", len(E), "eruptions")
    print("subregions:", collections.Counter(v["Subregion"] for v in V).most_common())
    print("activity types:", collections.Counter(e["Activity_Type"] for e in E).most_common())
    ys = np.array([e["StartDateYear"] for e in E if e["StartDateYear"] is not None])
    print("start years:", ys.min(), "..", ys.max(), " since 1600:", (ys >= 1600).sum(), " since 1900:", (ys >= 1900).sum())
    vei = collections.Counter(e["ExplosivityIndexMax"] for e in E)
    print("VEI:", sorted(vei.items(), key=lambda kv: (kv[0] is None, kv[0])))
    lon = np.array([v["Longitude"] for v in V]); lat = np.array([v["Latitude"] for v in V])
    print("box:", lon.min(), lon.max(), lat.min(), lat.max())
    far = [(v["Volcano_Name"], v["Longitude"], v["Latitude"]) for v in V if v["Longitude"] > 145.3 or v["Latitude"] < 30]
    print("east of 145.3E or south of 30N:", far)


if __name__ == "__main__" and "--info" not in sys.argv:
    for n in [a for a in sys.argv[1:] if not a.startswith("--")] or list(VIEWS) + ["stripes"]:
        if n == "stripes":
            render_stripes(*DESKTOP, "out/volcanoes_stripes_desktop.png")
            render_stripes(*PHONE, "out/volcanoes_stripes_phone.png")
            continue
        render(n, VIEWS[n], *DESKTOP, f"out/volcanoes_{n}_desktop.png")
        render(n, VIEWS[n], *PHONE, f"out/volcanoes_{n}_phone.png")
