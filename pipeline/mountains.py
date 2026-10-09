"""Japan's next highest peaks after Fuji, in two views drawn with fuji_ridges.py: the range as layered
skylines (contour rings, tried first, pile into solid bands on ground this steep), and ridge lines
close up as for Fuji. Both
are seen from the east, as the Southern and Northern Alps are best known, with their twin peaks
beside them.

Data: Copernicus DEM GLO-30 (30 m), tiles from the AWS open data bucket, in dl/copdem/. The tiles use
a floating-point predictor that tifffile only decodes with imagecodecs, so they are rewritten
uncompressed once with GDAL:

    gdal_translate -co COMPRESS=NONE <tile>.tif <tile>_raw.tif

Pixel centres are at (lon0 + j / 3600, lat0 + 1 - i / 3600). A 30 m grid rounds the sharpest
summits off (Yari-ga-take reads 3,105 m), so the labels give the official GSI heights.

    python mountains.py               # both peaks, both views, desktop and phone, into out/
    python mountains.py kitadake      # one of them
"""
import sys
from types import SimpleNamespace
import numpy as np
import tifffile
from scipy.ndimage import gaussian_filter
import fuji as F
from common import dl, DESKTOP, PHONE

HALF = 0.2                                              # window around the summit, degrees
PEAKS = {
    # the Southern Alps' highest, with Aino-dake 3 km south: Japan's 2nd and 3rd= highest summits
    "kitadake": dict(tile="N35_00_E138_00", jp="北岳", en="Kita-dake", height=3193, summit=(138.23889, 35.67417),
                     labels=[(138.22833, 35.64583, "間ノ岳  Aino-dake, 3,190 m")]),
    # the Northern Alps' highest, with Yari-ga-take's spire 6 km north
    "hotaka": dict(tile="N36_00_E137_00", jp="奥穂高岳", en="Oku-hotaka-dake", height=3190, summit=(137.64778, 36.28944),
                   labels=[(137.64722, 36.34194, "槍ヶ岳  Yari-ga-take, 3,180 m")]),
}


def load(name):
    p = PEAKS[name]
    a = tifffile.imread(dl("copdem", f"Copernicus_DSM_COG_10_{p['tile']}_DEM_raw.tif"))
    r = 1 / 3600
    lon_t, lat_t = int(p["tile"][8:11]), int(p["tile"][1:3]) + 1
    lo, la = p["summit"]
    i0, i1 = round((lat_t - la - HALF) / r), round((lat_t - la + HALF) / r)
    j0, j1 = round((lo - HALF - lon_t) / r), round((lo + HALF - lon_t) / r)
    dem = a[i0:i1 + 1, j0:j1 + 1].astype(np.float32)
    smooth = gaussian_filter(dem, 0.8)
    return SimpleNamespace(name=name, jp=p["jp"], en=p["en"], height=p["height"], labels=p["labels"],
                           dem=dem, smooth=smooth, LON0=lon_t + j0 * r, LAT0=lat_t - i0 * r, RES=r,
                           SUMMIT=p["summit"], ecolor=F.ecolor, RAMP=F.RAMP)


# both peaks from the east (az -90, a little turned for Kita-dake so Aino-dake stands clear).
# Side: the range as layered skylines, widely spaced profiles from a low camera 30 km out.
# Ridges: close up, the lines starting just in front of the summit's east face (Kita-dake's
# buttress, Hotaka's Karasawa cirque), light falling off away from the summit (spot, km).
def _views(az):
    return {
        "side": {"desktop": dict(near=-9, far=14, step=0.5, half=10, spot=8, w=1.9,
                                 cam=dict(dist=30, cam_h=3.6, az_deg=az, target_h=2.6, fov_deg=21, y_frac=0.56)),
                 "phone": dict(near=-7, far=12, step=0.4, half=6, spot=6, w=1.9,
                               cam=dict(dist=26, cam_h=3.8, az_deg=az, target_h=2.85, fov_deg=12, y_frac=0.52))},
        "ridges": {"desktop": dict(near=-2.5, far=6.5, step=0.167, half=6.5, spot=4.5,
                                   cam=dict(dist=17, cam_h=6.6, az_deg=az, target_h=2.4, fov_deg=33, y_frac=0.45)),
                   "phone": dict(near=-2.5, far=5.5, step=0.134, half=4.2, spot=3.5,
                                 cam=dict(dist=15, cam_h=6.2, az_deg=az, target_h=2.6, fov_deg=24, y_frac=0.50))},
    }


VIEWS = {"kitadake": _views(-80), "hotaka": _views(-95)}
VIEWS["hotaka"]["side"]["desktop"]["cam"]["fov_deg"] = 27      # wide enough for Yari-ga-take, 6 km north
VIEWS["hotaka"]["side"]["desktop"]["half"] = 13


if __name__ == "__main__":
    import fuji_ridges
    for n in [a for a in sys.argv[1:] if not a.startswith("--")] or list(PEAKS):
        M = load(n)
        print(n, f"model summit {np.nanmax(M.smooth):.0f} m")
        for (W, H), kind in ((DESKTOP, "desktop"), (PHONE, "phone")):
            v = VIEWS[n]["side"][kind]
            fuji_ridges.render(W, H, f"out/{n}_side_{kind}.png", M, v,
                               text=f"{M.jp}  {M.en} from the east, {M.height:,} m  ·  the range as layered skylines, "
                                    f"one every {v['step'] * 1000:.0f} m, true vertical scale  ·  Copernicus DEM, 30 m")
            fuji_ridges.render(W, H, f"out/{n}_ridges_{kind}.png", M, VIEWS[n]["ridges"][kind])
