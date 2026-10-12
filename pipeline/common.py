"""Shared helpers for the Hikari Atlas wallpapers: additive light on pure black.

Everything is accumulated into a float RGB buffer (light adds up, never paints over),
blurred into a soft core + wide glow, tone-mapped with 1 - exp(-x) and saved as PNG
with every unlit pixel forced to exactly #000000.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter

DESKTOP, PHONE = (3840, 2160), (1290, 2796)

HERE = os.path.dirname(os.path.abspath(__file__))
# raw downloaded datasets (see README, "Data"); pipeline/dl/ by default, or set HIKARI_DL
DL = os.environ.get("HIKARI_DL", os.path.join(HERE, "dl"))
# the website's public folder, where export_web.py and export_particles.py write by default
WEB_PUBLIC = os.path.join(HERE, "..", "public")


def dl(*parts):
    return os.path.join(DL, *parts)


def _font(*c):
    p = next((p for p in c if os.path.exists(p)), None)
    if p is None:
        raise FileNotFoundError("no CJK font found for captions; install Noto Sans CJK or add a path in common.py: "
                                + ", ".join(c))
    return p

F_LIGHT = _font("/usr/share/fonts/opentype/noto/NotoSansCJK-Light.ttc",
                "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc")
F_REG = _font("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
              "/System/Library/Fonts/ヒラギノ角ゴシック W5.ttc")


class Canvas:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.buf = np.zeros((H, W, 3), np.float32)

    @property
    def phone(self):
        return self.H > self.W

    def add_points(self, x, y, rgb, w=1.0):
        """Bilinear (sub-pixel) additive deposit of N points. rgb: (N,3) or (3,)"""
        x = np.asarray(x, np.float32); y = np.asarray(y, np.float32)
        rgb = np.broadcast_to(np.asarray(rgb, np.float32), (len(x), 3))
        w = np.broadcast_to(np.asarray(w, np.float32), (len(x),))
        x0 = np.floor(x).astype(np.int64); y0 = np.floor(y).astype(np.int64)
        fx, fy = x - x0, y - y0
        for dx, dy, ww in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)),
                           (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            xi, yi = x0 + dx, y0 + dy
            ok = (xi >= 0) & (xi < self.W) & (yi >= 0) & (yi < self.H)
            for c in range(3):
                np.add.at(self.buf[..., c], (yi[ok], xi[ok]), (rgb[ok, c] * w[ok] * ww[ok]))

    def add_polyline(self, x, y, rgb, w=1.0, step=0.6):
        """Densify a polyline into samples every `step` px (colour/weight interpolated)."""
        x = np.asarray(x, np.float32); y = np.asarray(y, np.float32)
        if len(x) < 2:
            return
        rgb = np.broadcast_to(np.asarray(rgb, np.float32), (len(x), 3))
        w = np.broadcast_to(np.asarray(w, np.float32), (len(x),))
        seg = np.hypot(np.diff(x), np.diff(y))
        n = np.maximum(1, np.ceil(seg / step).astype(int))
        idx = np.repeat(np.arange(len(seg)), n)
        t = np.concatenate([np.arange(k) / k for k in n]).astype(np.float32)
        X = x[idx] + (x[idx + 1] - x[idx]) * t
        Y = y[idx] + (y[idx + 1] - y[idx]) * t
        C = rgb[idx] + (rgb[idx + 1] - rgb[idx]) * t[:, None]
        Wt = (w[idx] + (w[idx + 1] - w[idx]) * t) * step   # constant brightness per px length
        self.add_points(X, Y, C, Wt)

    def finish(self, core=0.8, glow=5.0, glow_amt=0.35, gain=1.0, gamma=0.85, black=6e-3):
        b = self.buf
        out = np.empty_like(b)
        for c in range(3):
            out[..., c] = gaussian_filter(b[..., c], core) + glow_amt * gaussian_filter(b[..., c], glow)
        img = np.clip(1.0 - np.exp(-out * gain), 0, 1) ** gamma
        arr = (img * 255 + 0.5).astype(np.uint8)
        arr[out.max(-1) * gain < black] = 0          # guaranteed true black
        return Image.fromarray(arr)


def caption(im, title, desc="", ramp=None, phone=None):
    """Bottom-left: a short title, and under it a smaller dim line saying what the picture is, led by
    an optional thin colour bar (list of rgb 0..1). The description wraps onto more lines rather than
    run past the strip export_particles.py blanks, and a soft halo dims the light under the words so
    they read over any picture."""
    W, H = im.size
    phone = H > W if phone is None else phone
    u = H / 2160 if not phone else W / 1290 * 0.9
    ft = ImageFont.truetype(F_LIGHT, int(40 * u))
    fd = ImageFont.truetype(F_LIGHT, int(23 * u))
    x = int(W * (0.06 if phone else 0.025))
    y = int(H - (150 * u if phone else 60 * u))          # the last line's middle, clear of a phone's home bar
    lw, lh = int(70 * u), max(2, int(3 * u))
    tx = x + lw + 14 * u if ramp is not None else x
    limit = W * (0.8 if phone else 0.6) - tx              # what export_particles.py blanks
    rows = []
    # too long for one line: break first before the source (after the last "  ·  "), then between words
    parts = desc.rsplit("  ·  ", 1) if desc and fd.getlength(desc) > limit else [desc] if desc else []
    for part in parts:
        rows.append("")
        for word in part.split(" "):
            if rows[-1] and fd.getlength(rows[-1] + " " + word) > limit:
                rows.append("")
            rows[-1] += (" " if rows[-1] else "") + word
    step = 30 * u
    first = y - step * (len(rows) - 1)                    # the first description line's middle
    ty = first - 26 * u if rows or ramp is not None else y + 12 * u
    lines = [((x, ty), title, ft, (170, 170, 170), "ls")]
    lines += [((tx, first + i * step), r, fd, (110, 110, 110), "lm") for i, r in enumerate(rows)]

    mask = Image.new("L", im.size, 0)                    # the halo: the words' shapes, grown and blurred
    md = ImageDraw.Draw(mask)
    for pos, text, f, _, anchor in lines:
        md.text(pos, text, font=f, fill=255, anchor=anchor, stroke_width=int(10 * u), stroke_fill=255)
    if ramp is not None:
        md.rectangle([x, first - 4 * lh, x + lw, first + 4 * lh], fill=255)
    m = gaussian_filter(np.asarray(mask, np.float32) / 255, 14 * u)
    a = np.asarray(im.convert("RGB"), np.float32) * (1 - np.clip(m * 1.8, 0, 0.94))[..., None]
    im.paste(Image.fromarray((a + 0.5).astype(np.uint8)))

    d = ImageDraw.Draw(im)
    if ramp is not None:
        ramp = np.asarray(ramp, np.float32)
        for i in range(lw):
            p = i / max(1, lw - 1) * (len(ramp) - 1)
            k, t = int(p), p - int(p)
            c = ramp[k] * (1 - t) + ramp[min(k + 1, len(ramp) - 1)] * t
            d.line([(x + i, first - lh // 2), (x + i, first - lh // 2 + lh)], fill=tuple(int(v * 255 * 0.6) for v in c))
    for pos, text, f, fill, anchor in lines:
        d.text(pos, text, font=f, fill=fill, anchor=anchor)


def save(im, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, optimize=True)
    a = np.asarray(im)
    print(f"{path}: black={(a.max(-1) == 0).mean():.1%}")


class EquiProj:
    """lon/lat -> pixels, equirectangular with cos(lat0) scaling, fit a box into the canvas."""
    def __init__(self, W, H, lon0, lon1, lat0, lat1, margin=0.02, mode="fit"):
        self.k = np.cos(np.radians((lat0 + lat1) / 2))
        bw, bh = (lon1 - lon0) * self.k, lat1 - lat0
        sx, sy = W * (1 - 2 * margin) / bw, H * (1 - 2 * margin) / bh
        self.s = min(sx, sy) if mode == "fit" else max(sx, sy)   # "fill" crops
        self.cx, self.cy = (lon0 + lon1) / 2, (lat0 + lat1) / 2
        self.W, self.H = W, H

    def __call__(self, lon, lat):
        return (self.W / 2 + (np.asarray(lon) - self.cx) * self.k * self.s,
                self.H / 2 - (np.asarray(lat) - self.cy) * self.s)


def flower_sprite(r, rot=0.0, petals=5):
    """Soft five-petal blossom of radius r px (float alpha map), notched petal tips."""
    n = int(np.ceil(r * 1.3)) * 2 + 1
    yy, xx = np.mgrid[:n, :n] - n // 2
    ang = np.arctan2(yy, xx) + rot
    rad = np.hypot(xx, yy) / r
    k = petals * ang / 2
    petal = np.abs(np.cos(k))                        # petal lobes
    notch = 1 - 0.25 * np.exp(-((np.abs(np.sin(k * 2))) / 0.15) ** 2) * (rad > 0.6)
    edge = petal ** 0.6 * notch
    a = np.clip((edge - rad) * 3.0, 0, 1)            # soft edge
    a += 0.6 * np.exp(-(rad / 0.18) ** 2)            # bright centre
    return a.astype(np.float32)


def add_sprite(canvas, x, y, sprite, rgb, w=1.0):
    h = sprite.shape[0] // 2
    xi, yi = int(round(x)), int(round(y))
    x0, x1 = max(xi - h, 0), min(xi + h + 1, canvas.W)
    y0, y1 = max(yi - h, 0), min(yi + h + 1, canvas.H)
    if x0 >= x1 or y0 >= y1:
        return
    s = sprite[y0 - (yi - h):y1 - (yi - h), x0 - (xi - h):x1 - (xi - h)]
    canvas.buf[y0:y1, x0:x1] += (s * w)[..., None] * np.asarray(rgb, np.float32)
