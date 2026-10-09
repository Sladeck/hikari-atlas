"""Where the 2011 Tōhoku tsunami reached the coast: every point the joint survey measured.

Data: the 2011 Tohoku Earthquake Tsunami Joint Survey Group, release 20121229 (final), tide-corrected,
dl/tsunami/ttjt_survey_29-Dec-2012_tidecorrected_web.csv (Shift-JIS). Each point is a mark the water
left: an inundation height (type I, the water's height where it stood) or a run-up height (type R,
the ground height where it stopped), both above the tide at the time, with the distance from the
shoreline for most of them. Only points graded A (clear mark) or B (reliable witness) are drawn.

    python tsunami_coast.py           # both views, desktop and phone, into out/
    python tsunami_coast.py heights   # one of them
    python tsunami_coast.py --info    # the figures the chapter text quotes
"""
import sys
from types import SimpleNamespace
import numpy as np
import pandas as pd
from common import Canvas, caption, save, dl, DESKTOP, PHONE
from volcanoes import splat
import rivers

CSV = dl("tsunami", "ttjt_survey_29-Dec-2012_tidecorrected_web.csv")
# the tsunami chapter's own light: navy, teal, aqua, white (as tsunami_render.py)
RAMP = np.array([(0.00, 0.30, 0.55), (0.00, 0.70, 0.80), (0.55, 0.95, 1.00), (1, 1, 1)], np.float32)


def load():
    d = pd.read_csv(CSV, skiprows=1, encoding="cp932", skipinitialspace=True)
    d.columns = [c.strip() for c in d.columns]
    kind = d["type"].astype(str).str.strip()
    grade = d["reliability"].astype(str).str.strip().str[0]
    h = d["height corrected by ttjt [m]"]
    keep = grade.isin(["A", "B"]) & kind.isin(["R", "I"]) & h.notna() & (h > 0) & d["lon [deg]"].notna() & d["lat [deg]"].notna()
    d = d[keep]
    return dict(lon=d["lon [deg]"].values, lat=d["lat [deg]"].values, h=d["height corrected by ttjt [m]"].values,
                dist=d["runup distance [m]"].values, kind=kind[keep].values, place=d["location"].values)


def ramp(t):
    t = np.clip(t, 0, 1) * (len(RAMP) - 1)
    a = np.minimum(t.astype(int), len(RAMP) - 2)
    f = (t - a)[:, None]
    return RAMP[a] * (1 - f) + RAMP[a + 1] * f


def land(cv, P, w):
    """Japan's land drawn faintly by its rivers, as in volcanoes.py: the tsunami ran up them too."""
    R = rivers.load()
    x, y = P(R["pts"][:, 0], R["pts"][:, 1])
    off = R["off"]
    for i in range(len(off) - 1):
        xs, ys = x[off[i]:off[i + 1]], y[off[i]:off[i + 1]]
        if xs.max() < -20 or xs.min() > cv.W + 20 or ys.max() < -20 or ys.min() > cv.H + 20:
            continue
        cv.add_polyline(xs, ys, (0.62, 0.58, 0.55), w, step=0.8)


VIEWS = {
    # every point, from Hokkaido to Okinawa's latitude, framed as the Rivers chapter frames Japan
    "heights": dict(jp="津波の高さ", en="How high the 2011 tsunami reached"),
    # the Sendai plain and Ishinomaki, from Sōma to the Oshika peninsula: where it went farthest inland,
    # 14.5 km up the Kitakami
    "inland": dict(jp="浸水", en="How far the 2011 tsunami came inland", box=(140.75, 141.7, 37.7, 38.75)),
}


def render(name, v, W, H, out):
    S = load()
    phone = H > W
    z = min(W, H) / 2160 if not phone else W / 1290 * 0.75
    if name == "heights":
        R = rivers.load()
        main = R["pts"][::7]
        P = rivers.RotProj(W, H, main[main[:, 1] > 30.9])
        land_w, size, amp = 0.05, 1.0, 0.38
    else:
        lo0, lo1, la0, la1 = v["box"]
        inb = (S["lon"] > lo0) & (S["lon"] < lo1) & (S["lat"] > la0) & (S["lat"] < la1)
        P = rivers.RotProj(W, H, np.stack([S["lon"][inb], S["lat"][inb]], 1))
        land_w, size, amp = 0.14, 2.2, 0.6
    cv = Canvas(W, H)
    land(cv, P, land_w)
    x, y = P(S["lon"], S["lat"])
    h = S["h"]
    k = np.sqrt(np.clip(h / 40, 0.02, 1))                     # 0.14 .. 1: a 40 m mark the largest
    if name == "heights":
        rgb = ramp((h / 40) ** 0.7)
    else:
        d = S["dist"]
        t = np.clip(np.log10(np.maximum(np.nan_to_num(d), 1) / 30) / np.log10(5000 / 30), 0, 1)   # 30 m .. 5 km
        rgb = ramp(t)
        k = 0.55 + 0.45 * k                                    # here the light is about distance, not height
        h = np.where(np.isnan(d), np.nan, h)                   # only the marks with a measured distance
        for ring in rivers.japan_polygons():                   # the shore the distances are measured from
            cx, cy = P(ring[:, 0], ring[:, 1])
            if cx.max() > 0 and cx.min() < W and cy.max() > 0 and cy.min() < H:
                cv.add_polyline(cx, cy, (0.62, 0.58, 0.55), 0.10, step=0.8)
    for i in np.argsort(h)[:np.isfinite(h).sum()]:
        if not (-50 < x[i] < W + 50 and -50 < y[i] < H + 50):
            continue
        splat(cv.buf, x[i], y[i], 7 * z * size * k[i], rgb[i], 0.035 * amp * k[i])     # the glow
        splat(cv.buf, x[i], y[i], 1.6 * z * size, rgb[i], 0.32 * amp * k[i])          # the mark
    shown = np.isfinite(h) & (x > 0) & (x < W) & (y > 0) & (y < H)
    im = cv.finish(core=0.6, glow=5 * max(z, 0.6), glow_amt=0.35, gain=2.4, black=1.2e-2)
    if name == "heights":
        text = (f"{v['jp']}  {v['en']}  ·  {len(h):,} marks, colour = height above the tide, up to {h.max():.0f} m  ·  "
                f"TTJS Group")
    else:
        text = (f"{v['jp']}  {v['en']}  ·  {shown.sum():,} marks, colour = distance from the shore, 30 m to 5 km  ·  "
                f"TTJS Group")
    caption(im, text, ramp=RAMP)
    import render_views as rv                                  # both views are turned: mark north, as the quakes do
    rv.north_arrow(im, SimpleNamespace(theta=P.th), W, H, phone)
    save(im, out)


if __name__ == "__main__" and "--info" in sys.argv:
    S = load()
    h, d, kind = S["h"], S["dist"], S["kind"]
    print(f"{len(h):,} points graded A or B ({(kind == 'R').sum():,} run-up, {(kind == 'I').sum():,} inundation), "
          f"{np.isfinite(d).sum():,} with a distance from the shore")
    i = np.nanargmax(h)
    print(f"highest: {h[i]:.1f} m ({kind[i]}) at {S['place'][i]}, {S['lat'][i]:.3f}N {S['lon'][i]:.3f}E")
    j = np.nanargmax(d)
    print(f"farthest: {d[j]:,.0f} m at {S['place'][j]}")
    print(f"over 10 m: {(h > 10).sum():,}; over 20 m: {(h > 20).sum():,}; over 30 m: {(h > 30).sum():,}")
    print(f"more than 1 km inland: {(d > 1000).sum():,}; more than 5 km: {(d > 5000).sum():,}")
    print(f"latitudes {S['lat'].min():.2f} .. {S['lat'].max():.2f}; "
          f"coast surveyed about {(S['lat'].max() - S['lat'].min()) * 111:.0f} km north to south")

if __name__ == "__main__" and "--info" not in sys.argv:
    for n in [a for a in sys.argv[1:] if not a.startswith("--")] or list(VIEWS):
        render(n, VIEWS[n], *DESKTOP, f"out/tsunami_{n}_desktop.png")
        render(n, VIEWS[n], *PHONE, f"out/tsunami_{n}_phone.png")
