"""Two earthquake sequences, quake by quake, from the JMA catalogue (far denser than USGS M4.5+).

  tohoku_2011    the M9.0 of 11 March 2011 and every M2.5+ quake around it in the following week
  kumamoto_2016  the M6.5 foreshock of 14 April 2016, the M7.3 two days later, and every M1.5+
                 quake around them to the end of 2016

Colour is time since the first big shock on a log scale, like embers cooling: the first hours
white, the first days amber, the following weeks red, the rest of the year a dim deep red.
Size is magnitude. The map is turned
along the main axis of the sequence (PCA, as in render_views.py); a small arrow marks north.
"""
import sys
import numpy as np
from PIL import Image
import render_views as rv
import jma_hypo as J
from common import caption, save, DESKTOP, PHONE

SEQS = {
    "tohoku_2011": dict(
        jp="東北地方太平洋沖地震", en="Tōhoku 2011", year=2011, t0="2011-03-11 14:46:18", end="2011-03-18 14:46:18", when="in the week after the M9.0",
        box=(139.8, 145.8, 35.2, 41.6), minmag=2.5, gain=2.2, center=(142.2, 38.2), span=6.0, radius=4.0,
        cities=[("Sendai", 140.87, 38.27), ("Morioka", 141.15, 39.70), ("Fukushima", 140.47, 37.75),
                ("Mito", 140.45, 36.37)]),
    "kumamoto_2016": dict(
        jp="熊本地震", en="Kumamoto 2016", year=2016, t0="2016-04-14 21:26:34", end="2017-01-01", when="to the end of 2016",
        box=(130.4, 131.8, 32.5, 33.45), minmag=1.5, gain=2.2, center=(131.0, 32.95), span=0.95, radius=0.9,
        cities=[("Kumamoto", 130.71, 32.80), ("Ōita", 131.61, 33.24), ("Aso", 131.12, 32.95)]),
}
# time since the first shock (log10 hours) -> colour: white (6 min), amber (10 h), orange (4 days),
# red (6 weeks), deep red (10 months)
T_STOPS = [(-1.0, (1.00, 0.97, 0.90)), (1.0, (1.00, 0.80, 0.48)), (2.0, (1.00, 0.48, 0.18)),
           (3.0, (0.85, 0.18, 0.12)), (3.9, (0.50, 0.07, 0.10))]


def time_color(hours):
    x = np.log10(np.maximum(hours, 0.1))
    ks = np.array([k for k, _ in T_STOPS]); cs = np.array([c for _, c in T_STOPS])
    return np.stack([np.interp(x, ks, cs[:, i]) for i in range(3)], -1)


def sequence(name):
    s = SEQS[name]
    d = J.load(s["year"])
    lo0, lo1, la0, la1 = s["box"]
    d = d[(d.time >= s["t0"]) & (d.time < s["end"]) & d.lon.between(lo0, lo1) & d.lat.between(la0, la1)
          & (d.mag >= s["minmag"])]
    d = d.assign(hours=(d.time - np.datetime64(s["t0"])) / np.timedelta64(1, "h"))
    return d.sort_values("mag").reset_index(drop=True)          # big ones drawn last


def render(name, W, H, out, label=True):
    s = SEQS[name]
    gain = s["gain"]
    d = sequence(name)
    phone = H > W
    view = dict(center=s["center"], span=s["span"], radius=s["radius"], orient="auto", cities=s["cities"],
                margin=(0.03, 0.05))
    P = rv.Proj(view, W, H, d)                                          # axis and frame from every quake drawn
    X, Y = P(d.lon.values, d.lat.values)
    z = min(W, H) / 2160
    col = time_color(d.hours.values)
    buf = np.zeros((H, W, 3), np.float32)
    for x, y, m, c in zip(X, Y, d.mag.values, col):
        if not (-50 < x < W + 50 and -50 < y < H + 50):
            continue
        dm = m - s["minmag"]
        sig = max(0.7, 1.1 * z * 1.40 ** dm)
        rv.splat(buf, x, y, sig * 3.0, c, gain * 0.004 * 1.55 ** dm)    # halo
        rv.splat(buf, x, y, sig, c, gain * 0.05 * 1.50 ** dm)           # core
    img = np.clip(1.0 - np.exp(-buf * 2.6), 0, 1) ** 0.85
    arr = (img * 255 + 0.5).astype(np.uint8)
    arr[buf.max(-1) < 1e-3] = 0                                         # guaranteed #000000
    im = Image.fromarray(arr)
    if label:
        rv.draw_cities(im, P, view, W, H, phone)
        rv.north_arrow(im, P, W, H, phone)
        ramp = time_color(np.geomspace(0.1, d.hours.max(), 6))         # only the span this picture covers
        caption(im, f"{s['jp']}  {s['en']}  ·  {len(d):,} quakes M{s['minmag']:g}+ {s['when']}  ·  "
                    "colour = time since the first shock  ·  JMA", ramp=ramp)
    save(im, out)
    return len(d)


if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if not a.startswith("--")] or list(SEQS)
    for n in names:
        if "--try" in sys.argv:
            render(n, 960, 540, f"out/try_{n}_desktop.png")
            render(n, 430, 932, f"out/try_{n}_phone.png")
        else:
            render(n, *DESKTOP, f"out/{n}_desktop.png")
            render(n, *PHONE, f"out/{n}_phone.png")
