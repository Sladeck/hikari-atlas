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
ny, nx = F.dem.shape
dem = np.nan_to_num(F.smooth, nan=0) / 1000.0           # km
jj, ii = np.meshgrid(np.arange(nx), np.arange(ny))
GX = ((F.LON0 + jj * F.RES) - F.SUMMIT[0]) * KM * k     # km east of summit
GY = ((F.LAT0 - ii * F.RES) - F.SUMMIT[1]) * KM         # km north of summit


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


def zbuffer(cam, W, H, q=4):
    """Nearest terrain distance per (quarter-res) pixel, eroded to close foreground gaps."""
    x, y, d = cam.project(GX[::2, ::2].ravel(), GY[::2, ::2].ravel(), dem[::2, ::2].ravel())
    zb = np.full((H // q + 1, W // q + 1), np.inf, np.float32)
    ok = (d > 0) & (x >= 0) & (x < W) & (y >= 0) & (y < H)
    np.minimum.at(zb, ((y[ok] / q).astype(int), (x[ok] / q).astype(int)), d[ok].astype(np.float32))
    zb[np.isinf(zb)] = 1e9
    return grey_erosion(zb, size=(5, 5)), q


def render(W, H, out):
    phone = H > W
    cam = (Cam(W, H, dist=27, cam_h=3.2, az_deg=8, target_h=2.3, fov_deg=13.5, y_frac=0.50) if phone else
           Cam(W, H, dist=30, cam_h=3.0, az_deg=8, target_h=1.6, fov_deg=27, y_frac=0.52))
    zb, q = zbuffer(cam, W, H)
    cv = Canvas(W, H)
    z = min(W, H) / 2160
    for lev, c in F.CONTOURS:
        if lev < 600:
            continue
        lon = F.LON0 + c[:, 1] * F.RES; lat = F.LAT0 - c[:, 0] * F.RES
        x3 = (lon - F.SUMMIT[0]) * KM * k; y3 = (lat - F.SUMMIT[1]) * KM
        x, y, d = cam.project(x3, y3, np.full(len(x3), lev / 1000.0))
        inside = (d > 0) & (x > -20) & (x < W + 20) & (y > -20) & (y < H + 20)
        if inside.sum() < 2:
            continue
        xi = np.clip((x / q).astype(int), 0, zb.shape[1] - 1); yi = np.clip((y / q).astype(int), 0, zb.shape[0] - 1)
        vis = inside & (d <= zb[yi, xi] + 0.35)          # visible = not behind the terrain
        major = lev % 100 == 0
        w = (0.34 if major else 0.12) * (1.2 if phone else 1) * (0.15 + 0.85 * (lev / 3776) ** 1.1) * np.clip((lev - 600) / 900, 0, 1) ** 1.5
        w = w * vis * np.clip(30 / d, 0.4, 1.3)          # nearer rings slightly brighter
        cv.add_polyline(x, y, F.ecolor(lev), w, step=0.5)
    im = cv.finish(core=0.5 * max(1, z), glow=4 * z, glow_amt=0.45, gain=3.4, black=1.5e-2)
    caption(im, "富士山  Mount Fuji from the south, 3 km up  ·  10 m contour rings in perspective, true vertical scale  ·  "
                "30 m elevation model", ramp=F.RAMP)
    save(im, out)


if __name__ == "__main__":
    render(*DESKTOP, "out/fuji_side_desktop.png")
    render(*PHONE, "out/fuji_side_phone.png")
