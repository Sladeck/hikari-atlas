"""Japan's land as light: the Natural Earth 1:10m polygons that belong to Japan, rasterised for any
projection, drawn as a warm lit shoreline over a dim fill (the tsunami renders).

Japan is picked by each polygon's centre: the Northern Territories in, Urup out (PRODUCT.md
principle 5), and the Korean, Chinese and Russian islands near its seas left out.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
from common import dl

JAPAN = np.array([1.00, 0.81, 0.54])                 # warm light, against the blue sea


def is_japan(a):
    """A land polygon that belongs to Japan, by its centre."""
    lo, la = a.mean(0)
    if not (122.5 < lo < 149.0 and 24 < la < 45.8):
        return False
    if lo < 127.5 and la > 32.5:                  # Jeju
        return False
    if lo < 129.15 and la > 33.7:                 # Korea's south coast islands (Tsushima lies east of this)
        return False
    if lo < 139.2 and la > 41.6:                  # the islands off Vladivostok
        return False
    if abs(lo - 130.87) < 0.3 and abs(la - 37.5) < 0.3:   # Ulleungdo
        return False
    if lo < 123.5 and la > 26:                    # China's Zhoushan islands
        return False
    return True


def japan_polys():
    g = json.load(open(dl("ne", "land10.geojson")))
    out = []
    for f in g["features"]:
        geo = f["geometry"]
        for p in ([geo["coordinates"]] if geo["type"] == "Polygon" else geo["coordinates"]):
            a = np.array(p[0])
            if a[:, 0].max() > 122 and a[:, 0].min() < 150 and is_japan(a):
                out.append(a)
    return out


JP = japan_polys()


def land_mask(W, H, proj, ss=3):
    """Japan's land as a soft 0..1 mask; proj(lon, lat) -> pixel x, y. Drawn supersampled."""
    im = Image.new("L", (W * ss, H * ss), 0)
    d = ImageDraw.Draw(im)
    for a in JP:
        x, y = proj(a[:, 0], a[:, 1])
        d.polygon(list(zip(np.asarray(x) * ss, np.asarray(y) * ss)), fill=255)
    return np.asarray(im.resize((W, H), Image.BOX), np.float32) / 255


def shoreline(jp, z=1.0):
    """The coast, about a pixel wide, thickened so small islands read; z scales to the frame."""
    shore = np.clip(1 - np.abs(jp - 0.5) * 2, 0, 1)
    return np.maximum(shore, gaussian_filter(shore, 1.2 * z) * 2.5)


def light_japan(img, jp, z=1.0, rgb=None, fill=0.12):
    """Japan as warm light: a lit shoreline with a soft glow, over a dim fill, laid over img.
    rgb: an optional per-pixel colour for the shore (H, W, 3), in place of the warm light.
    fill: the land's own light; a close view wants less, or the land reads as paint."""
    shore = shoreline(jp, z)
    glow = gaussian_filter(shore, 6 * z) * 1.6
    a = np.clip(jp * fill + shore * 0.95 + glow * 0.35, 0, 1)[..., None]
    col = JAPAN if rgb is None else rgb
    return np.maximum(img * (1 - jp[..., None]), col * a)
