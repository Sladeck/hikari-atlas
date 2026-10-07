"""Render the tsunami simulation: max wave height (log) + hourly arrival-time rings,
and the animation frames as a WebM for the website."""
import os, subprocess
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import map_coordinates, gaussian_filter
from common import caption, save, DESKTOP, PHONE

S = np.load("out/tsunami_sim.npz")
emax, arrival, wet, lon, lat = S["emax"], S["arrival"], S["wet"], S["lon"], S["lat"]

# max height (m) -> colour: deep navy, teal, aqua, white
STOPS = [(0.00, (0.00, 0.00, 0.00)), (0.10, (0.00, 0.00, 0.00)), (0.25, (0.02, 0.07, 0.24)), (0.42, (0.00, 0.30, 0.55)),
         (0.60, (0.00, 0.70, 0.80)), (0.82, (0.55, 0.95, 1.00)), (1.00, (1.00, 1.00, 1.00))]
RAMP = [c for _, c in STOPS[2:]]


def cmap(t):
    t = np.clip(t, 0, 1)
    ks = np.array([k for k, _ in STOPS]); cs = np.array([c for _, c in STOPS])
    return np.stack([np.interp(t, ks, cs[:, i]) for i in range(3)], -1)


def sample(field, W, H, box, order=1):
    lon0, lon1, lat0, lat1 = box
    xs = np.linspace(lon0, lon1, W); ys = np.linspace(lat1, lat0, H)
    gi = (ys[:, None] - lat[0]) / (lat[1] - lat[0]) + 0 * xs[None, :]
    gj = (xs[None, :] - lon[0]) / (lon[1] - lon[0]) + 0 * ys[:, None]
    return map_coordinates(field, [gi, gj], order=order, mode="nearest")


def intensity(e):
    # log scale: 5 cm -> 0, ~4 m -> 1 ; gamma keeps the open ocean dark
    return np.clip(np.log10(np.maximum(e, 1e-4) / 0.05) / np.log10(80), 0, 1) ** 1.5


def render(W, H, out):
    phone = H > W
    box = (128, 172, -32, 60) if phone else (117, 287, -52, 62)
    t = intensity(sample(gaussian_filter(emax, 0.6), W, H, box))
    img = cmap(t ** 0.9)
    # arrival-time rings, every hour, faint
    arr = sample(np.nan_to_num(arrival, nan=99), W, H, box)
    z = min(W, H) / 2160
    ring = np.zeros((H, W), np.float32)
    for hr in range(1, 24):
        d = np.abs(arr - hr)
        ring = np.maximum(ring, np.clip(1 - d / (0.045 if not phone else 0.03), 0, 1))
    ring *= sample(wet.astype(np.float32), W, H, box) > 0.5
    img = np.maximum(img, ring[..., None] * np.array([0.10, 0.30, 0.34]) * 0.6)
    # coastline: the faintest grey edge of the land mask so the Pacific can be read
    land = sample((~wet).astype(np.float32), W, H, box)
    edge = np.clip(1 - np.abs(land - 0.5) * 4, 0, 1) * 0.16
    img = np.maximum(img, edge[..., None])
    arr8 = (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
    arr8[arr8.max(-1) < 4] = 0
    im = Image.fromarray(arr8)
    caption(im, "津波  Tōhoku tsunami, 11 March 2011  ·  highest wave in 24 h, simulated from the shallow-water "
                "equations on real ocean depth  ·  rings = hours", ramp=RAMP)
    save(im, out)


def video(out, W=1280, H=720, fps=24):
    os.makedirs("out/frames", exist_ok=True)
    box = (117, 287, -52, 62)
    fr = S["frames"].astype(np.float32)
    land = sample((~wet).astype(np.float32), W, H, box)
    edge = np.clip(1 - np.abs(land - 0.5) * 4, 0, 1) * 0.16
    runmax = np.zeros((H, W), np.float32)
    for i, e in enumerate(fr):
        a = sample(gaussian_filter(np.abs(e), 1.0), W, H, box)
        runmax = np.maximum(runmax, a)
        t = np.clip(np.log10(np.maximum(a, 1e-4) / 0.025) / np.log10(24), 0, 1)
        tr = np.clip(np.log10(np.maximum(runmax, 1e-4) / 0.02) / np.log10(150), 0, 1) ** 1.4
        img = np.maximum(np.maximum(cmap(0.12 + 0.88 * t) * (t > 0)[..., None], 0.5 * cmap(tr)), edge[..., None])
        Image.fromarray((img * 255 + 0.5).astype(np.uint8)).save(f"out/frames/{i:04d}.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", "out/frames/%04d.png",
                    "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "36", "-pix_fmt", "yuv420p", out], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", "out/frames/%04d.png",
                    "-c:v", "libx264", "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    out.replace(".webm", ".mp4")], check=True)
    print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    import sys
    if "--video-only" not in sys.argv:
        render(*DESKTOP, "out/tsunami_desktop.png")
        render(*PHONE, "out/tsunami_phone.png")
    import sys
    if "--video" in sys.argv: video("out/tsunami.webm")
