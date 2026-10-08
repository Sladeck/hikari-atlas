"""Every typhoon tracked by the Japan Meteorological Agency, from 1951 to the last complete season.

Data: JMA RSMC Tokyo best track (bst_all.txt). One header line per storm (66666 ...),
then 6-hourly rows: YYMMDDHH 002 grade lat*10 lon*10 pressure(hPa) [wind kt].
Colour and brightness follow central pressure: lower pressure = stronger storm = whiter.
"""
import sys
import numpy as np
from common import Canvas, caption, save, EquiProj, dl, DESKTOP, PHONE

BST = dl("Typhoon-Search", "bst_all.txt")
LAST = 2025                      # last complete season in the file (the current one is still being added)
SRC = sys.argv[1] if __name__ == "__main__" and len(sys.argv) > 1 else BST


def load(path):
    storms, cur = [], None
    for line in open(path):
        if line.startswith("66666"):
            cur = []
            storms.append(cur)
            continue
        p = line.split()
        if len(p) < 6 or cur is None:
            continue
        yy = int(p[0][:2]); year = 1900 + yy if yy > 50 else 2000 + yy
        grade, lat, lon, pres = int(p[2]), int(p[3]) / 10, int(p[4]) / 10, int(p[5])
        cur.append((year, grade, lon, lat, pres))
    return [np.array(s, float) for s in storms if len(s) > 1]


# central pressure (hPa) -> colour: weak = dim slate blue, strong = ice white
RAMP_P = [(1006, (0.05, 0.22, 0.95)), (985, (0.00, 0.55, 1.00)), (960, (0.10, 0.90, 1.00)),
          (935, (0.70, 1.00, 1.00)), (905, (1.00, 1.00, 1.00))]
RAMP = [c for _, c in RAMP_P]


def pcolor(p):
    ks = np.array([k for k, _ in RAMP_P])[::-1]; cs = np.array([c for _, c in RAMP_P])[::-1]
    return np.stack([np.interp(p, ks, cs[:, i]) for i in range(3)], -1)


def render(storms, W, H, out, strong_k=4.5, weak_k=8.0, core=1.1, gain=3.5):
    phone = H > W
    box = (112, 166, 6, 52) if phone else (100, 178, 4, 52)
    P = EquiProj(W, H, *box, margin=0.0, mode="fill")
    cv = Canvas(W, H)
    z = min(W, H) / 2160
    k = 1.1 if phone else 1.0                                   # phone lines a little heavier (smaller screen)
    n_strong = 0
    for s in storms:
        x, y = P(s[:, 2], s[:, 3])
        pres, grade = s[:, 4], s[:, 1]
        col = pcolor(pres)
        col[grade == 6] *= np.array([0.5, 0.45, 0.8])           # extratropical tail: faded violet
        strong = pres.min() <= 930                               # a violent typhoon at its peak
        n_strong += strong
        if strong:   # bright line, brightest near the peak
            w = strong_k * k * 0.034 * (0.3 + np.clip((1000 - pres) / 60, 0, 1.6) ** 1.6)
        else:        # faint background haze of every other storm
            w = np.full(len(pres), weak_k * k * 0.0024)
        w = np.where(grade == 6, w * 0.3, w)
        cv.add_polyline(x, y, col, w)
    im = cv.finish(core=core * max(1, z), glow=4 * z, glow_amt=0.3, gain=gain, black=1.6e-2)
    yrs = (int(min(s[0, 0] for s in storms)), int(max(s[0, 0] for s in storms)))
    caption(im, f"台風  Typhoons of the Northwest Pacific  ·  {len(storms):,} storms, "
                f"{n_strong} below 930 hPa highlighted  ·  {yrs[0]}–{yrs[1]}  ·  JMA best track", ramp=RAMP)
    save(im, out)


if __name__ == "__main__":
    storms = [s for s in load(SRC) if s[0, 0] <= LAST]
    print(len(storms), "storms")
    render(storms, *DESKTOP, "out/typhoons_desktop.png")
    render(storms, *PHONE, "out/typhoons_phone.png")
