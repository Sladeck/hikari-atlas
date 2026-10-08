"""Two typhoons that changed Japan, each drawn alone from the JMA best track.

  isewan_1959   Typhoon Vera (伊勢湾台風), September 1959
  hagibis_2019  Typhoon Hagibis (令和元年東日本台風), October 2019

The track is coloured by central pressure like the other typhoon wallpapers (whiter = deeper),
with a glowing bead every 6 hours sized by intensity: the gaps between beads show the storm's
speed. Small date labels mark 00 UTC each day; a faint coastline gives the place.
Best-track times are UTC (JST = UTC + 9).
"""
import json
from datetime import datetime
import numpy as np
from PIL import ImageDraw, ImageFont
import typhoons as ty
import render_views as rv
from common import Canvas, caption, save, EquiProj, dl, DESKTOP, PHONE, F_LIGHT

STORMS = {
    "isewan_1959": dict(id="5915", jp="伊勢湾台風", en="Typhoon Vera (Isewan), 1959"),
    "hagibis_2019": dict(id="1919", jp="令和元年東日本台風", en="Typhoon Hagibis, 2019"),
}


def track(sid):
    """Rows of (time, grade, lon, lat, pressure) for one storm, from its 66666 header to the next."""
    rows, on = [], False
    for line in open(ty.BST):
        if line.startswith("66666"):
            if on:
                break
            on = line.split()[1] == sid
            continue
        if on:
            p = line.split()
            yy = int(p[0][:2]); year = 1900 + yy if yy > 50 else 2000 + yy
            t = datetime(year, int(p[0][2:4]), int(p[0][4:6]), int(p[0][6:8]))
            rows.append((t, int(p[2]), int(p[4]) / 10, int(p[3]) / 10, int(p[5])))
    return rows


def coast(box):
    lo0, lo1, la0, la1 = box
    out = []
    for f in json.load(open(dl("ne", "land10.geojson")))["features"]:
        g = f["geometry"]
        for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
            for ring in poly:
                r = np.asarray(ring)
                if r[:, 0].max() > lo0 and r[:, 0].min() < lo1 and r[:, 1].max() > la0 and r[:, 1].min() < la1:
                    out.append(r)
    return out


def render(name, W, H, out):
    s = STORMS[name]
    rows = track(s["id"])
    t = [r[0] for r in rows]
    grade, lon, lat, pres = (np.array([r[i] for r in rows], float) for i in range(1, 5))
    phone = H > W
    # frame: the tropical part of the track, with room around it; the extratropical tail runs off the edge
    core = grade != 6
    pad = 2.5
    box = (lon[core].min() - pad, lon[core].max() + pad, lat[core].min() - pad, lat[core].max() + pad)
    P = EquiProj(W, H, *box, margin=0.06 if phone else 0.05, mode="fit")
    z = min(W, H) / 2160 * (1.4 if phone else 1)
    cv = Canvas(W, H)
    for r in coast(box):                                       # the faintest outline of the land
        x, y = P(r[:, 0], r[:, 1])
        if x.max() < 0 or x.min() > W or y.max() < 0 or y.min() > H:
            continue
        cv.add_polyline(x, y, (0.45, 0.50, 0.62), 0.16 * z, step=0.7)
    x, y = P(lon, lat)
    col = ty.pcolor(pres)
    col[grade == 6] *= np.array([0.5, 0.45, 0.8])              # extratropical tail: faded violet
    depth = np.clip((1010 - pres) / 110, 0, 1)                  # 0 at 1010 hPa, 1 at 900 hPa
    w = (0.30 + 2.7 * depth ** 1.3) * z
    cv.add_polyline(x, y, col, np.where(grade == 6, w * 0.4, w))
    for i in range(len(rows)):                                  # a bead every 6 hours
        if t[i].hour % 6:
            continue
        r = (3.0 + 13.0 * depth[i] ** 1.2) * z
        rv.splat(cv.buf, x[i], y[i], r, col[i], 0.10 + 0.45 * depth[i])
    im = cv.finish(core=0.9 * max(1, z), glow=6 * z, glow_amt=0.4, gain=3.0, black=1.6e-2)

    dr = ImageDraw.Draw(im)
    u = min(W, H) / 2160 * (1.5 if phone else 1)
    f = ImageFont.truetype(F_LIGHT, int(18 * u))
    f2 = ImageFont.truetype(F_LIGHT, int(24 * u))
    for i in range(len(rows)):                                  # one date a day, beside the track
        if t[i].hour == 0:
            dr.text((x[i] + 18 * u, y[i]), t[i].strftime("%-d %b"), font=f, fill=(95, 110, 125), anchor="lm")
    k = int(np.argmin(pres))                                    # the deepest point
    dr.text((x[k] - 22 * u, y[k]), f"{int(pres[k])} hPa", font=f2, fill=(175, 205, 220), anchor="rm")
    caption(im, f"台風  {s['jp']}  {s['en']}  ·  {t[0]:%-d %b} to {t[-1]:%-d %b %Y}, every 6 hours, dates at 00 UTC  ·  "
                f"lowest {int(pres.min())} hPa  ·  JMA best track", ramp=ty.RAMP)
    save(im, out)


if __name__ == "__main__":
    for n, s in STORMS.items():
        rows = track(s["id"])
        p = np.array([r[4] for r in rows])
        print(n, len(rows), "points", rows[0][0], "->", rows[-1][0], "min", p.min(), "hPa at", rows[int(p.argmin())][0])
        render(n, *DESKTOP, f"out/{n}_desktop.png")
        render(n, *PHONE, f"out/{n}_phone.png")
