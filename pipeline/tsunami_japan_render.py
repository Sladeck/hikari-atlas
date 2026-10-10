"""The chapter animation: the 2011 tsunami striking Japan, from tsunami_japan.py's simulation.

About 12 s of video. A close-up on Tōhoku while the wave leaves the trench and strikes the coast
(0-70 min), a zoom out (70-100 min), then Japan's whole Pacific coast to 3 h as the wave reaches
Hokkaido, Tokyo, Shikoku and Amami. Japan is the lit land; its shoreline turns from warm to white
where the wave has struck, as bright as the highest wave beside it so far.

Writes public/video/tsunami.{webm,mp4}, the poster, and public/data/tsunami_marks.json: the sim time
and camera of every video frame, and the places the website labels (TsunamiVideo.vue) with their
simulated first arrival.

    python tsunami_japan_render.py [--info | --preview [frame numbers]]
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter, maximum_filter
from common import WEB_PUBLIC
from japan_land import land_mask, light_japan

S = np.load("out/tsunami_japan.npz")
lon, lat, wet, emax, arrival, times = S["lon"], S["lat"], S["wet"], S["emax"], S["arrival"], S["times"]
F = np.load("out/tsunami_japan_frames.npy", mmap_mode="r")
FRAME_S = float(times[1] - times[0])

W, H, FPS = 1280, 720, 24
K = np.cos(np.radians(37.0))                         # one x scale for every frame, so shapes hold while zooming
EPI = (142.860, 38.103)                              # JMA epicentre, 14:46 JST, M9.0

# video frame -> simulated minutes: slow over the impact, faster once the wave spreads along the coast
TIME = [(0, 0.0), (150, 70.0), (200, 100.0), (287, 180.0)]
# camera keyframes: sim minute -> centre lon, lat, and the frame's height in degrees of latitude
CAM = [(0, 142.2, 38.6, 6.4), (70, 142.2, 38.6, 6.4), (100, 136.5, 35.2, 21.6), (180, 136.5, 35.2, 21.6)]

# where the wave reached the coast, named on the video when it arrives (lon, lat on the shore);
# NEAR: the close-up's places, too close together to name once the camera has zoomed out
NEAR = {"miyako", "sendai", "fukushima"}
PLACES = [
    ("miyako", 141.97, 39.64),        # Miyako, Iwate: the Sanriku coast
    ("sendai", 141.02, 38.27),        # Sendai port
    ("fukushima", 141.03, 37.42),     # Fukushima Daiichi
    ("tokyo", 139.77, 35.62),         # Tokyo Bay
    ("kushiro", 144.37, 42.98),       # Kushiro, Hokkaido
    ("kochi", 133.55, 33.50),         # Kōchi, Shikoku
    ("amami", 129.50, 28.38),         # Naze, Amami Ōshima (Okinawa sees almost nothing within 3 h)
]

# the wave as light: deep blue troughs, aqua to white crests
STOPS = [(0.0, (0.0, 0.0, 0.0)), (0.12, (0.01, 0.04, 0.16)), (0.35, (0.00, 0.25, 0.50)),
         (0.60, (0.00, 0.70, 0.80)), (0.85, (0.55, 0.95, 1.00)), (1.0, (1.0, 1.0, 1.0))]


def cmap(t):
    t = np.clip(t, 0, 1)
    ks = np.array([k for k, _ in STOPS]); cs = np.array([c for _, c in STOPS])
    return np.stack([np.interp(t, ks, cs[:, i]) for i in range(3)], -1)


def level(a, lo=0.02, hi=8.0):
    """log scale: 2 cm -> 0, 8 m -> 1"""
    return np.clip(np.log10(np.maximum(a, 1e-5) / lo) / np.log10(hi / lo), 0, 1)


def smooth(u):
    return u * u * (3 - 2 * u)


def sim_minutes(i):
    xs, ys = zip(*TIME)
    return float(np.interp(i, xs, ys))


def camera(m):
    """lon, lat, height at sim minute m: the centre eases across, the zoom is geometric."""
    for (m0, *a), (m1, *b) in zip(CAM, CAM[1:]):
        if m0 <= m <= m1:
            u = smooth((m - m0) / (m1 - m0)) if m1 > m0 else 0
            lo = a[0] + (b[0] - a[0]) * u; la = a[1] + (b[1] - a[1]) * u
            return lo, la, a[2] * (b[2] / a[2]) ** u
    return CAM[-1][1:]


def box(cam):
    """lon0, lon1, lat0, lat1 of the frame for a camera."""
    lo, la, hgt = cam
    wdeg = hgt * W / H / K
    return lo - wdeg / 2, lo + wdeg / 2, la - hgt / 2, la + hgt / 2


def proj(cam):
    lon0, lon1, lat0, lat1 = box(cam)
    return lambda x, y: ((np.asarray(x) - lon0) / (lon1 - lon0) * W, (lat1 - np.asarray(y)) / (lat1 - lat0) * H)


def sampler(cam):
    """Grid indices for every pixel of the frame, and a mask of the pixels inside the simulated area."""
    lon0, lon1, lat0, lat1 = box(cam)
    xs = lon0 + (np.arange(W) + 0.5) / W * (lon1 - lon0)
    ys = lat1 - (np.arange(H) + 0.5) / H * (lat1 - lat0)
    gi = np.broadcast_to(((ys - lat[0]) / (lat[1] - lat[0]))[:, None], (H, W))
    gj = np.broadcast_to(((xs - lon[0]) / (lon[1] - lon[0]))[None, :], (H, W))
    # fade the wave over the last 2.5 degrees inside the simulated area: past its edge there is no data
    dx = np.minimum(xs - lon[0], lon[-1] - xs)[None, :]; dy = np.minimum(ys - lat[0], lat[-1] - ys)[:, None]
    fade = np.clip(np.minimum(dx, dy) / 2.5, 0, 1) ** 1.5
    return np.stack([gi, gj]), fade


def eta_at(m):
    """The sea surface at sim minute m, between the two stored frames around it."""
    p = m * 60 / FRAME_S
    i = min(int(p), len(F) - 2); u = p - i
    return F[i].astype(np.float32) * (1 - u) + F[i + 1].astype(np.float32) * u


def arrival_at(lo, la, crest=0.05):
    """Simulated first arrival (minutes) at the sea cell nearest a place on the shore: the first crest
    above 5 cm. (The source's landward drop already lowers the sea off Sanriku at the first instant,
    so a bare threshold on |eta| would call that the wave.)"""
    J, I = np.where(wet)
    d = ((lon[I] - lo) * np.cos(np.radians(la))) ** 2 + (lat[J] - la) ** 2
    k = np.argmin(d)
    series = F[:, J[k], I[k]].astype(np.float32)
    first = np.argmax(series > crest)
    return float(first * FRAME_S / 60) if series[first] > crest else float("nan")


def frame(m, runmax):
    """One video frame at sim minute m; runmax is the highest wave so far on the grid."""
    cam = camera(m)
    idx, fade = sampler(cam)
    z = (H / 720) * (6.4 / cam[2]) ** 0.35                       # the shore thins a little as the view widens
    a = map_coordinates(gaussian_filter(eta_at(m), 0.8), idx, order=1, mode="constant") * fade
    rm = map_coordinates(runmax, idx, order=1, mode="constant") * fade
    crest = level(np.maximum(a, 0)) ** 1.2; trough = level(np.maximum(-a, 0)) ** 1.2 * 0.4
    img = np.maximum(cmap(np.maximum(crest, trough)), 0.10 * cmap(level(rm) ** 2))
    # Japan: its shore whitens where the wave has struck, by the highest wave beside it so far
    jp = land_mask(W, H, proj(cam), ss=2)
    hit = level(maximum_filter(rm, size=5), lo=0.5, hi=15.0)[..., None]
    shore_rgb = np.array([1.00, 0.81, 0.54]) * (1 - hit) + np.array([0.85, 1.00, 1.00]) * hit
    img = light_japan(img, jp, z=z, rgb=shore_rgb, fill=0.035)
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)), cam


def runmax_until(m):
    rm = np.zeros(F.shape[1:], np.float32)
    for k in range(int(m * 60 / FRAME_S) + 1):
        np.maximum(rm, np.abs(F[k].astype(np.float32)), out=rm)
    return rm


def preview(frames, path):
    """A contact sheet of a few video frames, to tune the look without encoding."""
    ims = [frame(sim_minutes(i), runmax_until(sim_minutes(i)))[0].resize((W // 2, H // 2)) for i in frames]
    sheet = Image.new("RGB", (W, H // 2 * ((len(ims) + 1) // 2)))
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % 2) * W // 2, (k // 2) * H // 2))
    sheet.save(path)
    print(path)


def render():
    os.makedirs("out/japan_frames", exist_ok=True)
    runmax = np.zeros(F.shape[1:], np.float32)
    last = -1
    cams, mins = [], []
    for i in range(TIME[-1][0] + 1):
        m = sim_minutes(i)
        # the highest wave so far, from every stored frame passed since the last video frame
        upto = int(m * 60 / FRAME_S)
        for k in range(last + 1, upto + 1):
            np.maximum(runmax, np.abs(F[k].astype(np.float32)), out=runmax)
        last = max(last, upto)
        im, cam = frame(m, runmax)
        cams.append([round(v, 4) for v in box(cam)]); mins.append(round(m, 2))
        im.save(f"out/japan_frames/{i:04d}.png")
        if i == 60:                                              # the poster: 28 min, the wave striking Sanriku
            im.save(os.path.join(WEB_PUBLIC, "video", "tsunami_poster.webp"), "WEBP", quality=85, method=6)
        if i % 48 == 0:
            print(f"  frame {i}  t={m:.0f} min", flush=True)
    out = os.path.join(WEB_PUBLIC, "video", "tsunami.webm")
    src = ["-framerate", str(FPS), "-i", "out/japan_frames/%04d.png"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *src, "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "36",
                    "-pix_fmt", "yuv420p", out], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *src, "-c:v", "libx264", "-crf", "26", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", out.replace(".webm", ".mp4")], check=True)
    print(out, os.path.getsize(out) // 1024, "KB")
    marks = {"fps": FPS, "minutes": mins, "box": cams, "epicentre": list(EPI),
             "places": [{"key": k, "at": [lo, la], "minutes": round(arrival_at(lo, la)), "near": k in NEAR} for k, lo, la in PLACES]}
    path = os.path.join(WEB_PUBLIC, "data", "tsunami_marks.json")
    with open(path, "w") as fh:
        json.dump(marks, fh, separators=(",", ":"))
    print(path, os.path.getsize(path) // 1024, "KB")


if __name__ == "__main__":
    if "--info" in sys.argv:
        for k, lo, la in PLACES:
            print(f"{k:10s} first wave {arrival_at(lo, la):5.0f} min after the earthquake (simulated)")
        print(f"highest wave in the simulated area: {np.nanmax(emax):.1f} m")
        sys.exit()
    if "--preview" in sys.argv:                               # python tsunami_japan_render.py --preview 10 60 150
        preview([int(a) for a in sys.argv[2:] if a.isdigit()] or [10, 60, 100, 150, 200, 287], "out/tsunami_japan_preview.png")
        sys.exit()
    render()
