"""The recoloured UI swatches exist and are purple, not vanilla's blue."""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b
import recolor_ui as r


def test_swatches_are_purple():
    for n in r.SWATCHES:
        red, green, blue, _ = Image.open(b.MOD / f"loading_screen/gfx/interface/colors/{n}.dds").convert("RGBA").getpixel((5, 5))
        assert blue >= green and red >= green, n
