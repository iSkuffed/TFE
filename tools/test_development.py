"""14_development.txt replaces vanilla's whole 1337 file: every key it names must be a real vanilla map name."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

DEV = b.MOD / "main_menu/setup/start/14_development.txt"


def test_no_bom():
    # start files must not have one (the start loader chokes: see test_borders), though decoding tolerates it
    assert not DEV.read_bytes().startswith(b"\xef\xbb\xbf")


def test_keys_exist_in_vanilla_map():
    hier = b.load_hierarchy()  # location -> (continent, subcontinent, region, area, province)
    names = set(hier) | {n for anc in hier.values() for n in anc}
    text = re.sub(r"#[^\n]*", "", DEV.read_text(encoding="utf-8-sig"))
    places = text[text.index("scandinavian_region"):]  # the generic terms (base, coastal, ...) come first
    keys = re.findall(r"^\s*(\w+)\s*=\s*-?[\d.]+\s*$", places, re.M)
    assert not [k for k in keys if k not in names]
    assert len(keys) == len(set(keys))  # a repeated key is a typo, not a second bonus
