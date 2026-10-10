"""Render the tsunami simulation across the Pacific: max wave height (log) + hourly arrival-time rings.

Japan is drawn as the one lit land, so the Pacific has an anchor; the epicentre and the places the
wave reached are labelled with the simulated arrival time. The chapter's animation is the wave
striking Japan, from tsunami_japan.py and tsunami_japan_render.py.

    python tsunami_render.py [--info]
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import map_coordinates, gaussian_filter, binary_dilation
from common import caption, save, DESKTOP, PHONE, F_LIGHT
from japan_land import JP, land_mask, light_japan

S = np.load("out/tsunami_sim.npz")
emax, arrival, wet, lon, lat = S["emax"], S["arrival"], S["wet"], S["lon"], S["lat"]

# max height (m) -> colour: deep navy, teal, aqua, white
STOPS = [(0.00, (0.00, 0.00, 0.00)), (0.10, (0.00, 0.00, 0.00)), (0.25, (0.02, 0.07, 0.24)), (0.42, (0.00, 0.30, 0.55)),
         (0.60, (0.00, 0.70, 0.80)), (0.82, (0.55, 0.95, 1.00)), (1.00, (1.00, 1.00, 1.00))]
RAMP = [c for _, c in STOPS[2:]]

BOX = {"desktop": (117, 287, -52, 62), "phone": (128, 172, -32, 60)}   # lon0, lon1, lat0, lat1 (lon east, 0..360)
EPI = (142.860, 38.103)                                                 # JMA epicentre, 14:46 JST, M9.0
# where the wave reached land, by a harbour on that coast (lon east, 0..360)
PLACES = [
    ("hawaii", "ハワイ", "Hawaii", 202.14, 21.31),                       # Honolulu
    ("california", "カリフォルニア", "California", 235.80, 41.76),       # Crescent City
    ("newzealand", "ニュージーランド", "New Zealand", 178.02, -38.66),   # Gisborne
    ("peru", "ペルー", "Peru", 282.85, -12.05),                          # Callao
    ("guam", "グアム", "Guam", 144.65, 13.44),                            # Apra Harbor
]


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


def px(W, H, box, lo, la):
    """lon/lat -> pixel, matching sample()'s grid."""
    lon0, lon1, lat0, lat1 = box
    return (lo - lon0) / (lon1 - lon0) * (W - 1), (lat1 - la) / (lat1 - lat0) * (H - 1)


def intensity(e):
    # log scale: 5 cm -> 0, ~4 m -> 1 ; gamma keeps the open ocean dark
    return np.clip(np.log10(np.maximum(e, 1e-4) / 0.05) / np.log10(80), 0, 1) ** 1.5


def arrival_at(lo, la):
    """Simulated arrival (h) at the sea cell nearest a place: the first time the water moved 1 cm."""
    J, I = np.where(np.isfinite(arrival))
    d = ((lon[I] - lo) * np.cos(np.radians(la))) ** 2 + (lat[J] - la) ** 2
    k = np.argmin(d)
    return float(arrival[J[k], I[k]])


def japan_mask(W, H, box, ss=3):
    return land_mask(W, H, lambda lo, la: px(W, H, box, lo, la), ss)


def coast(W, H, box, jp):
    """The faintest grey edge of every other coast, so the Pacific can be read; none around Japan."""
    land = sample((~wet).astype(np.float32), W, H, box)
    edge = np.clip(1 - np.abs(land - 0.5) * 4, 0, 1) * 0.16
    near = binary_dilation(jp > 0.05, iterations=max(2, int(W / 300)))
    return np.where(near, 0, edge)


def halo(d, xy, text, f, u, fill, anchor):
    """Text with a black halo, so it stays legible where it crosses a beam."""
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=max(2, int(3 * u)), stroke_fill=(0, 0, 0))


def label(d, f, u, x, y, text, tx, ty, anchor):
    """A small ring on the point (x, y), a leader out to the text at (tx, ty)."""
    grey, w = (130, 130, 130), max(1, int(u))
    r = 4 * u
    d.ellipse([x - r, y - r, x + r, y + r], outline=(0, 0, 0), width=3 * w)
    d.ellipse([x - r, y - r, x + r, y + r], outline=grey, width=w)
    a = np.arctan2(ty - y, tx - x)
    d.line([(x + r * np.cos(a), y + r * np.sin(a)), (tx, ty)], fill=grey, width=w)
    halo(d, (tx + (8 * u if anchor[0] == "l" else -8 * u), ty), text, f, u, grey, anchor)


def hours(h):
    """Arrival rounded to the half hour: the source is idealised, minutes would overstate it."""
    return f"{round(h * 2) / 2:g} h"


# a few hour rings named along a line out from the epicentre, through the darker sea between the beams
# (stopping before the island arcs, where the arrival jumps and labels would pile up)
RING_LABELS = {"desktop": ((172.0, -40.0), (1, 2, 4, 6)), "phone": ((150.0, -28.0), (1, 2, 4, 5))}
LABEL_AT = {  # (Japan's name, the epicentre's label) lon/lat, per frame
    "desktop": ((134.0, 29.5), (151.0, 48.5)),
    "phone": ((134.5, 29.0), (151.0, 47.0)),
}


def render(W, H, out, bare=False):
    """bare: Japan lit but no labels or caption (the front page's particle scene samples it)."""
    phone = H > W
    kind = "phone" if phone else "desktop"
    box = BOX[kind]
    t = intensity(sample(gaussian_filter(emax, 0.6), W, H, box))
    img = cmap(t ** 0.9)
    # arrival-time rings, every hour, faint
    arr = sample(np.nan_to_num(arrival, nan=99), W, H, box)
    ring = np.zeros((H, W), np.float32)
    for hr in range(1, 24):
        d = np.abs(arr - hr)
        ring = np.maximum(ring, np.clip(1 - d / (0.045 if not phone else 0.03), 0, 1))
    ring *= sample(wet.astype(np.float32), W, H, box) > 0.5
    img = np.maximum(img, ring[..., None] * np.array([0.10, 0.30, 0.34]) * 0.6)
    jp = japan_mask(W, H, box)
    img = np.maximum(img, coast(W, H, box, jp)[..., None])
    img = light_japan(img, jp, z=min(W, H) / 2160 * (1.6 if phone else 1))
    arr8 = (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
    arr8[arr8.max(-1) < 4] = 0
    im = Image.fromarray(arr8)
    if bare:
        save(im, out)
        return
    d = ImageDraw.Draw(im)
    u = H / 2160 if not phone else W / 1290 * 0.9
    f = ImageFont.truetype(F_LIGHT, int(17 * u))
    P = lambda lo, la: px(W, H, box, lo, la)
    (jlo, jla), (elo, ela) = LABEL_AT[kind]
    halo(d, P(jlo, jla), "日本  Japan", ImageFont.truetype(F_LIGHT, int(22 * u)), u, (190, 165, 130), "mm")
    ex, ey = P(*EPI)
    label(d, f, u, ex, ey, "震源  Epicentre, magnitude 9.0", *P(elo, ela), "lm")
    for key, jpn, en, lo, la in PLACES:
        x, y = P(lo, la)
        if not (0 < x < W and 0 < y < H):
            continue
        right = x > W * 0.8
        tx, ty = x + (-60 if right else 60) * u, y - 40 * u
        label(d, f, u, x, y, f"{jpn}  {en}, {hours(arrival_at(lo, la))}", tx, ty, "rm" if right else "lm")
    # hour rings: where the line out from the epicentre first meets each one
    (tlo, tla), hrs = RING_LABELS[kind]
    tx, ty = P(tlo, tla)
    for s in np.linspace(0, 1, 4000):
        x, y = ex + (tx - ex) * s, ey + (ty - ey) * s
        a = arr[int(y), int(x)]
        if hrs and hrs[0] <= a < 90:
            halo(d, (x, y), f"{hrs[0]} h", f, u, (110, 150, 155), "mm")
            hrs = hrs[1:]
    caption(im, "津波  Tōhoku tsunami, 11 March 2011  ·  highest wave in 24 h, simulated from the shallow-water "
                "equations on real ocean depth  ·  rings = hours", ramp=RAMP)
    save(im, out)


if __name__ == "__main__":
    if "--info" in sys.argv:
        print(f"Japan: {len(JP)} Natural Earth polygons")
        for k, jpn, en, lo, la in PLACES:
            print(f"{en:12s} first wave {arrival_at(lo, la):5.2f} h after the earthquake (simulated)")
        sys.exit()
    render(*DESKTOP, "out/tsunami_desktop.png")
    render(*PHONE, "out/tsunami_phone.png")
    render(*DESKTOP, "out/tsunami_bare_desktop.png", bare=True)
    render(*PHONE, "out/tsunami_bare_phone.png", bare=True)
