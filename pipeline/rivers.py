"""Rivers of Japan as light: every river reach in HydroRIVERS, as bright as the water it carries.

Data: HydroRIVERS v1.0, Asia (Lehner & Grill 2013), dl/hydrorivers/raw/. Each reach has its
long-term average discharge (DIS_AV_CMS, m3/s), the reach it flows into (NEXT_DOWN, 0 at the sea),
and the outlet reach of its whole river system (MAIN_RIV), which names the basin.
Only reaches on Japan's land are kept: Natural Earth 10 m land polygons inside Japan's box, minus
the continent, Sakhalin, Jeju and Taiwan. The first run caches them in dl/hydrorivers/japan.npz.

    python rivers.py              # every view, desktop and phone, into out/
    python rivers.py japan kanto  # some of them
    python rivers.py --info       # what the cache holds
"""
import os
import sys
import json
import colorsys
import numpy as np
from PIL import Image, ImageDraw
from common import Canvas, caption, save, EquiProj, dl, DESKTOP, PHONE

SHP = dl("hydrorivers", "raw", "HydroRIVERS_v10_as_shp", "HydroRIVERS_v10_as")
CACHE = dl("hydrorivers", "japan.npz")
BOX = (122.5, 146.2, 24.0, 45.8)          # lon0, lon1, lat0, lat1


def japan_polygons():
    """Natural Earth land rings that belong to Japan (outer rings only)."""
    g = json.load(open(dl("ne", "land10.geojson")))
    out = []
    for f in g["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for p in polys:
            ring = np.asarray(p[0], float)
            lo, la = ring[:, 0], ring[:, 1]
            cx, cy = lo.mean(), la.mean()
            if not (BOX[0] < cx < BOX[1] and BOX[2] < cy < BOX[3]):
                continue
            if lo.max() - lo.min() > 12:                     # the Asian continent
                continue
            if cy > 45.9 or (cx > 141.5 and cy > 46):        # Sakhalin
                continue
            if cx < 128.2 and cy > 32.8:                     # Jeju and the Korean islands
                continue
            if cx < 122.9:                                   # Taiwan and its islets
                continue
            out.append(ring)
    return out


def japan_mask(res=0.01):
    """Raster of Japan's land at `res` degrees: (mask, lookup(lon, lat) -> bool)."""
    W = int((BOX[1] - BOX[0]) / res) + 1
    H = int((BOX[3] - BOX[2]) / res) + 1
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    for ring in japan_polygons():
        xy = [((lo - BOX[0]) / res, (BOX[3] - la) / res) for lo, la in ring]
        d.polygon(xy, fill=1)
    m = np.asarray(im, bool)
    # a reach can end a little past the coarse coastline: grow the land by two cells (~2 km)
    from scipy.ndimage import binary_dilation
    m = binary_dilation(m, iterations=2)

    def inside(lon, lat):
        i = np.clip(((BOX[3] - np.asarray(lat)) / res).astype(int), 0, H - 1)
        j = np.clip(((np.asarray(lon) - BOX[0]) / res).astype(int), 0, W - 1)
        return m[i, j]
    return m, inside


def extract():
    import shapefile
    _, inside = japan_mask()
    r = shapefile.Reader(SHP)
    names = [f[0] for f in r.fields[1:]]
    col = {n: names.index(n) for n in ("HYRIV_ID", "NEXT_DOWN", "MAIN_RIV", "DIS_AV_CMS", "ORD_STRA",
                                       "DIST_DN_KM", "UPLAND_SKM", "LENGTH_KM")}
    keep, pts, off = [], [], [0]
    for i, sh in enumerate(r.iterShapes()):
        b = sh.bbox
        if b[2] < BOX[0] or b[0] > BOX[1] or b[3] < BOX[2] or b[1] > BOX[3]:
            continue
        p = np.asarray(sh.points, np.float32)
        mid = p[len(p) // 2]
        if not inside(mid[0], mid[1]):
            continue
        keep.append(i); pts.append(p); off.append(off[-1] + len(p))
    recs = [r.record(i) for i in keep]
    a = {n: np.array([rec[c] for rec in recs]) for n, c in col.items()}
    np.savez_compressed(CACHE, pts=np.concatenate(pts), off=np.asarray(off, np.int64), **a)
    print(f"{len(keep)} reaches on Japan's land -> {CACHE}")


def load():
    if not os.path.exists(CACHE):
        extract()
    z = np.load(CACHE)
    return {k: z[k] for k in z.files}


class RotProj:
    """Whole country, rotated so the islands run along the long side of the screen (as trains.py)."""
    def __init__(self, W, H, pts):
        self.W, self.H, self.lon0, self.lat0 = W, H, 137.0, 36.0
        self.k = np.cos(np.radians(self.lat0))
        u, v = (pts[:, 0] - self.lon0) * self.k, pts[:, 1] - self.lat0
        evec = np.linalg.eigh(np.cov(np.stack([u, v])))[1][:, -1]
        phi = np.arctan2(evec[1], evec[0]); phi += np.pi if np.cos(phi) < 0 else 0
        self.th = -phi if W >= H else np.pi / 2 - phi
        ur, vr = self._rot(u, v)
        lu, hu = np.percentile(ur, [0.05, 99.95]); lv, hv = np.percentile(vr, [0.05, 99.95])
        res = 0.05 * H if H > W else 0.0
        self.s = min(W * 0.97 / (hu - lu), (H - res) * 0.95 / (hv - lv))
        self.uc, self.vc, self.res = (lu + hu) / 2, (lv + hv) / 2, res

    def _rot(self, u, v):
        c, s = np.cos(self.th), np.sin(self.th)
        return c * u - s * v, s * u + c * v

    def __call__(self, lon, lat):
        u, v = self._rot((np.asarray(lon) - self.lon0) * self.k, np.asarray(lat) - self.lat0)
        return self.W / 2 + (u - self.uc) * self.s, (self.H - self.res) / 2 - (v - self.vc) * self.s


# flow: indigo trickles, blue streams, ice-white great rivers (log discharge 0.1 .. 400 m3/s)
FLOW = np.array([(0.22, 0.26, 0.85), (0.25, 0.52, 1.00), (0.55, 0.78, 1.00), (0.86, 0.94, 1.00), (1, 1, 1)], np.float32)


def flow_rgb(q):
    t = np.clip((np.log10(np.maximum(q, 0.1)) + 1) / (np.log10(400) + 1), 0, 1) * (len(FLOW) - 1)
    i = np.minimum(t.astype(int), len(FLOW) - 2)
    f = (t - i)[..., None]
    return FLOW[i] * (1 - f) + FLOW[i + 1] * f


def basin_rgb(R):
    """One colour per river system: the largest systems take the most distant hues first."""
    main, inv = np.unique(R["MAIN_RIV"], return_inverse=True)
    size = np.bincount(inv, weights=R["LENGTH_KM"])
    rank = np.empty(len(main), int); rank[np.argsort(-size)] = np.arange(len(main))
    hue = (0.58 + rank * 0.61803398875) % 1.0
    pal = np.array([colorsys.hsv_to_rgb(h, 0.62, 1.0) for h in hue], np.float32)
    return pal[inv]


VIEWS = {
    "japan": dict(jp="日本の川", en="Rivers of Japan", rotate=True, w=1.0, colour="flow"),
    "basins": dict(jp="流域", en="River systems", rotate=True, w=1.0, colour="basin"),
    # the Tone, Japan's largest basin, with the Arakawa and Tama beside it
    "kanto": dict(jp="関東", en="Kantō and the Tone", desk=(138.0, 141.5, 35.25, 37.15), phone=(138.55, 140.95, 35.0, 37.25),
                  mode="fill", w=3.2, gain=5.0, colour="flow"),
    # the phone holds the Ishikari, Hokkaido's great river, from the Daisetsu mountains to the sea
    "hokkaido": dict(jp="北海道", en="Hokkaido", desk=(139.7, 146.0, 41.35, 45.6), phone=(140.9, 143.3, 42.55, 44.35),
                     mode="fit", margin=0.05, w=1.7, colour="flow"),
}


def render(name, v, W, H, out, R):
    phone = H > W
    main = R["pts"][::7]
    main = main[main[:, 1] > 30.9]                    # fit the four main islands; the Ryukyus run off the edge
    P = RotProj(W, H, main) if v.get("rotate") else \
        EquiProj(W, H, *(v["phone"] if phone else v["desk"]), margin=0.0 if phone else v.get("margin", 0.0),
                 mode="fill" if phone else v.get("mode", "fill"))
    cv = Canvas(W, H)
    z = min(W, H) / 2160
    q = R["DIS_AV_CMS"]
    rgb = flow_rgb(q) if v["colour"] == "flow" else basin_rgb(R)
    # light per pixel of river grows with the water it carries, gently, so trickles still draw the land
    w = (0.16 + 1.6 * (np.maximum(q, 0.1) / 400) ** 0.5) * v["w"] * (1.25 if phone else 1.0)
    x, y = P(R["pts"][:, 0], R["pts"][:, 1])
    off = R["off"]
    seen = np.zeros(len(q), bool)                     # reaches with any part inside the frame
    for i in range(len(q)):
        a, b = off[i], off[i + 1]
        xs, ys = x[a:b], y[a:b]
        if xs.max() < -20 or xs.min() > W + 20 or ys.max() < -20 or ys.min() > H + 20:
            continue
        seen[i] = True
        cv.add_polyline(xs, ys, rgb[i], w[i], step=0.6)
    im = cv.finish(core=0.55 * max(1, z), glow=5 * z, glow_amt=0.45, gain=v.get("gain", 4.2), black=1.2e-2)
    km = R["LENGTH_KM"][seen].sum()
    caption(im, f"{v['jp']}  {v['en']}  ·  {seen.sum():,} river reaches, {km:,.0f} km, as bright as the water they carry  ·  "
                f"HydroRIVERS", ramp=FLOW if v["colour"] == "flow" else None)
    save(im, out)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--info":

    R = load()
    n = len(R["HYRIV_ID"])
    big = np.argsort(-R["DIS_AV_CMS"])
    print(n, "reaches;", len(np.unique(R["MAIN_RIV"])), "river systems;",
          f"{R['LENGTH_KM'].sum():,.0f} km of river")
    for i in big[:5]:
        print(f"  {R['DIS_AV_CMS'][i]:8.1f} m3/s  order {R['ORD_STRA'][i]}  "
              f"{R['DIST_DN_KM'][i]:6.1f} km from the sea  at {R['pts'][R['off'][i]]}")


elif __name__ == "__main__":
    R = load()
    for n in sys.argv[1:] or list(VIEWS):
        render(n, VIEWS[n], *DESKTOP, f"out/rivers_{n}_desktop.png", R)
        render(n, VIEWS[n], *PHONE, f"out/rivers_{n}_phone.png", R)
