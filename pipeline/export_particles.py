"""Turn the wallpapers into particle scenes for the WebGL front page.

Flat scenes: importance-sample N pixels from a render, with probability ~ brightness^gamma,
so every scene IS its wallpaper rebuilt from points of light (position + colour + brightness).
Fuji: real 3D points along the 10 m contour rings (x, y east/north, z elevation), coloured by
height, so the browser can turn the mountain.

File format per scene (little endian, N records of 8 bytes):
  uint16 x, uint16 y, uint16 z  (0..65535 -> -1..1; z = 32768 for flat scenes)
  uint8  colour index into a 256-entry palette? no: packed RGB565 would lose too much,
so instead: x,y,z as above (6 bytes) + uint8 r, g, b, a (4 bytes) = 10 bytes per point.
"""
import json, os, sys
import numpy as np
from PIL import Image

# usage: python export_particles.py [scene ...] [--out DIR]   (no scene names = all scenes)
ARGS = sys.argv[1:]
OUT = ARGS[ARGS.index("--out") + 1] if "--out" in ARGS else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "particles")
os.makedirs(OUT, exist_ok=True)
SETS = {"d": ("desktop", 36000), "p": ("phone", 22000)}
SCENES = ["japan", "tsunami", "typhoons", "fuji3d", "sakura", "trains_tokyo"]
ONLY = [a for a in ARGS if a in SCENES] or SCENES
rng = np.random.default_rng(7)


def q16(v):
    return np.clip(np.round((np.asarray(v) * 0.5 + 0.5) * 65535), 0, 65535).astype(np.uint16)


def write(name, x, y, z, rgb, a):
    rec = np.zeros(len(x), dtype=[("x", "<u2"), ("y", "<u2"), ("z", "<u2"), ("r", "u1"), ("g", "u1"), ("b", "u1"), ("a", "u1")])
    rec["x"], rec["y"], rec["z"] = q16(x), q16(y), q16(z)
    rgb = np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)
    rec["r"], rec["g"], rec["b"] = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    rec["a"] = np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
    rec.tofile(f"{OUT}/{name}.bin")
    return os.path.getsize(f"{OUT}/{name}.bin")


def from_render(img, kind, n, gamma=1.35):
    im = np.asarray(Image.open(f"out/{img}_{kind}.png").convert("RGB"), np.float32) / 255
    H, W, _ = im.shape
    # drop the caption strip and a thin border
    lum = im.max(-1)
    lum[int(H * (0.93 if kind == "desktop" else 0.90)):, : int(W * 0.6)] = 0
    lum[:, :2] = lum[:, -2:] = 0
    # sample on a 2x downscaled grid to keep it fast, then jitter inside the cell
    s = 2
    l2 = lum[: H // s * s, : W // s * s].reshape(H // s, s, W // s, s).mean((1, 3))
    c2 = im[: H // s * s, : W // s * s].reshape(H // s, s, W // s, s, 3).mean((1, 3))
    w = l2.ravel() ** gamma
    w[l2.ravel() < 0.02] = 0
    idx = rng.choice(len(w), size=n, replace=True, p=w / w.sum())
    yy, xx = np.divmod(idx, l2.shape[1])
    jx, jy = rng.random(n), rng.random(n)
    x = (xx + jx) * s / W * 2 - 1                    # -1..1 across the frame
    y = 1 - (yy + jy) * s / H * 2                    # +1 at the top
    col = c2.reshape(-1, 3)[idx]
    mx = np.maximum(col.max(-1, keepdims=True), 1e-3)
    rgb = col / mx                                   # pure hue at full value
    raw = l2.ravel()[idx]
    a = np.clip(raw / np.percentile(raw, 92), 0, 1) ** 0.75   # per-scene normalised brightness
    return x, y, np.zeros(n), rgb, a


def fuji3d(n):
    import fuji as F
    KM, k = 111.32, np.cos(np.radians(F.SUMMIT[1]))
    pts, cols = [], []
    for lev, c in F.CONTOURS:
        if lev < 1000:
            continue
        lon = F.LON0 + c[:, 1] * F.RES; lat = F.LAT0 - c[:, 0] * F.RES
        x = (lon - F.SUMMIT[0]) * KM * k; y = (lat - F.SUMMIT[1]) * KM
        keep = np.hypot(x, y) < 13.5
        if keep.sum() < 3:
            continue
        pts.append(np.stack([x[keep], y[keep], np.full(keep.sum(), lev / 1000.0)], 1))
    P = np.concatenate(pts)
    # more points high up (where the rings are short) so the cone reads, fewer on the wide base
    w = 0.25 + (P[:, 2] / 3.776) ** 1.5
    idx = rng.choice(len(P), size=n, replace=True, p=w / w.sum())
    P = P[idx] + rng.normal(0, 0.012, (n, 3)) * [1, 1, 0]
    rgb = F.ecolor(P[:, 2] * 1000)
    a = 0.35 + 0.65 * (P[:, 2] / 3.776)
    # normalise: x, y by 13.5 km, z centred so the cone sits around the origin
    return P[:, 0] / 13.5, P[:, 1] / 13.5, (P[:, 2] - 1.9) / 13.5 * 2.0, rgb, a


meta = {"scenes": SCENES, "sets": {}}
for key, (kind, n) in SETS.items():
    total = 0
    for sc in ONLY:
        x, y, z, rgb, a = fuji3d(n) if sc == "fuji3d" else from_render(sc, kind, n)
        total += write(f"{sc}_{key}", x, y, z, rgb, a)
    meta["sets"][key] = {"n": n, "aspect": 3840 / 2160 if key == "d" else 1290 / 2796}
    print(kind, n, "points/scene,", total // 1024, "KB total")
json.dump(meta, open(f"{OUT}/meta.json", "w"))
