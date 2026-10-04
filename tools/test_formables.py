"""The kingdoms that may rise: no tribe forms a European nation, and Germania, Portugal and the Holy Roman Empire are ours."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b
import formables as f

FORMABLES = (b.MOD / "in_game/common/formable_countries/00_formable_countries.txt").read_text(encoding="utf-8-sig")
NAMES = b.MOD / "main_menu/localization/english/replace"


E = {k: FORMABLES[s:e] for k, s, e in f.blocks(FORMABLES)}


def test_every_european_formable_refuses_tribes():
    """Europe = most of the required locations lie on vanilla's europe continent."""
    defs = f.definitions(b.MAP / "definitions.txt")
    missing = [k for k, body in E.items() if f.in_europe(body, defs) and "has_tribal_government = no" not in f.sub(body, "allow")]
    assert not missing, f"European formables a tribe could form: {missing}"


def test_netherlands_is_never_offered():
    assert re.search(r"^\t\talways = no", f.sub(E["NED_f"], "potential"), re.M)


def test_portugal_is_a_kingdom():
    p = E["POR_f"]
    assert "level = 3" in p and "rank_kingdom" in p and "country_rank_level < 3" in p
    assert {"north_portugal_area", "south_portugal_area"} <= set(f.sub(p, "areas").split())
    assert "culture" not in f.sub(p, "potential") and "christian" not in f.sub(p, "potential")


def test_germania_is_a_kingdom():
    g = E["GER_f"]
    assert "level = 3" in g and "rank_kingdom" in g and "rank_empire" not in g
    assert set(f.sub(g, "regions").split()) == {"north_german_region", "south_german_region"}
    loc = (NAMES / "tfe_formables_l_english.yml").read_text(encoding="utf-8-sig")
    for key, value in (("GER_f", "Germania"), ("GER", "Germania"), ("GER_ADJ", "Germanic")):
        assert f' {key}: "{value}"' in loc


def test_holy_roman_empire_is_an_empire_without_the_io():
    h = E["HRE_f"]
    assert "level = 4" in h and "rank_empire" in h and "country_rank_level < 4" in h
    assert set(f.sub(h, "regions").split()) == {"north_german_region", "south_german_region", "france_region"}
    assert "international_organization" not in h and "always = no" not in f.sub(h, "allow")
    assert "religion_group:christian" in f.sub(h, "potential")


def test_region_names_carry_no_title():
    loc = (NAMES / "tfe_place_names_l_english.yml").read_text(encoding="utf-8-sig")
    want = {"crescent": "Oriens", "egypt": "Aegyptus", "ethiopia": "Aksum", "france": "Gallia", "great_britain": "Britannia",
            "iberia": "Hispania", "italy": "Italia", "maghreb": "Africa", "north_german": "Germania"}
    for region, name in want.items():
        assert f' {region}_region: "{name}"' in loc
    titled = re.findall(r'^ (\w+_region): "((?:Diocese|Kingdom|Free |Empire)[^"]*)"', loc, re.M)
    assert not titled, titled
