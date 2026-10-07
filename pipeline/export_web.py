"""Export compact binary/JSON data for the website's live canvas animations.

Coordinates are pre-projected with the same projections as the wallpapers and
normalised to 0..1 of a 16:9 (desktop) and a 1290x2796 (phone) frame, so the
browser only has to scale and draw.
"""
import json, os, sys, warnings
import numpy as np
warnings.filterwarnings("ignore")
from common import WEB_PUBLIC
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WEB_PUBLIC, "data")
os.makedirs(OUT, exist_ok=True)
DW, DH, PW, PH = 3840, 2160, 1290, 2796

# ---------------------------------------------------------------- earthquakes
import render_views as rv
df = rv.load()
v = rv.VIEWS["japan"]
Pd = rv.Proj(v, DW, DH, df[df.mag >= 5.0]); Pp = rv.Proj(v, PW, PH, df[df.mag >= 5.0])
xd, yd = Pd(df.lon.values, df.lat.values); xp, yp = Pp(df.lon.values, df.lat.values)
t = df.time.dt.year.values + (df.time.dt.dayofyear.values - 1) / 366
o = np.argsort(t)
arr = np.stack([xd / DW, yd / DH, xp / PW, yp / PH, df.mag.values, df.depth.values, t], 1)[o].astype(np.float32)
arr.tofile(f"{OUT}/quakes.f32")
meta = {"quakes": {"n": len(arr), "fields": ["xd", "yd", "xp", "yp", "mag", "depth", "year"],
                   "theta_d": float(Pd.theta), "theta_p": float(Pp.theta)}}
print("quakes", arr.shape)

# ---------------------------------------------------------------- typhoons
import typhoons as ty
from common import EquiProj
storms = [s for s in ty.load(ty.BST) if s[0, 0] <= 2019]
Ed = EquiProj(DW, DH, 100, 178, 4, 52, margin=0, mode="fill")
Ep = EquiProj(PW, PH, 112, 166, 6, 52, margin=0, mode="fill")
pts, offs = [], [0]
for s in storms:
    a, b = Ed(s[:, 2], s[:, 3]); c, d = Ep(s[:, 2], s[:, 3])
    pts.append(np.stack([a / DW, b / DH, c / PW, d / PH, s[:, 4], s[:, 1], np.full(len(s), s[0, 0])], 1))
    offs.append(offs[-1] + len(s))
P = np.concatenate(pts).astype(np.float32)
P.tofile(f"{OUT}/typhoons.f32")
np.array(offs, np.uint32).tofile(f"{OUT}/typhoons_offsets.u32")
meta["typhoons"] = {"n_points": len(P), "n_storms": len(storms),
                    "fields": ["xd", "yd", "xp", "yp", "pressure", "grade", "year"]}
print("typhoons", P.shape)

# ---------------------------------------------------------------- sakura
import sakura as sk
d = sk.df
rec = np.stack([(d.doy.values - sk.DOY0) / (sk.DOY1 - sk.DOY0), (d.lat.values - sk.LAT0) / (sk.LAT1 - sk.LAT0),
                d.year.values, d.doy.values], 1).astype(np.float32)
rec.tofile(f"{OUT}/sakura.f32")
cities = []
for c in ["NAHA", "KAGOSHIMA", "TOKYO", "SENDAI", "SAPPORO", "WAKKANAI"]:
    r = d[d.romaji == c]
    if len(r):
        cities.append({"name": c.title(), "b": float((r.lat.iloc[0] - sk.LAT0) / (sk.LAT1 - sk.LAT0)),
                       "a": float((np.percentile(r.doy, 2) - sk.DOY0) / (sk.DOY1 - sk.DOY0))})
meta["sakura"] = {"n": len(rec), "fields": ["season", "lat", "year", "doy"], "doy0": sk.DOY0, "doy1": sk.DOY1,
                  "y0": int(d.year.min()), "y1": int(d.year.max()), "cities": cities}
print("sakura", rec.shape)

# ---------------------------------------------------------------- trains (Tokyo)
import trains as tr
tv = tr.VIEWS["tokyo"]
Td = EquiProj(DW, DH, *tv["desk"], margin=0, mode="fill")
Tp = EquiProj(PW, PH, *tv["phone"], margin=0, mode="fill")
lines, tpts = [], []
lo0, lo1, la0, la1 = 139.40, 140.10, 35.45, 35.92
for g, col, w, shink in tr.SEGS:
    keep = (g[:, 0] > lo0) & (g[:, 0] < lo1) & (g[:, 1] > la0) & (g[:, 1] < la1)
    if keep.sum() < 2:
        continue
    gg = g[keep][::2] if keep.sum() > 6 else g[keep]
    a, b = Td(gg[:, 0], gg[:, 1]); c, e = Tp(gg[:, 0], gg[:, 1])
    lines.append({"o": len(tpts), "n": len(gg), "c": [round(float(x), 3) for x in col], "s": int(shink)})
    tpts.extend(np.stack([a / DW, b / DH, c / PW, e / PH], 1).tolist())
np.array(tpts, np.float32).tofile(f"{OUT}/trains_tokyo.f32")
meta["trains"] = {"lines": lines, "n_points": len(tpts)}
print("trains", len(lines), "lines", len(tpts), "points")

json.dump(meta, open(f"{OUT}/meta.json", "w"))
print("wrote", OUT)
