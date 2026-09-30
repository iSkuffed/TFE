"""Rewrites vanilla's blue UI swatches (10x10 solid .dds) as imperial purple, into loading_screen/gfx/interface/colors/.
Same-path override; rerun after an EU5 patch changes them."""
import colorsys
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

SRC = b.GAME / "loading_screen/gfx/interface/colors"
OUT = b.MOD / "loading_screen/gfx/interface/colors"
SWATCHES = ["bg_blue", "blue", "dark_blue", "light_blue", "mid_blue", "nobles", "clergy", "progress_blue"]
HUE = 280 / 360  # vanilla's steel blue sits near 205 degrees


def recolor(name):
    px = Image.open(SRC / f"{name}.dds").convert("RGBA")
    r, g, bl, a = px.getpixel((5, 5))
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, bl / 255)
    r, g, bl = (round(c * 255) for c in colorsys.hls_to_rgb(HUE, l, max(s, 0.25) if l > 0.06 else s))
    Image.new("RGBA", px.size, (r, g, bl, a)).save(OUT / f"{name}.dds", pixel_format="DXT1")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for n in SWATCHES:
        recolor(n)
