"""Build the Limitanei's picture and mask (main_menu/gfx/interface/illustrations/units/army_infantry_tfe_limitanei.dds
and masks/) from the base game's middle_east_gfx infantry: the helmeted spearman in mail hood and leather jerkin, not
the turbaned ranks around him.

The small unit icons show only the left third of a unit picture (army_builder.gui: frame_grid = {3 1}, frame = 1),
so he stands in the left third. The full picture (the unit page, the army banner) fades the turbaned ranks to his
right into the mist, blurred like the painting's own back ranks.

    python tools/limitanei_art.py            # a preview sheet only
    python tools/limitanei_art.py --write    # rewrite the two .dds files
"""
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

SRC = b.GAME / "main_menu/gfx/interface/illustrations/units"
OUT = b.MOD / "main_menu/gfx/interface/illustrations/units"
NAME = "army_infantry_middle_east_gfx.dds"
# at the painting's own scale, as vanilla's icons show their soldier from helmet to waist; his face (x 950 of the
# original) at the centre of the left third. That pushes the picture 617 px left, so the empty right edge is filled
# with the painting mirrored, and faded into the mist with the turbaned ranks.
FACE_X, ZOOM = 950, 1.0
FADE_FROM, FADE_TO, FADE_MAX = 0.31, 0.52, 1.0   # fractions of the width, and how far the far side fades


def ramp(w, h):
    row = bytes(int(FADE_MAX * 255 * min(1, max(0, (x / w - FADE_FROM) / (FADE_TO - FADE_FROM)))) for x in range(w))
    return Image.frombytes("L", (w, 1), row).resize((w, h))


def build(path, haze=None):
    src = Image.open(path).convert("RGBA")
    w, h = src.size
    ext = Image.new("RGBA", (2 * w, h), (0, 0, 0, 0))   # the painting, and beyond its right edge its mirror (the mask: nothing)
    ext.paste(src, (0, 0))
    if haze:
        ext.paste(src.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (w, 0))
    left = round(FACE_X - w / 6 / ZOOM)
    img = ext.crop((left, 0, left + round(w / ZOOM), round(h / ZOOM))).resize((w, h), Image.LANCZOS)
    if haze:   # the picture: the far ranks recede into the mist
        far = Image.blend(img.filter(ImageFilter.GaussianBlur(14)), Image.new("RGBA", (w, h), haze + (255,)), 0.5)
    else:      # the mask: faded figures take no country colour
        far = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return Image.composite(far, img, ramp(w, h))


def main():
    haze = Image.open(SRC / NAME).crop((1750, 20, 1990, 200)).convert("RGB").resize((1, 1), Image.BOX).getpixel((0, 0))
    pic, mask = build(SRC / NAME, haze), build(SRC / "masks" / NAME)
    if "--write" in sys.argv:
        pic.save(OUT / "army_infantry_tfe_limitanei.dds", pixel_format="DXT5")
        mask.save(OUT / "masks" / "army_infantry_tfe_limitanei.dds", pixel_format="DXT5")
        print(f"wrote {OUT / 'army_infantry_tfe_limitanei.dds'} and its mask")
    w, h = pic.size
    full = pic.convert("RGB")
    full.thumbnail((1000, 500))
    icon = pic.crop((0, 0, w // 3, h)).convert("RGB")
    icon.thumbnail((240, 300))
    sheet = Image.new("RGB", (1250, full.height + 20), "black")
    sheet.paste(full, (0, 20))
    sheet.paste(icon, (1005, 20))
    ImageDraw.Draw(sheet).text((5, 3), "the picture | right: the icon (its left third)", fill="yellow")
    preview = Path(os.environ.get("TEMP", "/tmp")) / "limitanei_preview.png"
    sheet.save(preview)
    print(f"preview: {preview}")


if __name__ == "__main__":
    main()
