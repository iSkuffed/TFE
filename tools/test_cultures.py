"""395 cultures: twelve new ones built from vanilla parts, and a rule table that remaps every 1337 pop of the core."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

CULTURES = b.MOD / "in_game/common/cultures/tfe_cultures.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_cultures_l_english.yml"
REPLACE = b.MOD / "main_menu/localization/english/replace/tfe_cultures_replace_l_english.yml"
NEW = {"gallo_roman", "hispano_roman", "afro_roman", "briton", "pictish", "frankish", "alamannic", "suebian",
       "vandal", "tfe_burgundian", "hunnic", "venedi"}


def vanilla_text(folder):
    return "\n".join(p.read_text(encoding="utf-8-sig") for p in (b.GAME / "in_game/common" / folder).glob("*.txt"))


def blocks(text):
    return {m.group(1): m.group(2) for m in re.finditer(r"^(\w+)\s*=\s*\{(.*?)^\}", text, re.M | re.S)}


def test_new_cultures_are_defined_from_vanilla_parts():
    assert CULTURES.read_bytes().startswith(b"\xef\xbb\xbf")
    text = CULTURES.read_text(encoding="utf-8-sig")
    assert text.count("{") == text.count("}")
    defs = blocks(text)
    assert set(defs) == NEW
    languages = vanilla_text("languages")
    groups = set(blocks(vanilla_text("culture_groups")))
    for name, body in defs.items():
        lang = re.search(r"language = (\w+)", body).group(1)
        assert re.search(rf"^\s*{lang}\s*=\s*\{{", languages, re.M), (name, lang)
        mine = re.findall(r"\w+", re.search(r"culture_groups = \{(.*?)\}", body, re.S).group(1))
        assert mine and set(mine) <= groups, (name, mine)
        assert re.search(r"color = rgb \{ \d+ \d+ \d+ \}", body), name


def test_cultures_are_localized_and_roman_is_roman():
    for p in (LOC, REPLACE):
        assert p.read_bytes().startswith(b"\xef\xbb\xbfl_english:")
    keys = dict(re.findall(r'^ (\w+): "(.*)"', LOC.read_text(encoding="utf-8-sig"), re.M))
    assert NEW <= set(keys)
    assert re.search(r'^ roman_culture: "Roman"$', REPLACE.read_text(encoding="utf-8-sig"), re.M)
