"""The share card (Open Graph / Twitter): Fuji's summit cone in ridge lines with the site's name,
1200 x 630, written to public/og.png. Rendered at twice the size and scaled down so the lines stay fine.

    python og.py
"""
import os
from PIL import Image, ImageDraw, ImageFont
import fuji_ridges as R
from common import WEB_PUBLIC, F_LIGHT

W, H = 2400, 1260                                       # 2x the card
MINCHO = next((p for p in ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Medium.ttc",
                           "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc") if os.path.exists(p)), F_LIGHT)
# the desktop close-up, the cone a little to the right so the name has the dark sky on the left
VIEW = dict(R.VIEW["desktop"], cam=dict(R.VIEW["desktop"]["cam"], y_frac=0.40))

im = R.render(W, H, None, view=VIEW, bare=True).convert("RGB")
d = ImageDraw.Draw(im)
x, y = 130, 190                                         # clear of the edges some platforms crop
d.text((x, y), "光の地図", font=ImageFont.truetype(MINCHO, 120), fill=(255, 138, 76), anchor="ls")       # Fuji's accent
d.text((x + 4, y + 70), "HIKARI ATLAS", font=ImageFont.truetype(F_LIGHT, 40), fill=(225, 225, 225), anchor="ls")
d.text((x + 4, y + 126), "Japan drawn only with light, from real data", font=ImageFont.truetype(F_LIGHT, 34),
       fill=(140, 140, 140), anchor="ls")
out = os.path.join(WEB_PUBLIC, "og.png")
im.resize((W // 2, H // 2), Image.LANCZOS).save(out, optimize=True)
print(out, os.path.getsize(out) // 1024, "KB")
