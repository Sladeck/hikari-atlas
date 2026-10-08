"""Publish finished renders to the website.

    python publish.py quakes_3d [more names...] [--feature]

For each name, copies out/<name>_{desktop,phone}.png to public/wallpapers/full/ and writes the
WebP previews the gallery shows (desktop 1920x1080, phone 516x1118) to public/wallpapers/preview/.
--feature also writes the front page's large stills (no-WebGL fallback) to public/wallpapers/feature/
as <name>_d.webp (2560x1440) and <name>_p.webp (860x1864).
Then run `npm run sizes` so the download buttons show the new file sizes.
"""
import os, shutil, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(HERE, "..", "public", "wallpapers")
PREVIEW = {"desktop": (1920, 1080), "phone": (516, 1118)}
FEATURE = {"desktop": ("d", (2560, 1440)), "phone": ("p", (860, 1864))}

feature = "--feature" in sys.argv
for name in [a for a in sys.argv[1:] if not a.startswith("--")]:
    for kind, size in PREVIEW.items():
        src = os.path.join(HERE, "out", f"{name}_{kind}.png")
        shutil.copyfile(src, os.path.join(PUBLIC, "full", f"{name}_{kind}.png"))
        im = Image.open(src).convert("RGB").resize(size, Image.LANCZOS)
        dst = os.path.join(PUBLIC, "preview", f"{name}_{kind}.webp")
        im.save(dst, "WEBP", quality=85, method=6)
        print(f"{name}_{kind}: png {os.path.getsize(src) / 1e6:.1f} MB, preview {os.path.getsize(dst) / 1e3:.0f} KB")
        if feature:
            tag, fsize = FEATURE[kind]
            fdst = os.path.join(PUBLIC, "feature", f"{name}_{tag}.webp")
            Image.open(src).convert("RGB").resize(fsize, Image.LANCZOS).save(fdst, "WEBP", quality=85, method=6)
            print(f"  feature {os.path.basename(fdst)}: {os.path.getsize(fdst) / 1e3:.0f} KB")
