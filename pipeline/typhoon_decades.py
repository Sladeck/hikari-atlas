"""Typhoons decade by decade: the same map eight times, 1950s to the 2020s, as small multiples.

Same drawing as typhoons.py (colour = central pressure, storms that fell below 930 hPa drawn
bright), one panel per decade so the decades can be compared: 4 x 2 on desktop, 2 x 4 on phone.
The first panel starts in 1951 and the last runs to the last complete season.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import typhoons as ty
from common import caption, save, DESKTOP, PHONE, F_LIGHT

BOX = (112, 166, 6, 52)                          # the phone view's box: near square, Japan in frame
storms = [s for s in ty.load(ty.BST) if s[0, 0] <= ty.LAST]
DECADES = [(y, min(y + 9, ty.LAST)) for y in range(1950, ty.LAST + 1, 10)]


def label(a, b):
    if b < a + 9:
        return f"{max(a, 1951)}–{str(b)[2:]}"    # a decade still in progress, e.g. 2020–25
    return f"{a}s"


def render(W, H, out):
    phone = H > W
    cols, rows = (2, 4) if phone else (4, 2)
    mx, top, bottom = (0.05 * W, 0.05 * H, 0.09 * H) if phone else (0.03 * W, 0.04 * H, 0.08 * H)
    gap = 0.012 * max(W, H)
    pw = int((W - 2 * mx - (cols - 1) * gap) / cols)
    ph = int((H - top - bottom - (rows - 1) * gap) / rows)
    im = Image.new("RGB", (W, H))
    dr = ImageDraw.Draw(im)
    u = min(W, H) / 2160 * (1.5 if phone else 1)
    f = ImageFont.truetype(F_LIGHT, int(20 * u))
    f2 = ImageFont.truetype(F_LIGHT, int(15 * u))
    total_strong = 0
    for i, (a, b) in enumerate(DECADES):
        sel = [s for s in storms if a <= s[0, 0] <= b]
        panel, n_strong = ty.tracks(sel, pw, ph, BOX, k=1.0, weak_k=10.0)
        # soften the panel edges so tracks fade out instead of ending on a hard rectangle
        e = 0.06
        fx = np.clip(np.minimum(np.arange(pw), pw - 1 - np.arange(pw)) / (e * pw), 0, 1)
        fy = np.clip(np.minimum(np.arange(ph), ph - 1 - np.arange(ph)) / (e * ph), 0, 1)
        fade = (fx[None, :] * fy[:, None]) ** 1.5
        panel = Image.fromarray((np.asarray(panel, np.float32) * fade[..., None] + 0.5).astype(np.uint8))
        total_strong += n_strong
        x0 = int(mx + (i % cols) * (pw + gap)); y0 = int(top + (i // cols) * (ph + gap))
        im.paste(panel, (x0, y0))
        dr.text((x0 + 14 * u, y0 + ph - 38 * u), label(a, b), font=f, fill=(120, 140, 150), anchor="ls")
        dr.text((x0 + 14 * u, y0 + ph - 14 * u), f"{len(sel)} storms · {n_strong} below 930 hPa", font=f2,
                fill=(80, 95, 105), anchor="ls")
    arr = np.asarray(im).copy()
    arr[arr.max(-1) <= 2] = 0                    # guaranteed #000000 between and around the panels
    im = Image.fromarray(arr)
    caption(im, f"台風  Typhoons decade by decade  ·  {len(storms):,} storms, {DECADES[0][0] + 1}–{ty.LAST}  ·  "
                f"bright = below 930 hPa ({total_strong})  ·  JMA best track", ramp=ty.RAMP)
    save(im, out)


if __name__ == "__main__":
    for a, b in DECADES:
        print(label(a, b), sum(a <= s[0, 0] <= b for s in storms), "storms")
    render(*DESKTOP, "out/typhoon_decades_desktop.png")
    render(*PHONE, "out/typhoon_decades_phone.png")
