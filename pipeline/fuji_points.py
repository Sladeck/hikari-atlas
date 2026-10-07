"""Mount Fuji as a 3D cloud of light: the front page's WebGL view, rendered as a wallpaper.

Points along every 10 m contour ring from 1,000 m to the summit, at their real positions,
seen with the same tilted perspective camera as ParticleJourney.vue (scene 'fuji3d'),
with ~10x more points than the browser draws. Colour = height (the red-Fuji ramp).
"""
import numpy as np
import fuji as F
from common import Canvas, caption, save, DESKTOP, PHONE

KM, k = 111.32, np.cos(np.radians(F.SUMMIT[1]))
rng = np.random.default_rng(11)

pts = []
for lev, c in F.CONTOURS:
    if lev < 1000:
        continue
    lon = F.LON0 + c[:, 1] * F.RES; lat = F.LAT0 - c[:, 0] * F.RES
    x = (lon - F.SUMMIT[0]) * KM * k; y = (lat - F.SUMMIT[1]) * KM
    keep = np.hypot(x, y) < 13.5
    if keep.sum() < 3:
        continue
    # densify along the ring so points are spread evenly, not clumped at raw vertices
    xs, ys = x[keep], y[keep]
    seg = np.hypot(np.diff(xs), np.diff(ys)); L = np.concatenate([[0], np.cumsum(seg)])
    n = max(3, int(L[-1] / 0.012))
    t = np.sort(rng.random(n)) * L[-1]
    pts.append(np.stack([np.interp(t, L, xs), np.interp(t, L, ys), np.full(n, lev / 1000.0)], 1))
P = np.concatenate(pts)
print(len(P), "points on the rings")

ROT = 0.95          # turned a little past the browser's opening angle: the Hōei crater faces us


def project(P, W, H):
    """Same maths as the WebGL vertex shader (fuji3d branch)."""
    x, y = P[:, 0] / 13.5, P[:, 1] / 13.5
    z = (P[:, 2] - 1.9) / 13.5 * 2.0
    c, s = np.cos(ROT), np.sin(ROT)
    rx, ry = x * c - y * s, x * s + y * c
    persp = 1.0 / (1.0 + ry * 0.28)
    qx, qy = rx * persp * 0.92, (z * 1.6 + ry * 0.20 - 0.10) * persp * 0.92
    a = W / H
    if a >= 1:
        cx, cy = qx / a * 1.75, qy * 1.75 + 0.05          # zoomed in: the cone fills the frame
    else:
        cx, cy = qx * 2.8, qy * a * 2.8
    return (cx * 0.5 + 0.5) * W, (0.5 - cy * 0.5) * H, persp


def render(W, H, out):
    phone = H > W
    sx, sy, persp = project(P, W, H)
    if phone:                                          # phone: cone in the upper-middle third
        sy += H * 0.02
    col = F.ecolor(P[:, 2] * 1000)
    h = P[:, 2] / 3.776
    fade = np.clip((P[:, 2] - 1.0) / 0.7, 0, 1) ** 1.6     # low rings dissolve instead of ending on a hard edge
    w = (0.15 + 0.85 * h ** 1.2) * fade * persp * 0.034 * (1.5 if phone else 1)
    cv = Canvas(W, H)
    cv.add_points(sx, sy, col, w)
    z = min(W, H) / 2160
    im = cv.finish(core=0.9 * max(1, z), glow=6 * z, glow_amt=0.55, gain=4.2, black=1.5e-2)
    caption(im, "富士山  Mount Fuji in light  ·  points along every 10 m contour from 1,000 m to the 3,776 m summit, "
                "at their real positions in 3D", ramp=F.RAMP)
    save(im, out)


if __name__ == "__main__":
    render(*DESKTOP, "out/fuji_points_desktop.png")
    render(*PHONE, "out/fuji_points_phone.png")
