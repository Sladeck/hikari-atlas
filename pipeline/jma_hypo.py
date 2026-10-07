"""Reader for the JMA unified hypocentre catalogue (地震月報 カタログ編, 震源データ).

One 96-byte fixed-width record per quake, with implied decimals (Fortran F-formats without a
point). Columns as documented in the JMA format page (data/format/hypfmt_j.html):
  1 record type (J = JMA), 2-5 year, 6-7 month, 8-9 day, 10-11 hour, 12-13 minute,
  14-17 second F4.2, 22-24 latitude deg, 25-28 latitude min F4.2, 33-36 longitude deg,
  37-40 longitude min F4.2, 45-49 depth km F5.2 (or I3 + 2 blanks when fixed),
  53-54 magnitude F2.1 (below zero: -1..-9 = -0.1..-0.9, A0..A9 = -1.0..-1.9, B0 = -2.0, ...).
Download yearly files from https://www.data.jma.go.jp/eqev/data/bulletin/hypo.html into dl/jma-hypo/.
"""
import numpy as np
import pandas as pd
from common import dl


def _num(field, dec):
    whole, frac = field[:len(field) - dec], field[len(field) - dec:]
    if not whole.strip() and not frac.strip():
        return np.nan
    return float(whole.strip() or 0) + (float(frac.replace(" ", "0")) / 10 ** dec if frac.strip() else 0.0)


def _mag(m):
    if not m.strip():
        return np.nan
    if m[0] == "-":
        return -int(m[1]) / 10
    if m[0].isalpha():                          # A0 = -1.0, B0 = -2.0, C0 = -3.0
        return -(ord(m[0]) - ord("A") + 1) - int(m[1]) / 10
    return int(m) / 10


def load(year):
    rows = []
    for line in open(dl("jma-hypo", f"h{year}"), encoding="ascii", errors="replace"):
        if line[0] != "J" or len(line) < 55:
            continue
        lat = _num(line[21:24], 0) + _num(line[24:28], 2) / 60
        lon = _num(line[32:36], 0) + _num(line[36:40], 2) / 60
        rows.append((int(line[1:5]), int(line[5:7]), int(line[7:9]), int(line[9:11]), int(line[11:13]),
                     _num(line[13:17], 2), lat, lon, _num(line[44:49], 2), _mag(line[52:54])))
    d = pd.DataFrame(rows, columns=["year", "month", "day", "hour", "minute", "sec", "lat", "lon", "depth", "mag"])
    d["sec"] = d.sec.fillna(0)
    d["time"] = pd.to_datetime(d[["year", "month", "day", "hour", "minute"]]) + pd.to_timedelta(d.sec, unit="s")
    return d.dropna(subset=["lat", "lon", "depth", "mag"])[["time", "lat", "lon", "depth", "mag"]].reset_index(drop=True)
