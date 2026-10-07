"""Every railway line in Japan, in its official line colour, plus every station.

Data: 国土数値情報 鉄道データ via the R package jprailway (github.com/paithiov909/jprailway):
polylines.rda (track geometry per line section), lines.rda (line metadata incl. official
colour, closed flag), stations.rda (11,439 stations).
Shinkansen are drawn white. Lines without an official colour get a dim warm white.
Closed lines are skipped.
"""
import sys, warnings
import numpy as np, rdata
from common import Canvas, caption, save, EquiProj, dl, DESKTOP, PHONE

warnings.filterwarnings("ignore")
D = dl("jprailway", "data") + "/"


def rd(name):
    return list(rdata.conversion.convert(rdata.parser.parse_file(D + name + ".rda"),
                                         default_encoding="utf8").values())[0]


poly, lines, stations = rd("polylines"), rd("lines"), rd("stations")
meta = lines.set_index(lines.code.astype(int))
open_codes = set(meta.index[~meta.closed.astype(bool)])


def hex2rgb(h):
    h = str(h)
    if not h.startswith("#") or len(h) != 7:
        return None
    return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])


def line_color(code):
    if 1000 <= code < 1100:                       # Shinkansen
        return np.array([1.0, 1.0, 1.0]), 2.2
    c = hex2rgb(meta.color.get(code)) if code in meta.index else None
    if c is None:
        return np.array([0.75, 0.68, 0.58]), 0.55   # no official colour: dim warm white
    c = 0.15 + 0.85 * c                            # lift very dark official colours a bit
    return c, 1.0


SEGS = []
for code, g in zip(poly.code.astype(int), poly.geometry):
    if code in open_codes and isinstance(g, np.ndarray) and g.ndim == 2 and len(g) > 1:
        col, w = line_color(code)
        SEGS.append((g, col, w, 1000 <= code < 1100))
SEGS.sort(key=lambda s: s[3])                     # Shinkansen last (on top; additive anyway)

_st = stations[~stations.closed.astype(bool)]
ST = np.stack([_st.lng.astype(float).values, _st.lat.astype(float).values], 1)

class RotProj:
    """Whole country: rotate so the main islands run along the long side (like Fault Light)."""
    def __init__(self, W, H):
        self.W, self.H, self.lon0, self.lat0 = W, H, 137.0, 36.0
        self.k = np.cos(np.radians(self.lat0))
        pts = np.concatenate([g[::20] for g, *_ in SEGS])
        u, v = (pts[:, 0] - self.lon0) * self.k, pts[:, 1] - self.lat0
        evec = np.linalg.eigh(np.cov(np.stack([u, v])))[1][:, -1]
        phi = np.arctan2(evec[1], evec[0]); phi += np.pi if np.cos(phi) < 0 else 0
        self.th = -phi if W >= H else np.pi / 2 - phi
        ur, vr = self._rot(u, v)
        lu, hu = np.percentile(ur, [0.3, 99.7]); lv, hv = np.percentile(vr, [0.3, 99.7])
        res = 0.05 * H if H > W else 0.0
        self.s = min(W * 0.97 / (hu - lu), (H - res) * 0.95 / (hv - lv))
        self.uc, self.vc, self.res = (lu + hu) / 2, (lv + hv) / 2, res

    def _rot(self, u, v):
        c, s = np.cos(self.th), np.sin(self.th)
        return c * u - s * v, s * u + c * v

    def __call__(self, lon, lat):
        u, v = self._rot((np.asarray(lon) - self.lon0) * self.k, np.asarray(lat) - self.lat0)
        return self.W / 2 + (u - self.uc) * self.s, (self.H - self.res) / 2 - (v - self.vc) * self.s


VIEWS = {
    "japan": dict(jp="日本の鉄道", en="Railways of Japan", rotate=True, w=1.0, st=0.0),
    "tokyo": dict(jp="東京の鉄道", en="Railways of Tokyo", desk=(139.50, 139.98, 35.56, 35.80),
                  phone=(139.60, 139.86, 35.52, 35.84), w=3.2, st=1.2),
    "kansai": dict(jp="関西の鉄道", en="Railways of Osaka, Kyoto & Kobe", desk=(135.10, 135.85, 34.55, 35.05),
                   phone=(135.38, 135.80, 34.55, 35.06), w=3.0, st=1.2),
}


def render(name, v, W, H, out):
    phone = H > W
    P = RotProj(W, H) if v.get("rotate") else EquiProj(W, H, *(v["phone"] if phone else v["desk"]), margin=0.0, mode="fill")
    cv = Canvas(W, H)
    z = min(W, H) / 2160
    for g, col, w, shink in SEGS:
        x, y = P(g[:, 0], g[:, 1])
        if x.max() < -50 or x.min() > W + 50 or y.max() < -50 or y.min() > H + 50:
            continue
        cv.add_polyline(x, y, col, 0.16 * w * v["w"] * (1.3 if phone else 1), step=0.5)
    if v["st"]:
        sx, sy = P(ST[:, 0], ST[:, 1])
        cv.add_points(sx, sy, (1.0, 1.0, 1.0), 0.9 * v["st"])
    im = cv.finish(core=0.55 * max(1, z), glow=5 * z, glow_amt=0.35, gain=2.6, black=1.5e-2)
    n = len({c for c in poly.code.astype(int) if c in open_codes})
    caption(im, f"{v['jp']}  {v['en']}  ·  {n} lines in their official colours, Shinkansen in white  ·  "
                f"国土数値情報", ramp=[(0.0, 0.7, 0.38), (1.0, 0.55, 0.0), (0.9, 0.2, 0.3), (0.1, 0.5, 0.9), (1, 1, 1)])
    save(im, out)


if __name__ == "__main__":
    names = sys.argv[1:] or list(VIEWS)
    print(len(SEGS), "line sections,", len(ST), "stations")
    for n in names:
        render(n, VIEWS[n], *DESKTOP, f"out/trains_{n}_desktop.png")
        render(n, VIEWS[n], *PHONE, f"out/trains_{n}_phone.png")
