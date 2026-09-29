"""A location's own speciality fits 395: the medieval and modern ones are gone, the Roman ones carry Roman names, and
the great Roman trades (Sidonian purple, Baetican oil, Noric steel) are marked where they were."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b
import location_templates as lt

TEMPLATES = b.MOD / "in_game/map_data/location_templates.txt"
MODS = b.MOD / "main_menu/common/static_modifiers/tfe_roman_specialities.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_roman_specialities_l_english.yml"
RENAMES = b.MOD / "main_menu/localization/english/replace/tfe_roman_specialities_replace_l_english.yml"
FLAVOR = b.MOD / "main_menu/localization/english/replace/tfe_location_flavor_l_english.yml"
CITIES = b.MOD / "main_menu/localization/english/replace/tfe_city_flavor_l_english.yml"


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def ours():
    text = TEMPLATES.read_text(encoding="utf-8-sig")
    return (dict(re.findall(r"^(\w+) = \{ modifier = (\w+)", text, re.M)),
            dict(re.findall(r"^(\w+) = \{[^\n]*\braw_material = (\w+)", text, re.M)))


def test_no_speciality_from_after_395_is_left():
    mods, raw = ours()
    left = {l: m for l, m in mods.items() if m in lt.MEDIEVAL_MODIFIERS + lt.LATER_MODIFIERS}
    assert not left, left
    assert raw["taizz"] == raw["al_mukha"] == "incense"   # coffee reached Yemen in the 1400s; Muza shipped myrrh


def test_the_setup_gives_no_town_a_medieval_market_or_mine():
    # vanilla's 21_locations gave Malmo its herring market (c. 1200) and Freiberg its silver (1168)
    setup = (b.MOD / "main_menu/setup/start/21_locations.txt").read_text(encoding="utf-8")
    assert "locations" in setup and "modifier" not in re.sub(r"#[^\n]*", "", setup)
    assert not setup.startswith("﻿")   # start files take no BOM


def test_each_roman_speciality_boosts_the_good_its_town_produces():
    mods, raw = ours()
    defs = dict(re.findall(r"^(\w+) = \{(.*?)^\}", code(MODS), re.M | re.S))
    assert set(defs) == set(lt.ROMAN_SPECIALITIES.values())
    for loc, mod in lt.ROMAN_SPECIALITIES.items():
        assert mods.get(loc) == mod, (loc, mods.get(loc))
        effects = re.findall(r"^\t(\w+) = ([\d.]+)", defs[mod], re.M)
        assert effects == [(f"local_{raw[loc]}_output_modifier", effects[0][1])], (loc, mod, effects)   # one: the badge


def test_specialities_are_named_described_and_told():
    keys = set(re.findall(r"^\s*(\w+):", LOC.read_text(encoding="utf-8-sig"), re.M))
    for mod in set(lt.ROMAN_SPECIALITIES.values()):
        assert {f"STATIC_MODIFIER_NAME_{mod}", f"STATIC_MODIFIER_DESC_{mod}"} <= keys, mod
    told = set(re.findall(r"^ (\w+)_desc:", FLAVOR.read_text(encoding="utf-8-sig"), re.M))
    assert set(lt.ROMAN_SPECIALITIES) <= told
    renamed = dict(re.findall(r'^ STATIC_MODIFIER_NAME_(\w+): "(.*)"', RENAMES.read_text(encoding="utf-8-sig"), re.M))
    assert renamed["almaden_base"] == "Cinnabar of Sisapo" and renamed["srebrenica_silver_mines_base"]
    for f in (MODS, LOC, RENAMES):
        assert f.read_bytes().startswith(b"\xef\xbb\xbf"), f.name


def test_every_city_of_our_world_is_described_as_it_was_in_395():
    # vanilla describes its cities for 1337 (Damascus of the Umayyads, Venice the trading republic); the tooltip under
    # a speciality shows the town's own description, so each city in our 25 regions gets one for 395
    import place_names as pn
    anc = b.load_hierarchy()
    vanilla = set(re.findall(r"^ (\w+)_desc:", (b.GAME / "main_menu/localization/english/location_flavor_l_english.yml")
                             .read_text(encoding="utf-8-sig"), re.M))
    defined = {}
    for f in (b.MOD / "main_menu/localization/english").rglob("*.yml"):
        for k in re.findall(r"^ (\w+)_desc:", f.read_text(encoding="utf-8-sig"), re.M):
            if k in anc:
                assert k not in defined, (k, f.name, defined.get(k))   # one description per town
                defined[k] = f.name
    want = {l for l in vanilla if l in anc and anc[l][2] in pn.SCOPE}
    want |= {"almaden", "srebrenica", "turda"}   # renamed Roman specialities vanilla leaves undescribed
    assert not want - set(defined), sorted(want - set(defined))
    cities = CITIES.read_text(encoding="utf-8-sig")
    assert CITIES.read_bytes().startswith(b"\xef\xbb\xbf") and "Umayyad" not in cities and "Abbasid" not in cities
