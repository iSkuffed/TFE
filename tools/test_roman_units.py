"""The Roman empires recruit Comitatenses and Limitanei in place of vanilla's Footmen and Archers."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b
from test_vanilla_copies import _block

UNITS = b.MOD / "in_game/common/unit_types/tfe_roman_units.txt"
ADVANCES = b.MOD / "in_game/common/advances/tfe_roman_units.txt"
START = b.MOD / "in_game/common/on_action/tfe_roman_units.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_roman_units_l_english.yml"
VANILLA = b.GAME / "in_game/common/unit_types/2_unlocked_through_tech.txt"
ROMAN = "OR = { tfe_is_western_rome = yes has_or_had_tag = EAR }"
# ours: the vanilla unit it stands in for, and where its picture comes from. The Comitatenses take the DLC's East
# Mediterranean armoured spearmen through a gfx tag named after that illustration (a unit's own tags are tried before
# its soldiers' culture). The Limitanei have their own picture, army_infantry_<unit type>.dds, which the game tries
# first of all: a copy of the base game's 2_light_tag, light spearmen in leather caps and hoods.
# Not the legionaries (the early Empire's, not 395's) nor light_tag (the pitchfork levy).
OURS = {"tfe_comitatenses": ("a_footmen", "east_mediterranean_gfx"), "tfe_limitanei": ("a_archers", None)}
ART = "gfx/interface/illustrations/units"
PICTURES = {"tfe_comitatenses": b.GAME / "dlc/D008_fate_of_the_phoenix/main_menu" / ART / "army_infantry_east_mediterranean_gfx.dds",
            "tfe_limitanei": b.MOD / "main_menu" / ART / "army_infantry_tfe_limitanei.dds"}


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
    for unit, (vanilla, tag) in OURS.items():
        body = block(units, unit)
        assert f"copy_from = {vanilla}" in body, unit
        assert f"country_potential = {{ {ROMAN} }}" in body, unit   # a copy inherits vanilla's, which bars Rome
        if tag:
            assert re.search(rf"gfx_tags = {{ [^}}]*\b{tag}\b", body), unit
        assert not re.search(r"\b(legionary_tag|light_tag|archer_tag|middle_east_gfx)\b", body), unit
        art = PICTURES[unit]
        assert art.exists() and (art.parent / "masks" / art.name).exists(), art


def test_the_limitanei_picture_is_vanillas_light_spearmen_whole():
    # MAZZO313: the cropped spearman's right side faded into a mirrored fog that looked broken on the Military tab,
    # which shows the whole picture. A vanilla painting used whole already frames its front man for the small icons
    for sub in ("", "masks/"):
        ours = b.MOD / "main_menu" / ART / f"{sub}army_infantry_tfe_limitanei.dds"
        assert ours.read_bytes() == (b.GAME / "main_menu" / ART / f"{sub}army_infantry_2_light_tag.dds").read_bytes(), sub


def test_vanillas_footmen_and_archers_are_barred_to_rome_and_otherwise_unchanged():
    # REPLACE: blocks are vanilla's own plus one TFE line; this fails when an EU5 patch changes the originals
    vanilla = VANILLA.read_text(encoding="utf-8-sig")
    units = UNITS.read_text(encoding="utf-8-sig")
    for _, (unit, _) in OURS.items():
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
    armies = code(b.MOD / "main_menu/setup/start/27_armies.txt")
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
