"""Mount Fuji as glowing contour lines (等高線), coloured like sunrise on the mountain (赤富士).

Data: 1 arc-second (~30 m) elevation model of the Fuji area, from the geovista-data
repository (fuji_dem.tif). Contours every 10 m, every 100 m slightly brighter.
"""
import numpy as np, tifffile
from skimage.measure import find_contours
from scipy.ndimage import gaussian_filter
from common import Canvas, caption, save, dl, DESKTOP, PHONE

t = tifffile.TiffFile(dl("geovista-data", "assets", "rasters", "fuji_dem.tif"))
dem = t.asarray().astype(np.float32)
dem[dem < -1000] = np.nan
LON0, LAT0, RES = 138.48513888888888, 35.519861111111105, 1 / 3600
SUMMIT = (138.7274, 35.3606)
k = np.cos(np.radians(35.36))

# sunrise on Fuji: indigo base -> crimson -> orange -> pale gold -> white summit
STOPS = [(0, (0.16, 0.10, 0.45)), (900, (0.45, 0.10, 0.55)), (1600, (0.85, 0.12, 0.30)),
         (2300, (1.00, 0.42, 0.18)), (3000, (1.00, 0.80, 0.55)), (3776, (1.00, 1.00, 1.00))]
RAMP = [c for _, c in STOPS]


def ecolor(e):
    ks = np.array([s for s, _ in STOPS]); cs = np.array([c for _, c in STOPS])
    return np.stack([np.interp(e, ks, cs[:, i]) for i in range(3)], -1)


from scipy.ndimage import distance_transform_edt
_, (iy, ix) = distance_transform_edt(np.isnan(dem), return_indices=True)
smooth = gaussian_filter(dem[iy, ix], 0.8)          # fill gaps (lakes, sea) from nearest land
LEVELS = np.arange(200, 3760, 10)
CONTOURS = [(lev, c) for lev in LEVELS for c in find_contours(smooth, lev) if len(c) > 12]
print(len(CONTOURS), "contour lines")


def render(W, H, out):
    phone = H > W
    span_km = 13 if phone else 27                   # width of the view in km
    s = W / (span_km / (111.32 * k))                  # px per degree of longitude
    cv = Canvas(W, H)
    z = min(W, H) / 2160
    lat_c = SUMMIT[1] - 0.012 if phone else SUMMIT[1] - 0.004  # keep the frame inside the data
    ny, nx = dem.shape
    for lev, c in CONTOURS:
        lon = LON0 + c[:, 1] * RES; lat = LAT0 - c[:, 0] * RES
        x = W / 2 + (lon - SUMMIT[0]) * s
        y = H / 2 - (lat - lat_c) * s / k
        if x.max() < 0 or x.min() > W or y.max() < 0 or y.min() > H:
            continue
        major = lev % 100 == 0
        w = (0.30 if major else 0.10) * (1.25 if phone else 1) * (0.10 + 0.90 * (lev / 3776) ** 1.15)
        # fade out within ~40 cells of the data edge so the file border never draws a line
        e = np.minimum.reduce([c[:, 0], ny - 1 - c[:, 0], c[:, 1], nx - 1 - c[:, 1]])
        w = w * np.clip((e - 4) / 40, 0, 1)
        cv.add_polyline(x, y, ecolor(lev), w, step=0.5)
    im = cv.finish(core=0.5 * max(1, z), glow=4 * z, glow_amt=0.45, gain=3.4, black=1.5e-2)
    caption(im, "富士山  Mount Fuji, 3,776 m  ·  contour lines every 10 m, sunrise colours by height  ·  "
                "30 m elevation model", ramp=RAMP)
    save(im, out)


if __name__ == "__main__":
    render(*DESKTOP, "out/fuji_desktop.png")
    render(*PHONE, "out/fuji_phone.png")
