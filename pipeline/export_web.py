"""Export compact binary/JSON data for the website's live canvas animations.

Coordinates are pre-projected with the same projections as the wallpapers and
normalised to 0..1 of a 16:9 (desktop) and a 1290x2796 (phone) frame, so the
browser only has to scale and draw.

Usage: python export_web.py [quakes] [typhoons] [sakura] [trains] [rivers] [volcanoes] [momiji] [night] [--out DIR]
With no names every dataset is exported; meta.json keeps the entries of the ones left out.
"""
import json, os, sys, warnings
import numpy as np
warnings.filterwarnings("ignore")
from common import WEB_PUBLIC, EquiProj

DW, DH, PW, PH = 3840, 2160, 1290, 2796
# the phone stage (anim/Stage.vue) shows a 3:4 window from the middle of the tall PW x PH frame:
# national views are framed for that window and placed in the middle of the frame
PV = round(PW * 4 / 3)


class Band:
    """A projection made for the PW x PV window, moved to the middle of the PW x PH frame."""
    def __init__(self, P):
        self.P, self.dy = P, (PH - PV) / 2
        self.theta = getattr(P, "theta", 0.0)

    def __call__(self, lon, lat):
        x, y = self.P(lon, lat)
        return x, y + self.dy
NAMES = ("quakes", "typhoons", "sakura", "trains", "rivers", "volcanoes", "momiji", "night")


# ---------------------------------------------------------------- earthquakes
def quakes(OUT):
    import render_views as rv
    df = rv.load()
    v = rv.VIEWS["japan"]
    Pd = rv.Proj(v, DW, DH, df[df.mag >= 5.0]); Pp = Band(rv.Proj(v, PW, PV, df[df.mag >= 5.0]))
    xd, yd = Pd(df.lon.values, df.lat.values); xp, yp = Pp(df.lon.values, df.lat.values)
    t = df.time.dt.year.values + (df.time.dt.dayofyear.values - 1) / 366
    o = np.argsort(t)
    arr = np.stack([xd / DW, yd / DH, xp / PW, yp / PH, df.mag.values, df.depth.values, t], 1)[o].astype(np.float32)
    arr.tofile(f"{OUT}/quakes.f32")
    print("quakes", arr.shape)
    return {"n": len(arr), "fields": ["xd", "yd", "xp", "yp", "mag", "depth", "year"],
            "theta_d": float(Pd.theta), "theta_p": float(Pp.theta)}


# ---------------------------------------------------------------- typhoons
def typhoons(OUT):
    import typhoons as ty
    storms = [s for s in ty.load(ty.BST) if s[0, 0] <= ty.LAST]
    Ed = EquiProj(DW, DH, 100, 178, 4, 52, margin=0, mode="fill")
    # the phone stage shows a 3:4 window from the middle of the tall frame: fit the basin across its width
    Ep = EquiProj(PW, PH, 112, 166, 6, 52, margin=0.02, mode="fit")
    pts, offs = [], [0]
    for s in storms:
        a, b = Ed(s[:, 2], s[:, 3]); c, d = Ep(s[:, 2], s[:, 3])
        pts.append(np.stack([a / DW, b / DH, c / PW, d / PH, s[:, 4], s[:, 1], np.full(len(s), s[0, 0])], 1))
        offs.append(offs[-1] + len(s))
    P = np.concatenate(pts).astype(np.float32)
    P.tofile(f"{OUT}/typhoons.f32")
    np.array(offs, np.uint32).tofile(f"{OUT}/typhoons_offsets.u32")
    print("typhoons", P.shape)
    return {"n_points": len(P), "n_storms": len(storms), "y0": int(storms[0][0, 0]), "y1": int(ty.LAST),
            "fields": ["xd", "yd", "xp", "yp", "pressure", "grade", "year"]}


# ---------------------------------------------------------------- sakura
def sakura(OUT):
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
    print("sakura", rec.shape)
    return {"n": len(rec), "fields": ["season", "lat", "year", "doy"], "doy0": sk.DOY0, "doy1": sk.DOY1,
            "y0": int(d.year.min()), "y1": int(d.year.max()), "cities": cities}


# ---------------------------------------------------------------- trains (Tokyo)
def trains(OUT):
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
    print("trains", len(lines), "lines", len(tpts), "points")
    return {"lines": lines, "n_points": len(tpts)}


# ---------------------------------------------------------------- rivers (whole country)
def rivers(OUT):
    """Every reach in the national view, for the animation that runs the rivers from their springs to the sea.
    rivers.u16: x, y (desktop frame), x, y (phone frame) per point, 0..65535 of the frame;
    rivers_reach.u16: distance from the reach's mouth to the sea (10 m), its length (10 m) and its
    average discharge (0.01 m3/s) per reach; rivers_offsets.u32: first point of each reach.
    A reach's points run from upstream to downstream, as in HydroRIVERS."""
    import rivers as rv
    R = rv.load()
    main = R["pts"][::7]; main = main[main[:, 1] > 30.9]
    Pd, Pp = rv.RotProj(DW, DH, main), Band(rv.RotProj(PW, PV, main))
    off, pts = R["off"], R["pts"]
    xs, offs = [], [0]
    for i in range(len(off) - 1):
        g = pts[off[i]:off[i + 1]]
        if len(g) > 3:                                    # keep the ends, thin the middle
            g = np.concatenate([g[:1], g[1:-1:2], g[-1:]])
        a, b = Pd(g[:, 0], g[:, 1]); c, e = Pp(g[:, 0], g[:, 1])
        xs.append(np.stack([a / DW, b / DH, c / PW, e / PH], 1))
        offs.append(offs[-1] + len(g))
    X = np.concatenate(xs)
    q16 = lambda v: np.clip(np.round(v * 65535), 0, 65535).astype("<u2")
    # points just off the frame are kept (clipped to its edge) so rivers run cleanly out of the picture
    q16(np.clip(X, 0, 1)).tofile(f"{OUT}/rivers.u16")
    reach = np.stack([np.round(R["DIST_DN_KM"] * 100), np.round(R["LENGTH_KM"] * 100),
                      np.round(R["DIS_AV_CMS"] * 100)], 1)
    np.clip(reach, 0, 65535).astype("<u2").tofile(f"{OUT}/rivers_reach.u16")
    np.array(offs, "<u4").tofile(f"{OUT}/rivers_offsets.u32")
    print("rivers", len(offs) - 1, "reaches", len(X), "points")
    # the longest path from a spring to the sea: a reach's distance to the sea plus its own length
    return {"reaches": len(offs) - 1, "points": len(X), "maxKm": round(float((R["DIST_DN_KM"] + R["LENGTH_KM"]).max()), 1)}


# ---------------------------------------------------------------- volcanoes (eruptions since 1600)
def volcanoes(OUT):
    """Volcano positions in both frames, every confirmed eruption since 1600, and the faint land behind.
    meta.volcanoes.v: [x, y desktop, x, y phone] per volcano (0..1 of the frame);
    meta.volcanoes.e: [volcano, start year, end year (start + 0.5 when unknown), VEI (-1 unknown)]."""
    import volcanoes as vo
    Pd, Pp = vo.projection(DW, DH), vo.projection(PW, PH)
    vols, conf, name = vo.stripes_rows()
    t = {r["name"]: r for r in vo.table()}
    pos = []
    for n in vols:
        r = t[name[n]]
        a, b = Pd(r["lon"], r["lat"]); c, e = Pp(r["lon"], r["lat"])
        pos.append([round(float(a) / DW, 4), round(float(b) / DH, 4), round(float(c) / PW, 4), round(float(e) / PH, 4)])
    idx = {n: i for i, n in enumerate(vols)}
    ev = []
    for e in sorted(conf, key=lambda e: e["StartDateYear"]):
        s0 = e["StartDateYear"] + ((e["StartDateMonth"] or 1) - 1) / 12
        end = e["EndDateYear"]
        f = end + ((e["EndDateMonth"] or 12) - 0.5) / 12 if end is not None else s0 + 0.5
        vei = e["ExplosivityIndexMax"]
        ev.append([idx[e["Volcano_Number"]], round(s0, 2), round(max(f, s0 + 0.5), 2), -1 if vei is None else int(vei)])
    vo.land_backdrop(1920, 1080, f"{OUT}/volcano_land_d.webp")
    vo.land_backdrop(645, 1398, f"{OUT}/volcano_land_p.webp")
    print("volcanoes", len(pos), "volcanoes", len(ev), "eruptions")
    return {"v": pos, "e": ev, "y0": vo.Y0, "y1": vo.NOW}


# ---------------------------------------------------------------- autumn leaves (the maple front)
def momiji(OUT):
    """Same layout as sakura: per first red maple, [season 0..1, latitude 0..1, year, day of autumn]."""
    import momiji as mo
    d = mo.load("kaede")
    lat0, lat1 = d.lat.min() - 0.6, d.lat.max() + 0.6
    rec = np.stack([(d.doy.values - mo.DOY0) / (mo.DOY1 - mo.DOY0), (d.lat.values - lat0) / (lat1 - lat0),
                    d.year.values, d.doy.values], 1).astype(np.float32)
    rec.tofile(f"{OUT}/momiji.f32")
    cities = []
    for c in ["KAGOSHIMA", "FUKUOKA", "KYOTO", "TOKYO", "SENDAI", "SAPPORO", "ASAHIKAWA"]:
        r = d[d.romaji == c]
        if len(r):
            cities.append({"name": c.title(), "b": float((r.lat.iloc[0] - lat0) / (lat1 - lat0)),
                           "a": float((np.percentile(r.doy, 98) - mo.DOY0) / (mo.DOY1 - mo.DOY0))})
    print("momiji", rec.shape)
    return {"n": len(rec), "fields": ["season", "lat", "year", "doy"], "doy0": mo.DOY0, "doy1": mo.DOY1,
            "y0": int(d.year.min()), "y1": int(d.year.max()), "cities": cities}


# ---------------------------------------------------------------- night (nightfall on the equinox)
def night(OUT):
    """The national night view at 960x540 and 430x932 with each pixel's sunset minute (night.py)."""
    import night as nt
    A = nt.lights()
    d0, d1 = nt.export_nightfall(OUT, 960, 540, "d", A)
    p0, p1 = nt.export_nightfall(OUT, 430, 932, "p", A, view=round(430 * 4 / 3))
    print("night", d0, d1, p0, p1)
    return {"d": [d0, d1], "p": [p0, p1], "date": "2025-09-23"}


if __name__ == "__main__":
    args = sys.argv[1:]
    OUT = args[args.index("--out") + 1] if "--out" in args else os.path.join(WEB_PUBLIC, "data")
    only = [a for a in args if a in NAMES] or list(NAMES)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "meta.json")
    meta = json.load(open(path)) if os.path.exists(path) else {}
    for name in only:
        meta[name] = globals()[name](OUT)
    json.dump(meta, open(path, "w"))
    print("wrote", OUT, "·", ", ".join(only))
