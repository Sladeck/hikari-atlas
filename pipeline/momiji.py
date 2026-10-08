"""Autumn leaves (紅葉前線): the day each JMA station's reference maple turns red, and its ginkgo yellow.

Data: JMA 生物季節観測累年値, かえでの紅葉 (015.csv) and いちょうの黄葉 (013.csv), from
https://www.data.jma.go.jp/sakura/data/download_ruinenchi.html, in dl/jma-phenology/ (Shift_JIS).
Each row is a station (the last three digits of its WMO number, 47***); each year has a value
(month * 100 + day, 0 = not observed) and a remark: 8, 9 = the regular species (on site, nearby),
6, 7 = a substitute species. A date that slips into January is still written in its autumn's
column, so months 1 to 3 belong to the following calendar year. Station positions come from the
sakura data (dl/sakura/data/locations.csv), with the same four corrections as sakura.py.

    python momiji.py                 # every view, desktop and phone, into out/
    python momiji.py front map       # some of them (front, icho, map, stripes)
    python momiji.py --info          # what the data says
"""
import io
import os
import sys
import numpy as np
import pandas as pd
from PIL import ImageDraw, ImageFont
from common import Canvas, caption, save, add_sprite, dl, DESKTOP, PHONE, F_LIGHT

FILES = {"kaede": "015.csv", "icho": "013.csv"}
FIX = {597: (140.21, 37.13), 612: (138.25, 37.10), 651: (136.52, 34.73), 741: (133.07, 35.46)}  # as sakura.py


def stations():
    loc = pd.read_csv(dl("sakura", "data", "locations.csv"))
    for code, (lo, la) in FIX.items():
        loc.loc[loc.l_code == code, ["lon", "lat"]] = lo, la
    return loc[["l_code", "lon", "lat", "romaji", "loc_names"]]


def load(kind="kaede"):
    """Long table: one row per station and autumn, with the day of the autumn (days after 1 January
    of that year; a January date counts past 365) and the remark code."""
    raw = open(dl("jma-phenology", FILES[kind]), "rb").read().decode("shift_jis")
    rows = list(pd.read_csv(io.StringIO(raw), header=None, skiprows=2, dtype=str).itertuples(index=False))
    hdr = pd.read_csv(io.StringIO(raw), header=None, skiprows=1, nrows=1, dtype=str).iloc[0].tolist()
    years = [(i, int(h)) for i, h in enumerate(hdr) if h and str(h).isdigit() and 1900 < int(h) < 2100]
    out = []
    for r in rows:
        code, name = int(r[0]), str(r[1]).strip().replace("　", "")
        for i, y in years:
            v, rm = r[i], r[i + 1]
            if v is None or not str(v).strip().isdigit() or int(v) == 0:
                continue
            v = int(v); m, d = v // 100, v % 100
            if not (1 <= m <= 12 and 1 <= d <= 31):
                continue
            doy = pd.Timestamp(2001, m, 1).dayofyear + d - 1 + (365 if m <= 3 else 0)
            out.append((code, name, y, doy, int(rm) if str(rm).isdigit() else 0))
    df = pd.DataFrame(out, columns=["l_code", "name", "year", "doy", "rm"])
    return df.merge(stations(), on="l_code", how="left")


# ---------------------------------------------------------------- leaves
def maple_sprite(r, rot=0.0):
    """A Japanese maple leaf (iroha-momiji) of radius r px: a full palm with five broad pointed lobes and
    two small ones at its base, and a short stem."""
    n = int(np.ceil(r * 1.25)) * 2 + 1
    yy, xx = np.mgrid[:n, :n] - n // 2
    c, s_ = np.cos(rot), np.sin(rot)
    xr, yr = c * xx - s_ * yy, s_ * xx + c * yy
    ang = np.arctan2(xr, -yr)                               # 0 = up
    rad = np.hypot(xr, yr) / r
    reach = np.full_like(rad, 0.46)                         # the palm
    for th, L in ((0, 1.0), (0.95, 0.92), (-0.95, 0.92), (1.85, 0.68), (-1.85, 0.68), (2.55, 0.40), (-2.55, 0.40)):
        d = np.abs((ang - th + np.pi) % (2 * np.pi) - np.pi)
        reach = np.maximum(reach, 0.46 + (L - 0.46) * np.clip(1 - d / 0.52, 0, 1) ** 1.25)
    a = np.clip((reach - rad) * 5.0, 0, 1)
    stem = np.exp(-(xr / (0.045 * r)) ** 2) * ((yr > 0) & (yr < 0.62 * r))
    a = np.maximum(a, 0.8 * stem)
    a += 0.3 * np.exp(-(rad / 0.14) ** 2)                   # where the veins meet
    return a.astype(np.float32)


def ginkgo_sprite(r, rot=0.0):
    """A ginkgo leaf: a wide fan with a wavy edge and a notch at its middle, on a thin stem."""
    n = int(np.ceil(r * 1.25)) * 2 + 1
    yy, xx = np.mgrid[:n, :n] - n // 2
    c, s_ = np.cos(rot), np.sin(rot)
    xr, yr = c * xx - s_ * yy, s_ * xx + c * yy
    oy = 0.35 * r                                           # the fan opens from just below the centre
    ang = np.arctan2(xr, -(yr - oy))
    rad = np.hypot(xr, yr - oy) / r
    inside = np.abs(ang) < 1.15                             # about 130 degrees
    edge = 1.05 + 0.04 * np.cos(ang * 9) - 0.22 * np.exp(-(ang / 0.07) ** 2)
    a = np.clip((edge - rad) * 6.0, 0, 1) * inside * np.clip((1.15 - np.abs(ang)) * 8, 0, 1)
    stem = np.exp(-(xr / (0.04 * r)) ** 2) * ((yr > oy) & (yr < oy + 0.45 * r))
    return np.maximum(a, 0.8 * stem).astype(np.float32)


GOLD, CRIMSON = np.array([1.0, 0.80, 0.32]), np.array([0.98, 0.16, 0.20])     # maple: 1953 -> 2025
PALE_Y, DEEP_Y = np.array([1.0, 0.96, 0.66]), np.array([1.0, 0.66, 0.08])     # ginkgo: 1953 -> 2025
DOY0, DOY1 = 268, 382                                     # late September .. mid January
MONTHS = [("Oct", 274), ("Nov", 305), ("Dec", 335), ("Jan", 366)]


def front(kind, W, H, out):
    """x = date, y = latitude, one leaf per station per autumn; older autumns pale, recent ones deep,
    so the drift towards later colouring shows as the deep leaves trailing behind."""
    df = load(kind)
    phone = H > W
    cv = Canvas(W, H)
    mx, my = (0.10, 0.07) if phone else (0.07, 0.10)
    lat0, lat1 = df.lat.min() - 0.6, df.lat.max() + 0.6
    y0, y1 = int(df.year.min()), int(df.year.max())
    t = ((df.year.values - y0) / (y1 - y0)) ** 1.1
    c0, c1 = (GOLD, CRIMSON) if kind == "kaede" else (PALE_Y, DEEP_Y)
    col = c0 * (1 - t[:, None]) + c1 * t[:, None]
    rng = np.random.default_rng(5 if kind == "kaede" else 6)
    a = (df.doy.values + rng.uniform(-0.5, 0.5, len(df)) - DOY0) / (DOY1 - DOY0)
    b = (df.lat.values - lat0) / (lat1 - lat0)
    if phone:
        x = W * mx + b * W * (1 - 2 * mx); y = H * my + a * H * (1 - 2 * my - 0.05)
    else:
        x = W * mx + a * W * (1 - 2 * mx); y = H * (1 - my) - b * H * (1 - 2 * my)
    jit = (rng.random(len(x)) - 0.5) * (H if not phone else W) * 0.004
    if phone: x = x + jit * 0.6
    else: y = y + jit * 0.6
    z = min(W, H) / 2160
    r = 11.0 * z * (1.25 if phone else 1)
    make = maple_sprite if kind == "kaede" else ginkgo_sprite
    sprites = [make(r, rot) for rot in np.linspace(-0.6, 0.6, 8)]
    for i in rng.permutation(len(x)):
        add_sprite(cv, x[i], y[i], sprites[i % 8], col[i], 0.42)
    im = cv.finish(core=0.6, glow=6 * z, glow_amt=0.25, gain=2.4, gamma=0.8, black=1.5e-2)
    d = ImageDraw.Draw(im)
    u = min(W, H) / 2160 * (1.5 if phone else 1)
    f = ImageFont.truetype(F_LIGHT, int(18 * u))
    for name, doy in MONTHS:
        p = (doy - DOY0) / (DOY1 - DOY0)
        if phone:
            d.text((W * 0.035, H * my + p * H * (1 - 2 * my - 0.05)), name, font=f, fill=(80, 72, 66), anchor="lm")
        else:
            d.text((W * mx + p * W * (1 - 2 * mx), H * (1 - my) + 34 * u), name, font=f, fill=(80, 72, 66), anchor="mm")
    for city in ["KAGOSHIMA", "FUKUOKA", "KYOTO", "TOKYO", "SENDAI", "SAPPORO", "ASAHIKAWA"]:
        r_ = df[df.romaji == city]
        if not len(r_):
            continue
        lat, doy = r_.lat.iloc[0], np.percentile(r_.doy, 98)        # just after the latest dates
        a_, b_ = (doy - DOY0) / (DOY1 - DOY0), (lat - lat0) / (lat1 - lat0)
        if phone:
            d.text((W * mx + b_ * W * (1 - 2 * mx), H * my + a_ * H * (1 - 2 * my - 0.05) + 24 * u), city.title(),
                   font=f, fill=(110, 100, 94), anchor="mt")
        else:
            d.text((W * mx + a_ * W * (1 - 2 * mx) + 22 * u, H * (1 - my) - b_ * H * (1 - 2 * my)), city.title(),
                   font=f, fill=(110, 100, 94), anchor="lm")
    if kind == "kaede":
        text = f"紅葉前線  The autumn leaf front  ·  first red maple at {df.l_code.nunique()} cities  ·  {y0} gold → {y1} crimson  ·  JMA"
    else:
        text = f"銀杏の黄葉  Ginkgo gold  ·  first yellow ginkgo at {df.l_code.nunique()} cities  ·  {y0} pale → {y1} deep gold  ·  JMA"
    caption(im, text, ramp=[c0, c1])
    save(im, out)


# ---------------------------------------------------------------- map and stripes
def trends(kind="kaede"):
    from scipy.stats import theilslopes
    df = load(kind)
    rows = [(code, theilslopes(g.doy.values, g.year.values)[0] * 10)
            for code, g in df.groupby("l_code") if len(g) >= 30]
    return pd.DataFrame(rows, columns=["l_code", "slope"]).merge(stations(), on="l_code")


PALE_L, VIVID_L = np.array([0.95, 0.90, 0.80]), np.array([1.0, 0.12, 0.10])


def leaf_map(W, H, out):
    """One maple leaf per city, deeper red the later its leaves now turn than in the 1950s."""
    import sakura_map as sm                                # the same rotated frame and faint coastline
    T = trends("kaede")
    phone = H > W
    P = sm.Proj(W, H, rotate=not phone)
    cv = Canvas(W, H)
    z = min(W, H) / 2160 * (1.5 if phone else 1)
    for ring in sm.coast:
        x, y = P(ring[:, 0], ring[:, 1])
        if x.max() < 0 or x.min() > W or y.max() < 0 or y.min() > H:
            continue
        cv.add_polyline(x, y, (0.60, 0.40, 0.30), 0.09 * (1.3 if phone else 1), step=0.7)
    tt = np.clip(T.slope.values / 5.0, 0, 1) ** 0.9        # 0 = no change, 1 = 5+ days later per decade
    col = PALE_L * (1 - tt[:, None]) + VIVID_L * tt[:, None]
    x, y = P(T.lon.values, T.lat.values)
    rng = np.random.default_rng(4)
    sprites = [maple_sprite(r, rot) for r in (19 * z, 24 * z) for rot in np.linspace(-0.5, 0.5, 4)]
    for i in np.argsort(tt):
        add_sprite(cv, x[i], y[i], sprites[(1 if tt[i] > 0.5 else 0) * 4 + rng.integers(4)], col[i], 0.55 + 0.7 * tt[i])
    im = cv.finish(core=0.7 * max(1, z), glow=9 * z, glow_amt=0.55, gain=2.4, gamma=0.85, black=1.2e-2)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(F_LIGHT, int(19 * z))
    for city in ["KAGOSHIMA", "KYOTO", "TOKYO", "SENDAI", "SAPPORO"]:
        r_ = T[T.romaji == city]
        if len(r_):
            cx, cy = P(r_.lon.iloc[0], r_.lat.iloc[0])
            d.text((cx + 22 * z, cy - 22 * z), city.title(), font=f, fill=(120, 104, 96), anchor="ls")
    if P.th:
        a = P.th + np.pi / 2; dx, dy = np.cos(a), -np.sin(a)
        cx, cy, L = W - 70 * z, H - 70 * z, 22 * z
        d.line([(cx - dx * L, cy - dy * L), (cx + dx * L, cy + dy * L)], fill=(100, 90, 85), width=max(1, int(1.5 * z)))
        d.text((cx + dx * (L + 14 * z), cy + dy * (L + 14 * z)), "N", font=f, fill=(100, 90, 85), anchor="mm")
    caption(im, f"紅葉  Autumn leaf map  ·  {len(T)} JMA cities  ·  deeper red = maples turn later than in the 1950s "
                f"(up to 5 days per decade)  ·  {int((T.slope > 0).mean() * 100)}% of cities now turn later",
            ramp=[PALE_L, (PALE_L + VIVID_L) / 2, VIVID_L])
    save(im, out)


LATE_S, MID_S, EARLY_S = np.array([1.0, 0.22, 0.14]), np.array([1.0, 0.90, 0.80]), np.array([0.55, 0.66, 1.0])


def stripes(W, H, out, k=3.0):
    """One thread per city with 30+ autumns: red where its maples turned late against its own average."""
    d = load("kaede")
    d = d[d.groupby("l_code").year.transform("size") >= 30].copy()
    d["anom"] = d.doy - d.groupby("l_code").doy.transform("mean")      # days; positive = late
    cities = d.groupby("l_code").agg(lat=("lat", "first"), name=("romaji", "first")).sort_values("lat")
    row = {c: i for i, c in enumerate(cities.index)}
    y0, y1 = int(d.year.min()), int(d.year.max())
    phone = H > W
    mx, my = (0.08, 0.07) if phone else (0.07, 0.11)
    nc, ny = len(cities), y1 - y0 + 1
    if phone:
        cw, ch = W * (1 - 2 * mx) / nc, H * (1 - 2 * my - 0.04) / ny
    else:
        cw, ch = W * (1 - 2 * mx) / ny, H * (1 - 2 * my) / nc
    cv = Canvas(W, H)
    z = min(W, H) / 2160

    def colour(a):
        t = np.clip(a / 12.0, -1, 1)                                    # +1 = 12+ days late
        late, early = np.clip(t, 0, 1), np.clip(-t, 0, 1)
        c = MID_S * (1 - late - early)[:, None] + LATE_S * late[:, None] + EARLY_S * early[:, None]
        return c, 0.06 + 0.9 * late ** 1.3 + 0.10 * early
    for code, g in d.sort_values("year").groupby("l_code"):
        i = row[code] + 0.5
        c, w = colour(g.anom.values)
        j = g.year.values - y0 + 0.5
        for seg in np.split(np.arange(len(g)), np.where(np.diff(g.year.values) > 1)[0] + 1):
            jj = np.concatenate([[j[seg[0]] - 0.42], j[seg], [j[seg[-1]] + 0.42]])
            cc = np.concatenate([c[seg[:1]], c[seg], c[seg[-1:]]])
            ww = np.concatenate([w[seg[:1]], w[seg], w[seg[-1:]]]) * k * z
            if phone:
                xs, ys = np.full(len(jj), W * mx + i * cw), H * my + jj * ch
            else:
                xs, ys = W * mx + jj * cw, np.full(len(jj), H * (1 - my) - i * ch)
            cv.add_polyline(xs, ys, cc, ww)
    im = cv.finish(core=2.2 * z, glow=7 * z, glow_amt=0.4, gain=2.2, gamma=0.85, black=1.5e-2)
    dr = ImageDraw.Draw(im)
    u = z * (1.5 if phone else 1)
    f = ImageFont.truetype(F_LIGHT, int(18 * u))
    tick = (80, 72, 66)
    for yr in (1960, 1980, 2000, y1):
        j = yr - y0 + 0.5
        if phone:
            dr.text((W * mx - 14 * u, H * my + j * ch), str(yr), font=f, fill=tick, anchor="rm")
        else:
            dr.text((W * mx + j * cw, H * (1 - my) + 30 * u), str(yr), font=f, fill=tick, anchor="mm")
    for name in ("KAGOSHIMA", "TOKYO", "SENDAI", "SAPPORO", "ASAHIKAWA"):
        hit = cities[cities.name == name]
        if not len(hit):
            continue
        i = row[hit.index[0]] + 0.5
        if phone:
            dr.text((W * mx + i * cw, H * my - 16 * u), name.title(), font=f, fill=tick, anchor="ls")
        else:
            dr.text((W * mx - 14 * u, H * (1 - my) - i * ch), name.title(), font=f, fill=tick, anchor="rm")
    caption(im, f"紅葉の縞  Autumn leaf stripes  ·  first red maple at {len(cities)} cities, {y0}–{y1}, each against its own "
                "average  ·  red = late, white = usual, blue = early  ·  JMA", ramp=[EARLY_S * 0.5, MID_S * 0.4, LATE_S])
    save(im, out)


VIEWS = {"front": lambda W, H, o: front("kaede", W, H, o), "icho": lambda W, H, o: front("icho", W, H, o),
         "map": leaf_map, "stripes": stripes}
NAMES = {"front": "momiji", "icho": "icho", "map": "momiji_map", "stripes": "momiji_stripes"}


if __name__ == "__main__" and "--info" in sys.argv:
    from scipy.stats import theilslopes
    for kind in FILES:
        df = load(kind)
        print(f"{kind}: {len(df)} dates at {df.l_code.nunique()} stations, {df.year.min()}..{df.year.max()}, "
              f"no position: {df.lat.isna().sum()}, remarks {df.rm.value_counts().to_dict()}")
        print("   day range", df.doy.min(), df.doy.max(), " January dates:", (df.doy > 365).sum())
        sl = [theilslopes(g.doy, g.year)[0] * 10 for _, g in df.groupby("l_code") if len(g) >= 30]
        sl = np.array(sl)
        print(f"   {len(sl)} stations with 30+ autumns: median trend {np.median(sl):+.2f} days/decade, later at {(sl > 0).mean():.0%}")
        per = df[df.year.between(1953, 1962)].groupby("l_code").doy.mean()
        now = df[df.year.between(2016, 2025)].groupby("l_code").doy.mean()
        both = (now - per).dropna()
        print(f"   1953-62 vs 2016-25 at {len(both)} stations: median {both.median():+.1f} days")


if __name__ == "__main__" and "--info" not in sys.argv:
    for n in [a for a in sys.argv[1:] if not a.startswith("--")] or list(VIEWS):
        VIEWS[n](*DESKTOP, f"out/{NAMES[n]}_desktop.png")
        VIEWS[n](*PHONE, f"out/{NAMES[n]}_phone.png")
