"""The sakura front: first-bloom date of cherry trees at 102 JMA stations, 1953 to 2018.

Desktop: x = date (January to May), y = latitude of the city. One soft petal per
station per year. Old years are white, recent years pink, so the drift towards
earlier blooming shows up as pink running ahead of white.
Phone: same chart turned 90° (date runs top to bottom).
Data: JMA さくらの開花日 (via github.com/akg314/sakura, flowering.csv).
"""
import numpy as np, pandas as pd
from PIL import ImageDraw, ImageFont
from common import Canvas, caption, save, DESKTOP, PHONE, F_LIGHT, flower_sprite, add_sprite, dl

D = dl("sakura", "data") + "/"
fl = pd.read_csv(D + "flowering.csv")
loc = pd.read_csv(D + "locations.csv")
FIX = {597: (140.21, 37.13), 612: (138.25, 37.10), 651: (136.52, 34.73), 741: (133.07, 35.46)}  # misgeocoded stations
for code, (lo, la) in FIX.items():
    loc.loc[loc.l_code == code, ["lon", "lat"]] = lo, la
df = fl.merge(loc[["l_code", "lat", "lon", "romaji"]], on="l_code").dropna(subset=["lat"])
df = df[df.day.astype(str).str.isdigit()].copy()          # "-" = no observation that year
df["day"] = df.day.astype(int)
mm, dd = df.day // 100, df.day % 100
df["doy"] = pd.to_datetime(dict(year=2001, month=mm, day=dd), errors="coerce").dt.dayofyear
df = df.dropna(subset=["doy"])

Y0, Y1 = int(df.year.min()), int(df.year.max())
WHITE, PINK = np.array([1.0, 0.97, 0.98]), np.array([1.0, 0.42, 0.66])
DOY0, DOY1 = -6, 148             # late Dec .. late May
LAT0, LAT1 = df.lat.min() - 0.6, df.lat.max() + 0.6


def render(W, H, out):
    phone = H > W
    cv = Canvas(W, H)
    mx, my = (0.10, 0.07) if phone else (0.07, 0.10)
    t = (df.year.values - Y0) / (Y1 - Y0)
    col = WHITE * (1 - t[:, None] ** 1.2) + PINK * (t[:, None] ** 1.2)
    rng = np.random.default_rng(1)
    a = (df.doy.values + rng.uniform(-0.5, 0.5, len(df)) - DOY0) / (DOY1 - DOY0)   # 0..1 along the season
    b = (df.lat.values - LAT0) / (LAT1 - LAT0)            # 0..1 south -> north
    if phone:   # season runs downwards, south on the left
        x = W * mx + b * W * (1 - 2 * mx); y = H * my + a * H * (1 - 2 * my - 0.05)
    else:       # season runs rightwards, north at the top
        x = W * mx + a * W * (1 - 2 * mx); y = H * (1 - my) - b * H * (1 - 2 * my)
    jit = (rng.random(len(x)) - 0.5) * (H if not phone else W) * 0.004   # separate years on one row
    if phone: x = x + jit * 0.6
    else: y = y + jit * 0.6
    z = min(W, H) / 2160
    r = 6.5 * z * (1.25 if phone else 1)
    sprites = [flower_sprite(r, rot) for rot in np.linspace(0, 2 * np.pi / 5, 8, endpoint=False)]
    order = rng.permutation(len(x))
    for i in order:
        add_sprite(cv, x[i], y[i], sprites[i % 8], col[i], 0.55)
    im = cv.finish(core=0.6, glow=6 * z, glow_amt=0.25, gain=2.4, gamma=0.8, black=1.5e-2)

    # faint month ticks so the chart can be read
    d = ImageDraw.Draw(im)
    u = min(W, H) / 2160 * (1.5 if phone else 1)
    f = ImageFont.truetype(F_LIGHT, int(18 * u))
    for name, doy in [("Jan", 1), ("Feb", 32), ("Mar", 60), ("Apr", 91), ("May", 121), ("Jun", 152)]:
        p = (doy - DOY0) / (DOY1 - DOY0)
        if phone:
            yy = H * my + p * H * (1 - 2 * my - 0.05)
            d.text((W * 0.035, yy), name, font=f, fill=(80, 70, 75), anchor="lm")
        else:
            xx = W * mx + p * W * (1 - 2 * mx)
            d.text((xx, H * (1 - my) + 34 * u), name, font=f, fill=(80, 70, 75), anchor="mm")
    for city in ["NAHA", "KAGOSHIMA", "TOKYO", "SENDAI", "SAPPORO", "WAKKANAI"]:
        r = df[df.romaji == city]
        if not len(r):
            continue
        lat, doy = r.lat.iloc[0], np.percentile(r.doy, 2)        # just before the earliest blooms
        a_, b_ = (doy - DOY0) / (DOY1 - DOY0), (lat - LAT0) / (LAT1 - LAT0)
        if phone:
            px, py = W * mx + b_ * W * (1 - 2 * mx), H * my + a_ * H * (1 - 2 * my - 0.05) - 22 * u
            d.text((px, py), city.title(), font=f, fill=(110, 100, 105), anchor="mb")
        else:
            px, py = W * mx + a_ * W * (1 - 2 * mx) - 22 * u, H * (1 - my) - b_ * H * (1 - 2 * my)
            d.text((px, py), city.title(), font=f, fill=(110, 100, 105), anchor="rm")
    caption(im, f"桜前線  The sakura front  ·  first bloom at {df.l_code.nunique()} cities  ·  "
                f"{Y0} white → {Y1} pink  ·  JMA", ramp=[WHITE, PINK])
    save(im, out)


if __name__ == "__main__":
    print(len(df), "bloom dates")
    render(*DESKTOP, "out/sakura_desktop.png")
    render(*PHONE, "out/sakura_phone.png")
