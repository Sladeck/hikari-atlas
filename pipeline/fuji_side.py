"""Mount Fuji from the side: the same 10 m contour rings, seen in perspective from the south.

The rings stack into the cone's silhouette. Hidden lines are removed with a depth buffer
built from the elevation model itself (z-buffer at quarter resolution, eroded so the
sparse foreground has no holes). No vertical exaggeration: this is Fuji's real profile.
"""
import numpy as np
from scipy.ndimage import grey_erosion
import fuji as F                      # reuses the DEM, contours, colour ramp
from common import Canvas, caption, save, DESKTOP, PHONE

KM = 111.32
k = np.cos(np.radians(F.SUMMIT[1]))


def grids(M):
    """Terrain of mountain M (fuji, or one from mountains.py) in km around its summit."""
    ny, nx = M.smooth.shape
    kk = np.cos(np.radians(M.SUMMIT[1]))
    jj, ii = np.meshgrid(np.arange(nx), np.arange(ny))
    return (((M.LON0 + jj * M.RES) - M.SUMMIT[0]) * KM * kk,     # km east of summit
            ((M.LAT0 - ii * M.RES) - M.SUMMIT[1]) * KM,           # km north of summit
            np.nan_to_num(M.smooth, nan=0) / 1000.0)              # km up


class Cam:
    def __init__(self, W, H, dist, cam_h, az_deg, target_h, fov_deg, y_frac):
        a = np.radians(az_deg)                          # direction FROM which we look (0 = from south)
        self.C = np.array([-np.sin(a) * dist, -np.cos(a) * dist, cam_h])
        T = np.array([0.0, 0.0, target_h])
        f = T - self.C; self.f = f / np.linalg.norm(f)
        r = np.cross(self.f, [0, 0, 1]); self.r = r / np.linalg.norm(r)
        self.u = np.cross(self.r, self.f)
        self.F = W / (2 * np.tan(np.radians(fov_deg) / 2))
        self.W, self.H, self.cy = W, H, H * y_frac

    def project(self, x, y, z):
        v = np.stack([x - self.C[0], y - self.C[1], z - self.C[2]], -1)
        d = v @ self.f
        return self.W / 2 + (v @ self.r) / d * self.F, self.cy - (v @ self.u) / d * self.F, d


def zbuffer(cam, W, H, M=F, q=4):
    """Nearest terrain distance per (quarter-res) pixel, eroded to close foreground gaps."""
    GX, GY, dem = grids(M)
    x, y, d = cam.project(GX[::2, ::2].ravel(), GY[::2, ::2].ravel(), dem[::2, ::2].ravel())
    zb = np.full((H // q + 1, W // q + 1), np.inf, np.float32)
    ok = (d > 0) & (x >= 0) & (x < W) & (y >= 0) & (y < H)
    np.minimum.at(zb, ((y[ok] / q).astype(int), (x[ok] / q).astype(int)), d[ok].astype(np.float32))
    zb[np.isinf(zb)] = 1e9
    return grey_erosion(zb, size=(5, 5)), q


def render(W, H, out, M=F, view=None, lev_min=600, text=None):
    phone = H > W
    if view:
        cam = Cam(W, H, **view)
    else:
        cam = (Cam(W, H, dist=27, cam_h=3.2, az_deg=8, target_h=2.3, fov_deg=13.5, y_frac=0.50) if phone else
               Cam(W, H, dist=30, cam_h=3.0, az_deg=8, target_h=1.6, fov_deg=27, y_frac=0.52))
    kk = np.cos(np.radians(M.SUMMIT[1]))
    zb, q = zbuffer(cam, W, H, M)
    cv = Canvas(W, H)
    z = min(W, H) / 2160
    for lev, c in M.CONTOURS:
        if lev < lev_min:
            continue
        lon = M.LON0 + c[:, 1] * M.RES; lat = M.LAT0 - c[:, 0] * M.RES
        x3 = (lon - M.SUMMIT[0]) * KM * kk; y3 = (lat - M.SUMMIT[1]) * KM
        x, y, d = cam.project(x3, y3, np.full(len(x3), lev / 1000.0))
        inside = (d > 0) & (x > -20) & (x < W + 20) & (y > -20) & (y < H + 20)
        if inside.sum() < 2:
            continue
        xi = np.clip((x / q).astype(int), 0, zb.shape[1] - 1); yi = np.clip((y / q).astype(int), 0, zb.shape[0] - 1)
        vis = inside & (d <= zb[yi, xi] + 0.35)          # visible = not behind the terrain
        major = lev % 100 == 0
        w = (0.34 if major else 0.12) * (1.2 if phone else 1) * (0.15 + 0.85 * (lev / 3776) ** 1.1) * np.clip((lev - lev_min) / 900, 0, 1) ** 1.5
        w = w * vis * np.clip(30 / d, 0.4, 1.3)          # nearer rings slightly brighter
        cv.add_polyline(x, y, F.ecolor(lev), w, step=0.5)
    im = cv.finish(core=0.5 * max(1, z), glow=4 * z, glow_amt=0.45, gain=3.4, black=1.5e-2)
    caption(im, text or "富士山  Mount Fuji from the south, 3 km up  ·  10 m contour rings in perspective, true vertical scale  ·  "
                        "30 m elevation model", ramp=F.RAMP)
    save(im, out)


if __name__ == "__main__":
    render(*DESKTOP, "out/fuji_side_desktop.png")
    render(*PHONE, "out/fuji_side_phone.png")
