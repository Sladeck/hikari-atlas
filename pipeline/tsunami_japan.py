"""The 2011 Tōhoku tsunami striking Japan: the first three hours, Japan's seas only.

Ocean depth: NOAA NCEI ETOPO 2022, 60 arc-seconds (about 1.85 km), 22-47°N, 122-152°E
(dl/topo/etopo2022_60s_japan.nc, see README "Data"). Same equations and the same idealised source
as tsunami.py (the Pacific crossing), at nine times finer spacing, so the wave can be followed
across the continental shelf onto the coast. Land is a wall: the run-up onto land is not modelled.

Outputs, in out/ (git-ignored):
  * tsunami_japan_frames.npy: the sea surface every FRAME_S simulated seconds, float16, (n, ny, nx)
  * tsunami_japan.npz: grid, land mask, frame times, highest wave and first arrival per cell

    python tsunami_japan.py
"""
import time
import numpy as np
from scipy.io import netcdf_file
from common import dl

g, R = 9.81, 6.371e6
T = 3 * 3600                    # simulated seconds
FRAME_S = 25                    # one stored frame per 25 simulated seconds

f = netcdf_file(dl("topo", "etopo2022_60s_japan.nc"), mmap=False)
lat = f.variables["latitude"][:].astype(np.float64)
lon = f.variables["longitude"][:].astype(np.float64)
z = f.variables["z"][:].astype(np.float32)
h = np.where(z < -5, -z, 0).astype(np.float32)                  # depth (m), 0 on land (a wall)
wet = h > 0
ny, nx = h.shape
dlam = np.radians(lon[1] - lon[0]); dphi = np.radians(lat[1] - lat[0])
phi = np.radians(lat)
cosp = np.cos(phi)[:, None].astype(np.float32)
cosf = np.cos(np.radians(lat[0]) - dphi / 2 + dphi * np.arange(ny + 1))[:, None].astype(np.float32)   # at the N faces

# source: elliptical uplift + landward trough along the Japan Trench (as tsunami.py)
lon0, lat0, strike = 142.9, 38.2, np.radians(15)
X = (lon[None, :] - lon0) * 111.2 * np.cos(np.radians(lat0)); Y = (lat[:, None] - lat0) * 111.2
along = X * np.sin(strike) + Y * np.cos(strike)
across = X * np.cos(strike) - Y * np.sin(strike)                  # + = east (trench side)
eta = (5.0 * np.exp(-(along / 190) ** 2 - ((across - 25) / 45) ** 2)
       - 2.0 * np.exp(-(along / 190) ** 2 - ((across + 55) / 50) ** 2)).astype(np.float32)
eta[~wet] = 0

M = np.zeros((ny, nx + 1), np.float32); N = np.zeros((ny + 1, nx), np.float32)   # volume fluxes on faces
hu = np.zeros((ny, nx + 1), np.float32); hu[:, 1:-1] = np.minimum(h[:, 1:], h[:, :-1])
hv = np.zeros((ny + 1, nx), np.float32); hv[1:-1, :] = np.minimum(h[1:, :], h[:-1, :])

# time step: the CFL limit, shortened so a whole number of steps fills each frame
dx_min = R * np.cos(np.radians(lat.max())) * dlam
dt_cfl = 0.45 * dx_min / np.sqrt(g * h.max())
sub = int(np.ceil(FRAME_S / dt_cfl)); dt = FRAME_S / sub
nframes = T // FRAME_S + 1
print(f"grid {nx}x{ny}, dt={dt:.2f}s, {sub} steps per frame, {nframes} frames")

# sponge on every open edge, so waves leave instead of bouncing back
sp = np.ones((ny, nx), np.float32)
w = 40
for k in range(w):
    a = 1 - 0.04 * ((w - k) / w) ** 2
    sp[k, :] *= a; sp[-1 - k, :] *= a; sp[:, k] *= a; sp[:, -1 - k] *= a
spu = np.minimum(sp[:, 1:], sp[:, :-1]); spv = np.minimum(sp[1:, :], sp[:-1, :])

# constant factors of the update
cu = (dt * g * hu[:, 1:-1] / (R * cosp)).astype(np.float32)
cv = (dt * g * hv[1:-1, :] / R).astype(np.float32)
ce = (dt / (R * cosp)).astype(np.float32)

frames = np.lib.format.open_memmap("out/tsunami_japan_frames.npy", "w+", np.float16, (nframes, ny, nx))
emax = np.abs(eta)
arrival = np.full((ny, nx), np.nan, np.float32)
t0 = time.time()
for fi in range(nframes):
    frames[fi] = eta
    if fi == nframes - 1:
        break
    for _ in range(sub):
        M[:, 1:-1] -= cu * (eta[:, 1:] - eta[:, :-1]) / dlam
        N[1:-1, :] -= cv * (eta[1:, :] - eta[:-1, :]) / dphi
        div = (M[:, 1:] - M[:, :-1]) / dlam + (N[1:, :] * cosf[1:] - N[:-1, :] * cosf[:-1]) / dphi
        eta -= ce * div
        eta *= sp; eta[~wet] = 0
        M[:, 1:-1] *= spu; N[1:-1, :] *= spv
    a = np.abs(eta)
    np.maximum(emax, a, out=emax)
    newly = np.isnan(arrival) & (a > 0.05)
    arrival[newly] = (fi + 1) * FRAME_S / 60                       # minutes, to the frame
    if fi % 36 == 0:
        print(f"  t={(fi + 1) * FRAME_S / 60:5.1f} min  max|eta|={a.max():.2f} m  ({time.time() - t0:.0f} s)", flush=True)

frames.flush()
np.savez_compressed("out/tsunami_japan.npz", lon=lon, lat=lat, wet=wet, h=h, emax=emax, arrival=arrival,
                    times=np.arange(nframes) * FRAME_S)
print(f"saved {nframes} frames in {time.time() - t0:.0f} s")
