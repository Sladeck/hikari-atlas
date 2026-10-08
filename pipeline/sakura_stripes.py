"""Sakura stripes: every city's first bloom, year by year, as a field of light.

One thread of light per JMA city with 30+ years of records (south at the bottom, north at the top
on desktop; south on the left on phone), running through the years 1953-2018. Along each thread,
colour and brightness show how early or late that city bloomed compared with its own average:
glowing pink = early, faint white = about average, dim blue-white = late. Years without an
observation leave a gap (from about 2007 many stations stopped observing, so their threads end).
In the spirit of Ed Hawkins' warming stripes, with each city as its own thermometer.
"""
import numpy as np
from PIL import ImageDraw, ImageFont
import sakura as sk
from common import Canvas, caption, save, DESKTOP, PHONE, F_LIGHT

d = sk.df
n = d.groupby("l_code").year.transform("size")
d = d[n >= 30].copy()
d["anom"] = d.doy - d.groupby("l_code").doy.transform("mean")      # days; negative = early
cities = d.groupby("l_code").agg(lat=("lat", "first"), name=("romaji", "first")).sort_values("lat")
ROW = {c: i for i, c in enumerate(cities.index)}
Y0, Y1 = int(d.year.min()), int(d.year.max())
EARLY, MID, LATE = np.array([1.0, 0.30, 0.60]), np.array([1.0, 0.93, 0.95]), np.array([0.62, 0.70, 1.0])


def colour(a):
    """Colour and weight for anomalies in days (negative = early)."""
    t = np.clip(-a / 9.0, -1, 1)                                       # +1 = 9+ days early
    e, l = np.clip(t, 0, 1), np.clip(-t, 0, 1)
    c = MID * (1 - e - l)[:, None] + EARLY * e[:, None] + LATE * l[:, None]
    return c, 0.06 + 0.9 * e ** 1.3 + 0.10 * l                         # usual years faint, early ones glow


def render(W, H, out, k=3.0):
    phone = H > W
    mx, my = (0.08, 0.07) if phone else (0.07, 0.11)
    nc, ny = len(cities), Y1 - Y0 + 1
    if phone:      # years run down, cities south -> north left to right
        cw, ch = W * (1 - 2 * mx) / nc, H * (1 - 2 * my - 0.04) / ny
    else:          # years run right, cities south -> north bottom to top
        cw, ch = W * (1 - 2 * mx) / ny, H * (1 - 2 * my) / nc
    cv = Canvas(W, H)
    z = min(W, H) / 2160
    # one thread of light per city, through the centre of each year; broken where a year is missing
    for code, g in d.sort_values("year").groupby("l_code"):
        i = ROW[code] + 0.5
        c, w = colour(g.anom.values)
        j = g.year.values - Y0 + 0.5
        breaks = np.where(np.diff(g.year.values) > 1)[0] + 1
        for seg in np.split(np.arange(len(g)), breaks):
            # stretch each run half a year either side so single years still show as a dash
            jj = np.concatenate([[j[seg[0]] - 0.42], j[seg], [j[seg[-1]] + 0.42]])
            cc = np.concatenate([c[seg[:1]], c[seg], c[seg[-1:]]])
            ww = np.concatenate([w[seg[:1]], w[seg], w[seg[-1:]]]) * k * z
            if phone:
                xs, ys = np.full(len(jj), W * mx + i * cw), H * my + jj * ch
            else:
                xs, ys = W * mx + jj * cw, np.full(len(jj), H * (1 - my) - i * ch)
            cv.add_polyline(xs, ys, cc, ww)
    z = min(W, H) / 2160
    im = cv.finish(core=2.2 * z, glow=7 * z, glow_amt=0.4, gain=2.2, gamma=0.85, black=1.5e-2)

    dr = ImageDraw.Draw(im)
    u = z * (1.5 if phone else 1)
    f = ImageFont.truetype(F_LIGHT, int(18 * u))
    tick = (80, 70, 75)
    for yr in (1960, 1980, 2000, Y1):
        j = yr - Y0 + 0.5
        if phone:
            dr.text((W * mx - 14 * u, H * my + j * ch), str(yr), font=f, fill=tick, anchor="rm")
        else:
            dr.text((W * mx + j * cw, H * (1 - my) + 30 * u), str(yr), font=f, fill=tick, anchor="mm")
    for name in ("NAHA", "KAGOSHIMA", "TOKYO", "SENDAI", "SAPPORO", "WAKKANAI"):
        hit = cities[cities.name == name]
        if not len(hit):
            continue
        i = ROW[hit.index[0]] + 0.5
        if phone:
            dr.text((W * mx + i * cw, H * my - 16 * u), name.title(), font=f, fill=tick, anchor="ls")
        else:
            dr.text((W * mx - 14 * u, H * (1 - my) - i * ch), name.title(), font=f, fill=tick, anchor="rm")
    caption(im, f"桜  Sakura stripes  ·  first bloom at {len(cities)} cities, {Y0}–{Y1}, each against its own average  ·  "
                "pink = early, white = usual, blue = late  ·  JMA", ramp=[LATE * 0.5, MID * 0.4, EARLY])
    save(im, out)


if __name__ == "__main__":
    print(len(cities), "cities,", len(d), "bloom dates")
    render(*DESKTOP, "out/sakura_stripes_desktop.png")
    render(*PHONE, "out/sakura_stripes_phone.png")
