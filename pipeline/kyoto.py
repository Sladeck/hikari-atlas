"""Kyoto's cherry blossom, 812 to today: the longest flowering record on Earth.

One blossom per year with a record (838 of them), from old diaries and chronicles for the early
centuries to modern observation. Desktop: year left to right, peak-bloom date bottom (early) to
top (late). Phone: year top to bottom, date left (early) to right (late). The deeper the pink,
the earlier that year bloomed compared with the 812-1850 average; a faint line traces the
30-year average, which held near mid-April for a thousand years and has fallen since 1900.
Data: Aono & Kazui (2008), Aono & Saito (2010), Katata (2026), via Our World in Data.
"""
import numpy as np, pandas as pd
from PIL import ImageDraw, ImageFont
from common import Canvas, caption, save, dl, DESKTOP, PHONE, F_LIGHT, flower_sprite, add_sprite

d = pd.read_csv(dl("kyoto", "kyoto_peak_bloom.csv")).rename(
    columns={"Year": "year", "Day of the year with peak cherry blossom": "doy", "Thirty-year average": "avg"})
d = d[["year", "doy", "avg"]]
pts = d.dropna(subset=["doy"]).reset_index(drop=True)
avg = d.dropna(subset=["avg"]).reset_index(drop=True)
Y0, Y1 = 800, 2030                         # axis span (the record runs 812 to the latest spring)
D0, D1 = 80, 126                           # day-of-year span (the record runs 84 to 124)
BASE = pts[pts.year <= 1850].doy.mean()    # the pre-industrial average, about 105 (mid-April)
WHITE, PINK = np.array([1.0, 0.97, 0.98]), np.array([1.0, 0.34, 0.62])


def frame(W, H):
    phone = H > W
    mx, my = (0.12, 0.06) if phone else (0.06, 0.12)

    def xy(year, doy):
        a = (np.asarray(year, float) - Y0) / (Y1 - Y0)        # 0..1 along the centuries
        b = (np.asarray(doy, float) - D0) / (D1 - D0)          # 0..1 early -> late
        if phone:
            return W * mx + b * W * (1 - 2 * mx), H * my + a * H * (1 - 2 * my - 0.05)
        return W * mx + a * W * (1 - 2 * mx), H * (1 - my) - b * H * (1 - 2 * my)
    return xy, phone, mx, my


def render(W, H, out):
    xy, phone, mx, my = frame(W, H)
    z = min(W, H) / 2160
    cv = Canvas(W, H)
    # the 30-year average: a faint thread of light under the blossoms
    ax, ay = xy(avg.year.values, avg.avg.values)
    gaps = np.where(np.diff(avg.year.values) > 1)[0] + 1      # break the line where the average is undefined
    for seg in np.split(np.arange(len(avg)), gaps):
        if len(seg) > 1:
            cv.add_polyline(ax[seg], ay[seg], (1.0, 0.62, 0.78), 0.30 * z)
    early = np.clip((BASE - pts.doy.values) / 14, 0, 1) ** 0.8
    col = WHITE * (1 - early[:, None]) + PINK * early[:, None]
    rng = np.random.default_rng(3)
    x, y = xy(pts.year.values, pts.doy.values + rng.uniform(-0.45, 0.45, len(pts)))   # dates are whole days
    r = 13.0 * z * (1.3 if phone else 1)
    sprites = [flower_sprite(r, rot) for rot in np.linspace(0, 2 * np.pi / 5, 8, endpoint=False)]
    for i in rng.permutation(len(x)):
        add_sprite(cv, x[i], y[i], sprites[i % 8], col[i], 0.40 + 0.30 * early[i])
    im = cv.finish(core=0.9, glow=9 * z, glow_amt=0.45, gain=2.4, gamma=0.8, black=1.5e-2)

    # faint ticks: centuries and dates, so the chart can be read
    dr = ImageDraw.Draw(im)
    u = z * (1.5 if phone else 1)
    f = ImageFont.truetype(F_LIGHT, int(18 * u))
    tick = (80, 70, 75)
    for yr in (900, 1200, 1500, 1800, 2000):
        px, py = xy(yr, D0)
        if phone:
            dr.text((W * 0.035, py), str(yr), font=f, fill=tick, anchor="lm")
        else:
            dr.text((px, H * (1 - my) + 34 * u), str(yr), font=f, fill=tick, anchor="mm")
    for name, doy in (("1 Apr", 91), ("15 Apr", 105), ("1 May", 121)):
        px, py = xy(Y0, doy)
        if phone:
            dr.text((px, H * my - 30 * u), name, font=f, fill=tick, anchor="mm")
        else:
            dr.text((W * mx - 20 * u, py), name, font=f, fill=tick, anchor="rm")
    first = pts.loc[pts.doy.idxmin()]                         # the earliest spring on record
    px, py = xy(first.year, first.doy)
    label = f"{int(first.year)}, the earliest on record"
    if phone:
        dr.text((px, py + 30 * u), label, font=f, fill=(150, 110, 125), anchor="lt")
    else:
        dr.text((px - 26 * u, py + 6 * u), label, font=f, fill=(150, 110, 125), anchor="rt")
    caption(im, f"桜  Kyoto, {int(pts.year.min())}–{int(pts.year.max())}  ·  peak bloom in {len(pts)} years of records  ·  "
                "deeper pink = earlier than the 812–1850 average  ·  Aono & Kazui, Aono & Saito, Katata",
            ramp=[WHITE, PINK])
    save(im, out)


if __name__ == "__main__":
    print(len(pts), "years with a date; pre-1850 average day", round(BASE, 1))
    render(*DESKTOP, "out/kyoto_desktop.png")
    render(*PHONE, "out/kyoto_phone.png")
