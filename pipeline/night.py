"""Japan at night: the lights of the islands as NASA's Suomi NPP satellite saw them in 2016.

Data: NASA Earth Observatory Black Marble 2016, grayscale 500 m tile D1 (90-180 E, 0-90 N),
dl/blackmarble/BlackMarble_2016_D1_geo_gray.tif (15 arc-second pixels, WGS 84, corner at 90 E 90 N).
The grayscale is NASA's visual stretch of the VIIRS day/night band composite, not calibrated radiance.
The first run cuts out Japan's box into dl/blackmarble/japan_2016.png. Only lights on Japan's land
(the rivers.py land mask, grown by about 4 km for the coast) are kept, so no light from Korea, China
or Russia enters the frame.

    python night.py                  # every view, desktop and phone, into out/
    python night.py japan tokaido    # some of them (japan, tokaido, rivers)
"""
import os
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, binary_dilation
from common import Canvas, caption, save, dl, DESKTOP, PHONE

TIF = dl("blackmarble", "BlackMarble_2016_D1_geo_gray.tif")
CROP = dl("blackmarble", "japan_2016.png")
LON0, LON1, LAT0, LAT1 = 122.0, 147.0, 23.0, 46.5
PX = 240                                            # pixels per degree (15 arc-seconds)


def lights():
    """Japan's box as floats 0..1 with every light off Japan's land switched off."""
    if not os.path.exists(CROP):
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(TIF)
        x0, x1 = int((LON0 - 90) * PX), int((LON1 - 90) * PX)
        y0, y1 = int((90 - LAT1) * PX), int((90 - LAT0) * PX)
        im.crop((x0, y0, x1, y1)).convert("L").save(CROP)
    a = np.asarray(Image.open(CROP), np.float32) / 255
    import rivers
    m, _ = rivers.japan_mask(res=1 / PX)                # Japan's land on the same 15" grid
    m = binary_dilation(m, iterations=8)                # ~4 km: the coast and its harbours
    # the mask's box is rivers.BOX; place it on this crop's grid
    B = rivers.BOX
    keep = np.zeros_like(a, bool)
    r0, c0 = int(round((LAT1 - B[3]) * PX)), int(round((B[0] - LON0) * PX))
    h, w = min(m.shape[0], a.shape[0] - r0), min(m.shape[1], a.shape[1] - c0)
    keep[r0:r0 + h, c0:c0 + w] = m[:h, :w]
    return a * keep


class Frame:
    """The Rivers chapter's rotated national view (or a north-up box), with its inverse, so every
    output pixel can look up the light under it."""
    def __init__(self, W, H, box=None):
        self.W, self.H = W, H
        if box is None:
            import rivers
            R = rivers.load()
            main = R["pts"][::7]; main = main[main[:, 1] > 30.9]
            P = rivers.RotProj(W, H, main)
            self.k, self.lon0, self.lat0, self.th = P.k, P.lon0, P.lat0, P.th
            self.s, self.uc, self.vc, self.res = P.s, P.uc, P.vc, P.res
        else:
            lo0, lo1, la0, la1 = box
            self.lat0, self.lon0 = (la0 + la1) / 2, (lo0 + lo1) / 2
            self.k, self.th, self.res = np.cos(np.radians(self.lat0)), 0.0, 0.0
            self.s = max(W / ((lo1 - lo0) * self.k), H / (la1 - la0))      # fill the frame
            self.uc = self.vc = 0.0

    def lonlat(self, X, Y):
        ur = (X - self.W / 2) / self.s + self.uc
        vr = -(Y - (self.H - self.res) / 2) / self.s + self.vc
        c, s = np.cos(self.th), np.sin(self.th)
        u, v = c * ur + s * vr, -s * ur + c * vr
        return u / self.k + self.lon0, v + self.lat0

    def __call__(self, lon, lat):
        u, v = (np.asarray(lon) - self.lon0) * self.k, np.asarray(lat) - self.lat0
        c, s = np.cos(self.th), np.sin(self.th)
        ur, vr = c * u - s * v, s * u + c * v
        return self.W / 2 + (ur - self.uc) * self.s, (self.H - self.res) / 2 - (vr - self.vc) * self.s


def sample(A, F):
    """The light under every pixel of frame F (bilinear on the 15" grid)."""
    Y, X = np.mgrid[0:F.H, 0:F.W].astype(np.float32) + 0.5
    lon, lat = F.lonlat(X, Y)
    return map_coordinates(A, [(LAT1 - lat) * PX - 0.5, (lon - LON0) * PX - 0.5], order=1, cval=0.0).astype(np.float32)


# light -> colour: the faint glow of towns warm amber, bright city cores white
LAMP = [(0.0, (1.00, 0.55, 0.20)), (0.35, (1.00, 0.74, 0.42)), (0.7, (1.00, 0.90, 0.72)), (1.0, (1.0, 1.0, 1.0))]


def lamp(v):
    ks = np.array([k for k, _ in LAMP]); cs = np.array([c for _, c in LAMP])
    return np.stack([np.interp(v, ks, cs[:, i]) for i in range(3)], -1).astype(np.float32)


VIEWS = {
    "japan": dict(jp="夜の日本", en="Japan at night"),
    # the Tokaido megalopolis, Tokyo to Osaka; the phone holds Kanto around Tokyo and its bay
    "tokaido": dict(jp="東海道", en="The Tōkaidō corridor", desk=(134.7, 140.6, 33.9, 36.5), phone=(138.7, 140.95, 34.6, 37.0)),
    "rivers": dict(jp="光と川", en="Light and rivers"),
}


def render(name, v, W, H, out, A):
    phone = H > W
    F = Frame(W, H, box=(v["phone"] if phone else v["desk"]) if "desk" in v else None)
    L = sample(A, F)
    zoom = F.s / PX                                      # output pixels per source pixel
    cv = Canvas(W, H)
    if name == "rivers":
        P = F
        import rivers as rv
        R = rv.load()
        x, y = P(R["pts"][:, 0], R["pts"][:, 1])
        off = R["off"]
        q = R["DIS_AV_CMS"]
        w = (0.10 + 0.9 * (np.maximum(q, 0.1) / 400) ** 0.5)
        for i in range(len(q)):
            cv.add_polyline(x[off[i]:off[i + 1]], y[off[i]:off[i + 1]], (0.25, 0.42, 1.0), w[i], step=0.8)
    I = np.clip(L, 0, 1) ** 1.8                          # NASA's stretch, eased back towards linear light
    cv.buf += lamp(np.clip(L, 0, 1)) * I[..., None] * 1.3  # so the city cores keep their streets
    zz = np.sqrt(max(1, zoom))                           # a close view is enlarged 500 m pixels: glow only a little more
    im = cv.finish(core=0.6 * zz, glow=4.5 * zz, glow_amt=0.35 if zoom <= 1.2 else 0.22, gain=1.9 if zoom <= 1.2 else 1.6,
                   gamma=0.9, black=1.6e-2)
    caption(im, f"{v['jp']}  {v['en']}  ·  the lights of Japan from space, 2016  ·  NASA Black Marble (Suomi NPP VIIRS)",
            ramp=[c for _, c in LAMP])
    save(im, out)


# ---------------------------------------------------------------- nightfall (for the animation)
EQUINOX = (2025, 266)                                # 23 September 2025, the autumn equinox


def sunset_jst(lon, lat, doy=EQUINOX[1]):
    """Sunset in minutes after midnight JST, from NOAA's general solar position equations
    (gmd.noaa.gov/grad/solcalc/solareqns.PDF); the sun's centre 0.833 degrees below the horizon."""
    g = 2 * np.pi / 365 * (doy - 1)
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
    dec = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g) + 0.000907 * np.sin(2 * g)
           - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    phi = np.radians(lat)
    ha = np.degrees(np.arccos(np.cos(np.radians(90.833)) / (np.cos(phi) * np.cos(dec)) - np.tan(phi) * np.tan(dec)))
    return 720 - 4 * (np.asarray(lon) - ha) - eqt + 540


def export_nightfall(OUT, W, H, tag, A):
    """The night view small enough to rebuild in the browser every frame: the finished light (WebP)
    and the minute each pixel's sun sets (PNG, 0 = no light), on the same frame as the wallpaper."""
    F = Frame(W, H)
    L = sample(A, F)
    I = np.clip(L, 0, 1) ** 1.8
    img = np.clip(1 - np.exp(-lamp(np.clip(L, 0, 1)) * I[..., None] * 1.3 * 1.9), 0, 1) ** 0.9
    Image.fromarray((img * 255 + 0.5).astype(np.uint8)).save(f"{OUT}/night_{tag}.webp", quality=88)
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5
    lon, lat = F.lonlat(X, Y)
    t = sunset_jst(lon, lat)
    lit = img.max(-1) > 0.02
    t0, t1 = float(np.floor(t[lit].min())), float(np.ceil(t[lit].max()))
    code = np.where(lit, 1 + np.round((t - t0) / (t1 - t0) * 254), 0).astype(np.uint8)
    Image.fromarray(code).save(f"{OUT}/night_{tag}_t.png")
    return t0, t1


if __name__ == "__main__":
    A = lights()
    for n in [a for a in sys.argv[1:] if not a.startswith("--")] or list(VIEWS):
        render(n, VIEWS[n], *DESKTOP, f"out/night_{n}_desktop.png", A)
        render(n, VIEWS[n], *PHONE, f"out/night_{n}_phone.png", A)
