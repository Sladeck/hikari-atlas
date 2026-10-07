"""The plates in 3D: the quakes of the earthquake views at their real position and depth.

Every M4.5+ quake east of 136°E, lifted out of the map: east and north in km, depth stretched x2
(at true scale the slabs are thin next to a 3,000 km arc), seen in perspective from above the
Pacific. The sinking Pacific plate shows as sheets of light: diving under Japan and the Kurils,
and plunging to 680 km under the Izu-Bonin arc. Colour = depth, size = magnitude.
"""
import sys
import numpy as np
from PIL import Image
import render_views as rv
from common import caption, save, DESKTOP, PHONE

LON0, LAT0 = 138.0, 36.0                      # centre of the scene
KM = 111.32
K = np.cos(np.radians(LAT0))
VEX = 2.0                                     # vertical exaggeration, stated in the caption
WEST = (134.0, 137.0)                         # the Pacific plate only: fade out west of here
CAMERA = {"desktop": (125, 22), "phone": (195, 35)}   # azimuth, elevation (deg)


def scene(df):
    E = (df.lon.values - LON0) * KM * K
    N = (df.lat.values - LAT0) * KM
    Z = -df.depth.values * VEX
    return E, N, Z


def camera(E, N, Z, az, el, dist=4200.0):
    """Perspective camera at azimuth az (deg from north, clockwise) and elevation el above the
    horizon, looking at the scene centre. Returns view-plane u, v and a size factor."""
    a, e = np.radians(az), np.radians(el)
    dx, dy = -np.sin(a), -np.cos(a)            # horizontal viewing direction
    rx, ry = dy, -dx                           # screen right
    along = E * dx + N * dy
    u = E * rx + N * ry
    v = Z * np.cos(e) + along * np.sin(e)
    persp = dist / (dist + along * np.cos(e) - Z * np.sin(e))
    return u * persp, v * persp, persp


def weights(df):
    """Soft edges: fade towards the western cut and the edges of the downloaded box."""
    t = np.clip((df.lon.values - WEST[0]) / (WEST[1] - WEST[0]), 0, 1)
    e = np.minimum.reduce([rv.DATA_CLIP[1] - df.lon.values, df.lat.values - rv.DATA_CLIP[2],
                           rv.DATA_CLIP[3] - df.lat.values])
    u = np.clip(e / 1.5, 0, 1)
    return (t * t * (3 - 2 * t)) * (u * u * (3 - 2 * u))


def render(df, W, H, az, el, out, label=True):
    f = weights(df)
    df, f = df[f > 0], f[f > 0]
    pu, pv, persp = camera(*scene(df), az, el)
    core = f > 0.5                             # frame the cloud on its core, not the faded edges
    lo_u, hi_u = np.percentile(pu[core], [0.5, 99.5]); lo_v, hi_v = np.percentile(pv[core], [0.5, 99.5])
    mx, my = (0.04, 0.10) if W >= H else (0.06, 0.16)
    s = min(W * (1 - 2 * mx) / (hi_u - lo_u), H * (1 - 2 * my) / (hi_v - lo_v))
    x = W / 2 + (pu - (lo_u + hi_u) / 2) * s
    y = H / 2 - (pv - (lo_v + hi_v) / 2) * s

    z = min(W, H) / 2160
    buf = np.zeros((H, W, 3), np.float32)
    col = rv.depth_color(df.depth.values)
    m = df.mag.values
    for i in range(len(df)):
        dm = m[i] - 4.5
        sig = max(0.7, 1.9 * z * 1.30 ** dm * persp[i])
        rv.splat(buf, x[i], y[i], sig * 3.0, col[i], f[i] * 0.016 * 1.25 ** dm)   # halo
        rv.splat(buf, x[i], y[i], sig, col[i], f[i] * 0.16 * 1.28 ** dm)          # core
    img = np.clip(1.0 - np.exp(-buf * 2.6), 0, 1) ** 0.85
    arr = (img * 255 + 0.5).astype(np.uint8)
    arr[buf.max(-1) < 1e-3] = 0                # guaranteed #000000
    im = Image.fromarray(arr)
    if label:
        caption(im, f"地震  The plates in 3D  ·  {int((f > 0.5).sum()):,} quakes M4.5+, "
                    f"{df.time.min().year}–{df.time.max().year}  ·  depth ×{VEX:g}  ·  USGS",
                ramp=[c for _, c in rv.RAMP])
    save(im, out)


if __name__ == "__main__":
    df = rv.load()
    if len(sys.argv) > 1 and sys.argv[1] == "--try":           # quick low-res camera check
        render(df, 960, 540, *CAMERA["desktop"], "out/try_quakes_3d_desktop.png")
        render(df, 430, 932, *CAMERA["phone"], "out/try_quakes_3d_phone.png")
    else:
        render(df, *DESKTOP, *CAMERA["desktop"], "out/quakes_3d_desktop.png")
        render(df, *PHONE, *CAMERA["phone"], "out/quakes_3d_phone.png")
