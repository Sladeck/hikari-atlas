"""Blackbody-style OLED wallpapers: earthquakes of Japan, by region.

Data: USGS ComCat, M4.5+, 1973 to today, box 121-150°E / 23-47°N
(the three query*.csv files in ./usgs).

Each quake is splatted as a soft additive glow on a pure #000000 canvas:
  size  ~ magnitude
  color ~ depth (amber shallow -> crimson -> violet -> blue at ~650 km)
M7+ quakes get faint concentric "seismic wave" rings.

usage: python render_views.py [view ...]     (no args = all views)
writes out/<view>_desktop.png (3840x2160) and out/<view>_phone.png (1290x2796)
"""
import sys, glob, os, json
import numpy as np, pandas as pd
from PIL import Image, ImageDraw, ImageFont

OUT = "out"
from common import DESKTOP, PHONE, F_LIGHT, F_REG
DATA_CLIP = (121, 150, 23, 47)  # lon0, lon1, lat0, lat1 of the USGS query box

# ------------------------------------------------------------------ views
# center (lon, lat) and "span": degrees of latitude that must fit the short side.
# cities: little reference marks so you know where you are.
VIEWS = {
    "japan":    dict(jp="日本", en="Japan", center=(137.0, 35.5), span=20.5, cities=[], orient="auto"),
    "tohoku":   dict(jp="東北", en="Tōhoku", center=(141.9, 38.4), span=6.6,
                     cities=[("Sendai", 140.87, 38.27), ("Morioka", 141.15, 39.70), ("Fukushima", 140.47, 37.75)]),
    "tokyo":    dict(jp="東京・関東", en="Tokyo & Kantō", center=(140.4, 35.7), span=4.4,
                     cities=[("Tokyo", 139.69, 35.69), ("Yokohama", 139.64, 35.44), ("Chiba", 140.12, 35.61)]),
    "kurils":   dict(jp="北海道・千島", en="Hokkaido & Kurils", center=(145.0, 43.5), span=8, radius=5.5,
                     orient="auto", cities=[("Sapporo", 141.35, 43.06), ("Kushiro", 144.38, 42.98)]),
    "izu":      dict(jp="伊豆・小笠原", en="Izu–Bonin Trench", center=(141.2, 29.5), span=12, radius=6.5,
                     orient="auto", cities=[("Hachijōjima", 139.79, 33.11), ("Chichijima", 142.19, 27.09)]),
    "ryukyu":   dict(jp="琉球", en="Ryūkyū Arc", center=(127.2, 27.2), span=8, radius=5.5,
                     orient="auto", cities=[("Naha", 127.68, 26.21), ("Kagoshima", 130.56, 31.60), ("Ishigaki", 124.16, 24.34)]),
    "west":     dict(jp="西日本", en="Western & Central Japan", center=(134.6, 34.4), span=7.6,
                     cities=[("Osaka", 135.50, 34.69), ("Hiroshima", 132.46, 34.39), ("Fukuoka", 130.40, 33.59),
                             ("Nagoya", 136.91, 35.18), ("Kanazawa", 136.65, 36.56), ("Kumamoto", 130.71, 32.80)]),
}


# depth (km) -> color
RAMP = [(0, (1.00, 0.86, 0.62)), (60, (1.00, 0.45, 0.18)), (150, (0.90, 0.16, 0.30)),
        (350, (0.55, 0.20, 0.85)), (650, (0.25, 0.35, 1.00))]


def depth_color(d):
    ks = np.array([k for k, _ in RAMP]); cs = np.array([c for _, c in RAMP])
    return np.stack([np.interp(d, ks, cs[:, i]) for i in range(3)], -1)


# ------------------------------------------------------------------ data
def load():
    d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("usgs/*.csv"))]).drop_duplicates("id")
    d = d[d["type"] == "earthquake"]
    df = pd.DataFrame({"lon": d.longitude, "lat": d.latitude, "mag": d.mag, "depth": d.depth,
                       "time": pd.to_datetime(d.time, format="ISO8601"), "place": d.place})
    return df.dropna(subset=["lon", "lat", "mag", "depth"]).sort_values("mag").reset_index(drop=True)


# ------------------------------------------------------------------ geometry
class Proj:
    """Equirectangular (longitude scaled by cos(lat) at the view center), optionally rotated.

    orient="auto": find the main axis of the quakes with PCA and rotate so it runs
    along the long side of the canvas (horizontal on desktop, vertical on phone),
    then zoom to fit the data. Otherwise north-up around `center`, `span` deg tall.
    """
    def __init__(self, view, W, H, df=None):
        lon0, lat0 = view["center"]
        self.k = np.cos(np.radians(lat0))
        self.lon0, self.lat0, self.W, self.H = lon0, lat0, W, H
        self.theta, self.uc, self.vc, self.reserve = 0.0, 0.0, 0.0, 0.0
        self.s = min(W, H) / view["span"]          # pixels per degree of latitude
        if view.get("orient") == "auto":
            u, v = self._local(df.lon.values, df.lat.values)
            if "radius" in view:
                keep = np.hypot(u, v) < view["radius"]; u, v = u[keep], v[keep]
            ev, evec = np.linalg.eigh(np.cov(np.stack([u, v])))
            phi = np.arctan2(evec[1, -1], evec[0, -1])             # main axis angle
            if np.cos(phi) < 0: phi += np.pi                        # point it towards the NE
            self.theta = -phi if W >= H else np.pi / 2 - phi        # along the long side
            ur, vr = self._rot(u, v)
            lo_u, hi_u = np.percentile(ur, [1.5, 98.5]); lo_v, hi_v = np.percentile(vr, [1.5, 98.5])
            mx, my = view.get("margin", (0.01, 0.03))
            self.reserve = 0.07 * H if H > W else 0.0            # keep the phone caption clear
            self.s = min(W * (1 - 2 * mx) / (hi_u - lo_u), (H - self.reserve) * (1 - 2 * my) / (hi_v - lo_v))
            self.uc, self.vc = (lo_u + hi_u) / 2, (lo_v + hi_v) / 2

    def _local(self, lon, lat):
        return (lon - self.lon0) * self.k, lat - self.lat0

    def _rot(self, u, v):
        c, s = np.cos(self.theta), np.sin(self.theta)
        return c * u - s * v, s * u + c * v

    def __call__(self, lon, lat):
        u, v = self._rot(*self._local(lon, lat))
        return self.W / 2 + (u - self.uc) * self.s, (self.H - self.reserve) / 2 - (v - self.vc) * self.s


def splat(buf, x, y, sigma, rgb, amp):
    H, W, _ = buf.shape
    r = int(np.ceil(3.2 * sigma))
    x0, x1, y0, y1 = max(int(x) - r, 0), min(int(x) + r + 1, W), max(int(y) - r, 0), min(int(y) + r + 1, H)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * sigma * sigma)) * amp
    buf[y0:y1, x0:x1] += g[..., None] * rgb


def ring(buf, x, y, radius, width, rgb, amp):
    H, W, _ = buf.shape
    r = int(radius + 4 * width)
    x0, x1, y0, y1 = max(int(x) - r, 0), min(int(x) + r + 1, W), max(int(y) - r, 0), min(int(y) + r + 1, H)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    g = np.exp(-((np.hypot(xx - x, yy - y) - radius) / width) ** 2) * amp
    buf[y0:y1, x0:x1] += g[..., None] * rgb


# ------------------------------------------------------------------ render
def render(df, name, view, W, H, phone):
    P = Proj(view, W, H, df[(df.mag >= 5.0)])
    X, Y = P(df.lon.values, df.lat.values)
    pad = 0.05 * max(W, H)
    vis = (X > -pad) & (X < W + pad) & (Y > -pad) & (Y < H + pad)
    d, X, Y = df[vis], X[vis], Y[vis]

    # zoom relative to the national desktop view: dots grow, but slower than the map
    z = min(P.s, 2.2 * min(W, H) / 23.0) / (min(W, H) / 23.0)
    size = z ** 0.72 * (1.0 if not phone else 0.80)
    gain = z ** 0.55

    # fade near the edge of the downloaded box so it dissolves instead of cutting
    e = np.minimum.reduce([d.lon.values - DATA_CLIP[0], DATA_CLIP[1] - d.lon.values,
                           d.lat.values - DATA_CLIP[2], DATA_CLIP[3] - d.lat.values])
    t = np.clip(e / 1.5, 0, 1); fade = t * t * (3 - 2 * t)

    buf = np.zeros((H, W, 3), np.float32)
    for x, y, m, c, f in zip(X, Y, d.mag.values, depth_color(d.depth.values), fade):
        dm = m - 4.5
        sigma = max(0.8, 1.15 * size * 1.38 ** dm)
        splat(buf, x, y, sigma * 3.0, c, f * gain * 0.016 * 1.25 ** dm)   # halo
        splat(buf, x, y, sigma, c, f * gain * 0.13 * 1.30 ** dm)          # core

    for x, y, m, c, f in zip(X, Y, d.mag.values, depth_color(d.depth.values), fade):
        if m < 7.0:
            continue
        R = 9 * size * 1.9 ** (m - 7)
        for i in range(4):
            ring(buf, x, y, R * (1 + 0.85 * i), max(0.8, 1.0 * size ** 0.5),
                 c, f * 0.09 * 0.6 ** i * 1.4 ** (m - 7))

    img = np.clip(1.0 - np.exp(-buf * 2.6), 0, 1) ** 0.85   # tone map: 0 stays 0
    arr = (img * 255 + 0.5).astype(np.uint8)
    arr[buf.max(-1) < 1e-3] = 0                              # guaranteed #000000
    im = Image.fromarray(arr)
    draw_cities(im, P, view, W, H, phone)
    if P.theta:
        north_arrow(im, P, W, H, phone)
    stats = caption(im, d[fade > 0.5], view, W, H, phone)
    os.makedirs(OUT, exist_ok=True)
    kind = "phone" if phone else "desktop"
    im.save(f"{OUT}/{name}_{kind}.png", optimize=True)
    black = float((arr.max(-1) == 0).mean())
    print(f"{name:9s} {kind:7s} {len(d):6d} quakes  black={black:.1%}")
    return stats


def draw_cities(im, P, view, W, H, phone):
    d = ImageDraw.Draw(im)
    u = min(W, H) / 2160 * (1.6 if phone else 1)
    f = ImageFont.truetype(F_LIGHT, int(22 * u))
    for name, lon, lat in view["cities"]:
        x, y = P(lon, lat)
        r = 5 * u
        d.ellipse([x - r, y - r, x + r, y + r], outline=(120, 120, 120), width=max(1, int(1.4 * u)))
        d.text((x + 11 * u, y - 15 * u), name, font=f, fill=(115, 115, 115))


def north_arrow(im, P, W, H, phone):
    """Small rotated arrow pointing to geographic north, bottom-right corner."""
    d = ImageDraw.Draw(im)
    u = min(W, H) / 2160 * (1.6 if phone else 1)
    cx, cy = W - (W * (0.06 if phone else 0.025)) - 20 * u, H - (150 * u / 1.6 * 0.9 * 1.6 if phone else 60 * u)
    a = P.theta + np.pi / 2                       # north direction on screen (y down)
    dx, dy = np.cos(a), -np.sin(a)
    L = 22 * u
    tip, tail = (cx + dx * L, cy + dy * L), (cx - dx * L, cy - dy * L)
    d.line([tail, tip], fill=(90, 90, 90), width=max(1, int(1.5 * u)))
    px, py = -dy, dx
    h = 7 * u
    d.polygon([tip, (tip[0] - dx * h * 1.6 + px * h, tip[1] - dy * h * 1.6 + py * h),
               (tip[0] - dx * h * 1.6 - px * h, tip[1] - dy * h * 1.6 - py * h)], fill=(90, 90, 90))
    f = ImageFont.truetype(F_LIGHT, int(17 * u))
    d.text((tip[0] + dx * 14 * u, tip[1] + dy * 14 * u), "N", font=f, fill=(90, 90, 90), anchor="mm")


def caption(im, d, view, W, H, phone):
    """One small, dim line in the corner + a thin depth bar. The data is the picture."""
    draw = ImageDraw.Draw(im)
    u = H / 2160 if not phone else W / 1290 * 0.9
    f = ImageFont.truetype(F_LIGHT, int(17 * u))
    big = d.loc[d.mag.idxmax()]
    stats = dict(count=int(len(d)), y0=int(d.time.min().year), y1=int(d.time.max().year),
                 maxmag=float(big.mag), maxdate=big.time.strftime("%Y-%m-%d"),
                 maxdepth=round(float(big.depth)), maxplace=str(big.place),
                 deepest=round(float(d.depth.max())))
    text = f"{view['jp']}  {view['en']}  ·  {stats['count']:,} quakes M4.5+  ·  {stats['y0']}–{stats['y1']}  ·  USGS"
    x = int(W * (0.06 if phone else 0.025))
    y = int(H - (150 * u if phone else 60 * u))
    lw, lh = int(70 * u), max(2, int(3 * u))
    for i in range(lw):                                    # depth bar, shallow -> deep
        c = depth_color(np.array([i / lw * 650]))[0] * 0.6
        draw.line([(x + i, y), (x + i, y + lh)], fill=tuple(int(v * 255) for v in c))
    draw.text((x + lw + 12 * u, y + lh / 2), text, font=f, fill=(85, 85, 85), anchor="lm")
    return stats


if __name__ == "__main__":
    df = load()
    names = sys.argv[1:] or list(VIEWS)
    meta = {}
    if os.path.exists(f"{OUT}/views.json"):
        meta = json.load(open(f"{OUT}/views.json"))
    for n in names:
        v = VIEWS[n]
        st = render(df, n, v, *DESKTOP, phone=False)
        render(df, n, v, *PHONE, phone=True)
        meta[n] = dict(jp=v["jp"], en=v["en"], **st)
    json.dump(meta, open(f"{OUT}/views.json", "w"), indent=1, ensure_ascii=False)
