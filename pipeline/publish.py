"""Publish finished renders to the website.

    python publish.py quakes_3d [more names...]

For each name, copies out/<name>_{desktop,phone}.png to public/wallpapers/full/ and writes the
WebP previews the gallery shows (desktop 1920x1080, phone 516x1118) to public/wallpapers/preview/.
Then run `npm run sizes` so the download buttons show the new file sizes.
"""
import os, shutil, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(HERE, "..", "public", "wallpapers")
PREVIEW = {"desktop": (1920, 1080), "phone": (516, 1118)}

for name in sys.argv[1:]:
    for kind, size in PREVIEW.items():
        src = os.path.join(HERE, "out", f"{name}_{kind}.png")
        shutil.copyfile(src, os.path.join(PUBLIC, "full", f"{name}_{kind}.png"))
        im = Image.open(src).convert("RGB").resize(size, Image.LANCZOS)
        dst = os.path.join(PUBLIC, "preview", f"{name}_{kind}.webp")
        im.save(dst, "WEBP", quality=85, method=6)
        print(f"{name}_{kind}: png {os.path.getsize(src) / 1e6:.1f} MB, preview {os.path.getsize(dst) / 1e3:.0f} KB")
