"""Every 395 country flies its own flag, built from vanilla coat-of-arms textures and colours."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

FLAGS = b.MOD / "main_menu/common/coat_of_arms/coat_of_arms/tfe_countries.txt"
GFX = b.GAME / "main_menu/gfx/coat_of_arms"


def test_every_tag_has_a_flag_of_vanilla_parts():
    assert FLAGS.read_bytes().startswith(b"\xef\xbb\xbf")
    text = FLAGS.read_text(encoding="utf-8-sig")
    assert text.count("{") == text.count("}")
    keys = re.findall(r"^(\w+) = \{", text, re.M)
    assert len(keys) == len(set(keys))
    assert set(b.load_tags()) <= set(keys), set(b.load_tags()) - set(keys)
    for tex in set(re.findall(r'pattern = "(\w+\.dds)"', text)):
        assert (GFX / "patterns" / tex).exists(), tex
    for tex in set(re.findall(r'texture = "(\w+\.dds)"', text)):
        assert (GFX / "colored_emblems" / tex).exists(), tex
    named = set(re.findall(r"^\s*(\w+)\s*=\s*hsv360", (b.GAME / "main_menu/common/named_colors/01_coa.txt")
                           .read_text(encoding="utf-8-sig"), re.M))
    assert set(re.findall(r'color\d = "(\w+)"', text)) <= named


def test_vanilla_flag_lists_are_replaced():
    # a vanilla flag list for one of our tags would pick its own coat of arms (Thaton flew Wallachia's)
    ours = (b.MOD / "main_menu/common/flag_definitions/tfe_flag_definitions.txt").read_text(encoding="utf-8-sig")
    vanilla = (b.GAME / "main_menu/common/flag_definitions/00_flag_definitions.txt").read_text(encoding="utf-8-sig")
    listed = set(re.findall(r"^(\w+) = \{", vanilla, re.M)) & set(b.load_tags())
    assert listed and listed <= set(re.findall(r"^REPLACE:(\w+) = \{", ours, re.M)), listed
