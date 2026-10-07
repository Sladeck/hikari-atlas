"""The 2011 Tōhoku tsunami, simulated from the linear shallow-water equations.

Ocean depth: ETOPO1 resampled to 10 arc-minutes (fatiando-data/earth-topography-10arcmin).
Source: a simplified seafloor uplift along the Japan Trench (about +5 m on the trench side,
-2 m landward, ~400 x 150 km, striking ~15° east of north). This is an idealised source,
not the published rupture model, so arrival times and heights are approximate.

Solver: staggered C-grid on the sphere, forward-backward time stepping, land = walls,
sponge layer at the open boundaries. Outputs:
  * the maximum wave height reached everywhere in 24 h (the wallpaper)
  * hourly arrival-time contours drawn on top
  * frames of the moving wave for the website animation (frames/*.png -> webm)
"""
import os, sys
import numpy as np, h5py
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, zoom, binary_dilation
from common import caption, save, dl, DESKTOP, PHONE

g, R = 9.81, 6.371e6
f = h5py.File(dl("topo", "earth-topography-10arcmin.nc"))
LON = f["longitude"][:]; LAT = f["latitude"][:]; TOPO = f["topography"][:].astype(np.float32)

# Pacific domain, longitudes 115E .. 290E (=70W), latitudes 62S .. 62N
lat_i = np.where((LAT >= -62) & (LAT <= 62))[0]
lon_a = np.where(LON >= 115)[0]; lon_b = np.where(LON <= -70)[0]
lon_i = np.concatenate([lon_a, lon_b[1:]])
lat = LAT[lat_i]; lon = np.concatenate([LON[lon_a], LON[lon_b[1:]] + 360])
topo = TOPO[np.ix_(lat_i, lon_i)]
h = np.where(topo < -5, -topo, 0.0).astype(np.float64)          # depth (m), 0 on land
wet = h > 0
ny, nx = h.shape
dlam = np.radians(lon[1] - lon[0]); dphi = np.radians(lat[1] - lat[0])
phi = np.radians(lat)[:, None]
cosp = np.cos(phi)
cosp_v = np.cos(phi + dphi / 2)                                   # at N faces (between rows j, j+1)

# source: elliptical uplift + landward trough along the Japan Trench
lon0, lat0, strike = 142.9, 38.2, np.radians(15)
X = (lon[None, :] - lon0) * 111.2 * np.cos(np.radians(lat0)); Y = (lat[:, None] - lat0) * 111.2
along = X * np.sin(strike) + Y * np.cos(strike)
across = X * np.cos(strike) - Y * np.sin(strike)                  # + = east (trench side)
eta = (5.0 * np.exp(-(along / 190) ** 2 - ((across - 25) / 45) ** 2)
       - 2.0 * np.exp(-(along / 190) ** 2 - ((across + 55) / 50) ** 2))
eta = np.where(wet, eta, 0.0)

M = np.zeros((ny, nx + 1)); N = np.zeros((ny + 1, nx))           # volume fluxes on faces
hu = np.zeros((ny, nx + 1)); hu[:, 1:-1] = np.minimum(h[:, 1:], h[:, :-1])
hv = np.zeros((ny + 1, nx)); hv[1:-1, :] = np.minimum(h[1:, :], h[:-1, :])

cmax = np.sqrt(g * h.max())
dx_min = R * np.cos(np.radians(62)) * dlam
dt = 0.45 * dx_min / cmax
T = 24 * 3600
steps = int(T / dt)
print(f"grid {nx}x{ny}, dt={dt:.1f}s, {steps} steps")

# sponge near open boundaries
sp = np.ones((ny, nx))
w = 25
for k in range(w):
    a = 1 - 0.05 * ((w - k) / w) ** 2
    sp[k, :] *= a; sp[-1 - k, :] *= a; sp[:, -1 - k] *= a

emax = np.abs(eta).copy()
arrival = np.full((ny, nx), np.nan)
frames = []
frame_every = int(300 / dt)                                       # one frame per 5 simulated minutes

for n in range(steps):
    # momentum (fluxes) from surface gradient
    M[:, 1:-1] -= dt * g * hu[:, 1:-1] / (R * cosp) * (eta[:, 1:] - eta[:, :-1]) / dlam
    N[1:-1, :] -= dt * g * hv[1:-1, :] / R * (eta[1:, :] - eta[:-1, :]) / dphi
    # continuity
    div = ((M[:, 1:] - M[:, :-1]) / dlam
           + (N[1:, :] * np.vstack([cosp_v[:-1], cosp_v[-1:]]) - N[:-1, :] * np.vstack([cosp_v[:1] * 0 + np.cos(phi[:1] - dphi / 2), cosp_v[:-1]])) / dphi)
    eta -= dt * div / (R * cosp)
    eta *= sp; eta[~wet] = 0
    M[:, 1:-1] *= np.minimum(sp[:, 1:], sp[:, :-1]); N[1:-1, :] *= np.minimum(sp[1:, :], sp[:-1, :])
    a = np.abs(eta)
    np.maximum(emax, a, out=emax)
    newly = np.isnan(arrival) & (a > 0.01)
    arrival[newly] = n * dt / 3600
    if n % frame_every == 0:
        frames.append(eta.astype(np.float32).copy())
    if n % 2000 == 0:
        print(f"  t={n * dt / 3600:5.2f} h  max|eta|={a.max():.2f} m", flush=True)

np.savez_compressed("out/tsunami_sim.npz", emax=emax.astype(np.float32), arrival=arrival.astype(np.float32),
                    frames=np.array(frames, np.float16), lon=lon, lat=lat, wet=wet)
print("saved", len(frames), "frames")
