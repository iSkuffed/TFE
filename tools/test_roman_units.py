"""The Roman empires recruit Comitatenses and Limitanei in place of vanilla's Footmen and Archers."""
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b
from test_vanilla_copies import _block

UNITS = b.MOD / "in_game/common/unit_types/tfe_roman_units.txt"
ADVANCES = b.MOD / "in_game/common/advances/tfe_roman_units.txt"
START = b.MOD / "in_game/common/on_action/tfe_roman_units.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_roman_units_l_english.yml"
VANILLA = b.GAME / "in_game/common/unit_types/2_unlocked_through_tech.txt"
ROMAN = "OR = { tfe_is_western_rome = yes has_or_had_tag = EAR }"
# ours, and the vanilla unit each stands in for. Each has its own picture, army_infantry_<unit type>.dds, which the game
# tries before any gfx tag or culture: MAZZO313's paintings of late Roman spearmen, mailed behind eagle and sunburst
# shields (Comitatenses), in striped tunics behind wheel-painted shields (Limitanei).
# Not the legionaries' look (the early Empire's, not 395's) nor light_tag (the pitchfork levy).
OURS = {"tfe_comitatenses": "a_footmen", "tfe_limitanei": "a_archers"}
ART = "gfx/interface/illustrations/units"
PICTURES = {unit: b.MOD / "main_menu" / ART / f"army_infantry_{unit}.dds" for unit in OURS}


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def block(text, key):
    return _block("\n" + text, key)


def test_files_are_bom_prefixed_and_balanced():
    for p in (UNITS, ADVANCES, START, LOC):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in (UNITS, ADVANCES, START):
        assert code(p).count("{") == code(p).count("}"), p.name


def test_the_roman_units_copy_vanillas_and_only_rome_recruits_them():
    units = code(UNITS)
    for unit, vanilla in OURS.items():
        body = block(units, unit)
        assert f"copy_from = {vanilla}" in body, unit
        assert f"country_potential = {{ {ROMAN} }}" in body, unit   # a copy inherits vanilla's, which bars Rome
        assert not re.search(r"\b(legionary_tag|light_tag|archer_tag|middle_east_gfx)\b", body), unit
        art = PICTURES[unit]
        assert art.exists() and (art.parent / "masks" / art.name).exists(), art


def overlay(base, colour, opacity):
    # gui_threecolor_blendable_mask.shader: Overlay(picture, country colour, mask red * 0.75), Overlay as in utility.fxh
    o = np.where(base < 0.5, 2 * base * colour, 1 - 2 * (1 - base) * (1 - colour))
    return o * opacity + base * (1 - opacity)


def test_the_pictures_are_red_in_the_west_and_purple_in_the_east():
    # MAZZO313 painted each unit twice, red for the West and purple for the East. One picture serves both: its mask's
    # red marks the stripes and shields, which the game tints with the country's colour. The Military tab shows the
    # whole picture and the small icons its left third, where the front man stands
    from PIL import Image
    tags = b.load_tags()
    for unit, art in PICTURES.items():
        pic, mask = (np.asarray(Image.open(p).convert("RGB"), float) / 255 for p in (art, art.parent / "masks" / art.name))
        assert pic.shape == mask.shape and pic.shape[1] / pic.shape[0] > 2.3, unit   # vanilla's are 1080 x 440, 2000 x 840
        assert mask[..., 1:].max() == 0, unit   # green and blue would bring in the second and third colours
        tinted = mask[..., 0] > 0.5
        assert 0.05 < tinted.mean() < 0.5, unit
        seen = {}
        for tag in ("WRE", "EAR"):
            colour = np.array(tags[tag]["rgb"]) / 255
            r, g, bl = overlay(pic, colour, mask[..., :1] * 0.75)[tinted].mean(0)
            seen[tag] = (r, g, bl)
        assert seen["WRE"][0] > 2 * max(seen["WRE"][1:]), (unit, seen)   # red
        r, g, bl = seen["EAR"]
        assert bl > 1.5 * g and r > 1.5 * g, (unit, seen)                  # purple


def test_vanillas_footmen_and_archers_are_barred_to_rome_and_otherwise_unchanged():
    # REPLACE: blocks are vanilla's own plus one TFE line; this fails when an EU5 patch changes the originals
    vanilla = VANILLA.read_text(encoding="utf-8-sig")
    units = UNITS.read_text(encoding="utf-8-sig")
    for unit in OURS.values():
        ours = block(units.replace(f"REPLACE:{unit} = {{", f"{unit} = {{"), unit)
        assert ours.replace(f" NOT = {{ {ROMAN} }} # TFE", "") == block(vanilla, unit), unit
        assert f"NOT = {{ {ROMAN} }}" in ours, unit


def test_rome_can_research_its_units_and_has_them_from_the_start():
    adv = code(ADVANCES)
    for unit in OURS:
        body = block(adv, f"tfe_unlock_{unit[4:]}_advance")
        assert f"unlock_unit = {unit}" in body and f"potential = {{ {ROMAN} }}" in body
        assert "requires = codified_laws" in body   # researched for every country on day one (defs_start_advances.py)
    start = code(START)
    for unit in OURS:
        assert f"research_advance = advance_type:tfe_unlock_{unit[4:]}_advance" in start


def test_the_easts_armies_are_comitatenses_and_limitanei():
    armies = code(b.MOD / "main_menu/setup/395/27_armies.txt")
    roman = re.findall(r"country = (?:EAR|WRE)\s+location = \w+\s+sub_units = \{(.*?)\n\t\t\}", armies, re.S)
    assert len(roman) == 3
    units = re.findall(r"(\w+) = \{ strength", "".join(roman))
    assert units.count("tfe_comitatenses") == 14 and units.count("tfe_limitanei") == 5
    assert not {"a_footmen", "a_archers"} & set(units)


def test_everything_is_localized():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    want = {k for unit in OURS for k in (unit, f"{unit}_desc", f"tfe_unlock_{unit[4:]}_advance",
                                         f"tfe_unlock_{unit[4:]}_advance_desc")}
    assert not want - keys, sorted(want - keys)
