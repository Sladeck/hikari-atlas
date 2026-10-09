"""Mount Fuji's summit cone as ridge lines: profiles across the line of sight, one every 167 m,
stacked in perspective from the south, close enough to read the crater rim, the 1707 Hōei crater on
the south-east flank and the gullies. Each line hides what lies behind it: the lines are drawn near
to far and a running horizon per pixel column keeps only what rises above the lines already drawn.
True vertical scale, sunrise colours by height as in fuji.py.

Data: the same 1 arc-second (~30 m) elevation model (geovista-data, fuji_dem.tif). render() takes
any mountain and view, as mountains.py does for Kita-dake and Oku-hotaka.
"""
import numpy as np
from PIL import ImageDraw, ImageFont
from scipy.ndimage import map_coordinates
import fuji as F
from fuji_side import Cam, KM
from common import Canvas, caption, save, F_LIGHT, DESKTOP, PHONE

# the summit cone close up, from about 1,500 m to the crater rim. Distances in km from the summit:
# near / far along the line of sight, half the width of each line, the spacing of the lines
VIEW = {"desktop": dict(near=-3.85, far=7.17, step=0.167, half=6.35,
                        cam=dict(dist=19, cam_h=7.5, az_deg=0, target_h=2.6, fov_deg=31, y_frac=0.43)),
        "phone": dict(near=-5.08, far=5.49, step=0.134, half=4.08,
                      cam=dict(dist=17, cam_h=7.0, az_deg=0, target_h=2.7, fov_deg=26, y_frac=0.50))}
F.jp, F.height = "富士山", 3776
F.summit_name = "剣ヶ峰  3,776 m"
F.labels = [(138.75207, 35.34292, "宝永山  Hōei, 1707 crater")]   # the peak on the rim of the 1707 crater
SIDES = {0: "south", -90: "east", 90: "west", 180: "north"}


def height(M, lon, lat):
    """Elevation (m) at lon/lat, bilinear in the smoothed model."""
    return map_coordinates(M.smooth, [(M.LAT0 - lat) / M.RES, (lon - M.LON0) / M.RES], order=1, mode="nearest")


def render(W, H, out, M=F, view=None, text=None):
    phone = H > W
    V = view or VIEW["phone" if phone else "desktop"]
    cam = Cam(W, H, **V["cam"])
    kk = np.cos(np.radians(M.SUMMIT[1]))
    a = np.radians(V["cam"]["az_deg"])
    fwd, right = np.array([np.sin(a), np.cos(a)]), np.array([np.cos(a), -np.sin(a)])   # line of sight, across it
    z = min(W, H) / 2160 if not phone else W / 1290 * 0.75
    rows = np.arange(V["near"], V["far"] + 1e-9, V["step"])
    s = np.linspace(-V["half"], V["half"], 2400)
    cv = Canvas(W, H)
    horizon = np.full(W + 2, np.inf)                     # highest line drawn so far, per column (screen y)
    peak = None
    for i, t in enumerate(rows):                         # near to far
        e, n = t * fwd[0] + s * right[0], t * fwd[1] + s * right[1]          # km east, north of the summit
        h = height(M, M.SUMMIT[0] + e / (KM * kk), M.SUMMIT[1] + n / KM)
        x, y, d = cam.project(e, n, h / 1000)
        sv = s
        if x[0] > x[-1]:
            x, y, h, e, n, sv = x[::-1], y[::-1], h[::-1], e[::-1], n[::-1], s[::-1]
        cols = np.arange(max(int(np.ceil(x.min())), 0), min(int(x.max()), W - 1) + 1)
        if len(cols) < 2:
            continue
        yc = np.interp(cols, x, y)
        hc = np.interp(cols, x, h)
        vis = yc < horizon[cols] - 0.5
        horizon[cols] = np.minimum(horizon[cols], yc)
        far = np.clip(1.15 - i / max(len(rows) - 1, 1) * 0.45, 0.6, 1.15)   # farther lines a little dimmer
        w = 0.42 * (1.2 if phone else 1) * far * (0.45 + 0.55 * (hc / 3776) ** 0.8) * vis
        if "spot" in V:                                  # a range, not a lone cone: light falls off away from the summit
            ec, nc = np.interp(cols, x, e), np.interp(cols, x, n)
            w = w * (0.22 + 0.78 * np.exp(-(np.hypot(ec, nc) / V["spot"]) ** 2))
        w = w * V.get("w", 1.0)
        # a window onto the mountain, not a slab: every line fades out over its outer quarter
        sc = np.interp(cols, x, sv)
        edge = np.clip((V["half"] - np.abs(sc)) / (0.25 * V["half"]), 0, 1)
        edge = np.minimum(edge, np.clip(np.minimum(cols, W - 1 - cols) / (0.14 * W), 0, 1))   # and before the frame
        w = w * edge * edge * (3 - 2 * edge)
        cv.add_polyline(cols, yc, F.ecolor(hc), w, step=0.5)
        j = np.argmax(hc)
        if vis[j] and (peak is None or hc[j] > peak[2]):
            peak = (cols[j], yc[j], hc[j])
    im = cv.finish(core=0.45 * max(1, z), glow=4 * z, glow_amt=0.4, gain=3.2, black=1.5e-2)
    d = ImageDraw.Draw(im)
    u = H / 2160 if not phone else W / 1290 * 0.9
    f = ImageFont.truetype(F_LIGHT, int(17 * u))
    grey = (110, 110, 110)
    labels = list(M.labels)
    if M is not F:                                       # a 30 m model can misorder twin summits: label the real one
        labels.insert(0, (M.SUMMIT[0], M.SUMMIT[1], f"{M.jp}  {M.height:,} m"))
        peak = None
    for plon, plat, name in labels:
        e, n = (plon - M.SUMMIT[0]) * KM * kk, (plat - M.SUMMIT[1]) * KM
        hx, hy, _ = cam.project(np.array([e]), np.array([n]), height(M, np.array([plon]), np.array([plat])) / 1000)
        hx, hy = float(hx[0]), float(hy[0])
        if not (0 < hx < W and 0 < hy < H):
            continue
        if hy <= horizon[int(hx)] + 3:                   # on the skyline: a short leader straight up
            d.line([(hx, hy - 16 * u), (hx, hy - 60 * u)], fill=grey, width=max(1, int(u)))
            d.text((hx, hy - 72 * u), name, font=f, fill=grey, anchor="ms")
        else:                                            # on the near face: out into the dark beside it
            tw = d.textlength(name, font=f)
            lx = min(hx + 0.09 * W, W - tw - 0.04 * W)
            ly = horizon[int(lx):int(lx + tw) + 1].min() - 46 * u
            d.line([(hx, hy - 8 * u), (lx - 6 * u, ly + 6 * u)], fill=grey, width=max(1, int(u)))
            d.text((lx, ly), name, font=f, fill=grey, anchor="ls")
    if peak:                                            # the summit, with a leader line
        px, py, _ = peak
        d.line([(px, py - 16 * u), (px, py - 70 * u)], fill=grey, width=max(1, int(u)))
        d.text((px, py - 82 * u), getattr(M, "summit_name", f"{M.jp}  {M.height:,} m"), font=f, fill=grey, anchor="ms")
    side = SIDES.get(round(V["cam"]["az_deg"] / 90) * 90, "side")
    what = "The summit cone" if M is F else M.en
    caption(im, text or f"{M.jp}  {what} in ridge lines  ·  {len(rows)} profiles one every {V['step'] * 1000:.0f} m, seen from "
                f"the {side}, true vertical scale  ·  {'30 m elevation model' if M is F else 'Copernicus DEM, 30 m'}",
            ramp=F.RAMP)
    save(im, out)


if __name__ == "__main__":
    render(*DESKTOP, "out/fuji_ridges_desktop.png")
    render(*PHONE, "out/fuji_ridges_phone.png")
