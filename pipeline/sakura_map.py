"""Cherry blossom map of Japan: one glowing blossom per JMA observation city.

Pink intensity = how much earlier that city's first bloom now comes than in the 1950s:
the robust (Theil-Sen) trend of first-bloom day against year, 1953-2018, in days per decade.
Pale = no change, vivid pink = 3+ days earlier per decade. Faint coastline for orientation.

Data: JMA sakura first-bloom dates (github.com/akg314/sakura), Natural Earth 10 m land.
Desktop: rotated so the archipelago runs along the screen (north arrow). Phone: north up.
"""
import json
import numpy as np, pandas as pd
from scipy.stats import theilslopes
from PIL import ImageDraw, ImageFont
from common import Canvas, caption, save, DESKTOP, PHONE, F_LIGHT, flower_sprite, add_sprite, dl

D = dl("sakura", "data") + "/"
fl = pd.read_csv(D + "flowering.csv")
fl = fl[fl.day.astype(str).str.isdigit()].copy()
fl["day"] = fl.day.astype(int)
fl["doy"] = pd.to_datetime(dict(year=2001, month=fl.day // 100, day=fl.day % 100), errors="coerce").dt.dayofyear
fl = fl.dropna(subset=["doy"])
loc = pd.read_csv(D + "locations.csv")
# four stations were geocoded to namesakes abroad in the source file; use the JMA station sites
FIX = {597: (140.21, 37.13),   # 白河 Shirakawa, Fukushima
       612: (138.25, 37.10),   # 高田 Takada (Jōetsu), Niigata
       651: (136.52, 34.73),   # 津 Tsu, Mie
       741: (133.07, 35.46)}   # 松江 Matsue, Shimane
for code, (lo, la) in FIX.items():
    loc.loc[loc.l_code == code, ["lon", "lat"]] = lo, la

rows = []
for code, g in fl.groupby("l_code"):
    if len(g) < 30:
        continue
    slope = theilslopes(g.doy.values, g.year.values)[0] * 10        # days per decade
    rows.append((code, slope))
T = pd.DataFrame(rows, columns=["l_code", "slope"]).merge(loc, on="l_code")
print(len(T), "cities, median trend", round(T.slope.median(), 2), "days/decade,",
      round((T.slope < 0).mean() * 100), "% earlier")

# coastline rings near Japan
coast = []
for f in json.load(open(dl("ne", "land10.geojson")))["features"]:
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for poly in polys:
        for ring in poly:
            r = np.asarray(ring)
            if r[:, 0].max() > 122 and r[:, 0].min() < 147.5 and r[:, 1].max() > 23.5 and r[:, 1].min() < 46.5:
                coast.append(r)

PALE, VIVID = np.array([0.95, 0.92, 0.96]), np.array([1.0, 0.10, 0.50])
RAMP = [PALE, (PALE + VIVID) / 2, VIVID]


def pink(slope):
    t = np.clip(-slope / 1.5, 0, 1) ** 0.9           # 0 = no change, 1 = 1.5+ days earlier per decade
    return PALE * (1 - t[:, None]) + VIVID * t[:, None], t


class Proj:
    def __init__(self, W, H, rotate):
        self.W, self.H, self.lon0, self.lat0 = W, H, 136.5, 35.5
        self.k = np.cos(np.radians(self.lat0))
        u, v = (T.lon.values - self.lon0) * self.k, T.lat.values - self.lat0
        self.th = 0.0
        if rotate:
            evec = np.linalg.eigh(np.cov(np.stack([u, v])))[1][:, -1]
            phi = np.arctan2(evec[1], evec[0]); phi += np.pi if np.cos(phi) < 0 else 0
            self.th = -phi
        ur, vr = self._rot(u, v)
        mx, my = (0.05, 0.12) if rotate else (0.08, 0.06)
        q = 0 if rotate else 2.5                      # phone: let the far southern islands fall near the edge
        u0, u1 = np.percentile(ur, [q, 100 - q]); v0, v1 = np.percentile(vr, [q, 100])
        self.s = min(W * (1 - 2 * mx) / (u1 - u0), (H * (1 - 2 * my) - (0 if rotate else 0.05 * H)) / (v1 - v0))
        self.uc, self.vc = (u0 + u1) / 2, (v0 + v1) / 2
        self.yoff = 0 if rotate else -0.025 * H

    def _rot(self, u, v):
        c, s = np.cos(self.th), np.sin(self.th)
        return c * u - s * v, s * u + c * v

    def __call__(self, lon, lat):
        u, v = self._rot((np.asarray(lon) - self.lon0) * self.k, np.asarray(lat) - self.lat0)
        return self.W / 2 + (u - self.uc) * self.s, self.H / 2 + self.yoff - (v - self.vc) * self.s


def render(W, H, out):
    phone = H > W
    P = Proj(W, H, rotate=not phone)
    cv = Canvas(W, H)
    z = min(W, H) / 2160 * (1.5 if phone else 1)
    for r in coast:                                   # the faintest outline of the islands
        x, y = P(r[:, 0], r[:, 1])
        if x.max() < 0 or x.min() > W or y.max() < 0 or y.min() > H:
            continue
        cv.add_polyline(x, y, (0.60, 0.34, 0.46), 0.09 * (1.3 if phone else 1), step=0.7)
    col, t = pink(T.slope.values)
    x, y = P(T.lon.values, T.lat.values)
    rng = np.random.default_rng(3)
    sprites = [flower_sprite(r, rot) for r in (17 * z, 22 * z) for rot in np.linspace(0, 1.25, 4)]
    for i in np.argsort(t):                           # most vivid drawn last
        spr = sprites[(1 if t[i] > 0.5 else 0) * 4 + rng.integers(4)]
        add_sprite(cv, x[i], y[i], spr, col[i], 0.55 + 0.75 * t[i])
    im = cv.finish(core=0.7 * max(1, z), glow=9 * z, glow_amt=0.55, gain=2.4, gamma=0.85, black=1.2e-2)

    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F_LIGHT, int(19 * z))
    for city in ["NAHA", "KAGOSHIMA", "KYOTO", "TOKYO", "SENDAI", "SAPPORO"]:
        r = T[T.romaji == city]
        if len(r):
            cx, cy = P(r.lon.iloc[0], r.lat.iloc[0])
            d.text((cx + 20 * z, cy - 20 * z), city.title(), font=f, fill=(120, 100, 110), anchor="ls")
    if P.th:                                          # north arrow, bottom right
        a = P.th + np.pi / 2; dx, dy = np.cos(a), -np.sin(a)
        cx, cy, L = W - 70 * z, H - 70 * z, 22 * z
        d.line([(cx - dx * L, cy - dy * L), (cx + dx * L, cy + dy * L)], fill=(100, 90, 95), width=max(1, int(1.5 * z)))
        d.text((cx + dx * (L + 14 * z), cy + dy * (L + 14 * z)), "N", font=f, fill=(100, 90, 95), anchor="mm")
    caption(im, f"桜  Cherry blossom map of Japan  ·  {len(T)} JMA cities  ·  deeper pink = first bloom earlier than in the 1950s "
                f"(up to 1.5 days per decade)  ·  {int((T.slope < 0).mean() * 100)}% of cities now bloom earlier", ramp=RAMP)
    save(im, out)


if __name__ == "__main__":
    render(*DESKTOP, "out/sakura_map_desktop.png")
    render(*PHONE, "out/sakura_map_phone.png")
