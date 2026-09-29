"""Hunnic raiders: the Huns take captives from every land they occupy (vanilla's slave raid), for good from day one."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

MODIFIER = b.MOD / "main_menu/common/static_modifiers/tfe_hunnic_raiders.txt"
ON_ACTION = b.MOD / "in_game/common/on_action/tfe_hunnic_raiders.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_hunnic_raiders_l_english.yml"
SCRIPTS = (MODIFIER, ON_ACTION)


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def test_files_are_balanced_and_bom_prefixed():
    for p in SCRIPTS + (LOC,):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in SCRIPTS:
        assert code(p).count("{") == code(p).count("}"), p.name


def test_the_huns_raid_for_good_from_day_one():
    m = code(MODIFIER)
    # auto_slave_raid (not the _different_religion one) also shows vanilla's slave-raiding casus belli
    assert "auto_slave_raid = yes" in m and "category = country" in m
    assert re.search(r"slave_raid_efficiency = 0\.\d+", m)
    on = code(ON_ACTION)
    assert re.search(r"on_game_start = \{\s*on_actions = \{ tfe_on_start_hunnic_raiders \}", on)
    # no years/months: it never runs out
    assert "c:HNS ?= { add_country_modifier = { modifier = tfe_hunnic_raiders } }" in on


def test_occupied_lands_give_up_captives_to_the_capital():
    on = code(ON_ACTION)
    for hook in ("on_location_occupied", "on_siege_won"):
        assert re.search(hook + r" = \{\s*on_actions = \{ tfe_on_hunnic_raid \}", on), hook
    # the pop_type: prefix is required: a bare `pop_type = peasants` is an invalid comparison, matching nothing
    assert "pop_type = pop_type:peasants" in on and "pop_type = pop_type:laborers" in on
    assert re.search(r"split_pop = \{ fraction = 0\.\d+ type = pop_type:slaves location = root\.capital \}", on)


def test_everything_shown_is_localized():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    assert {"STATIC_MODIFIER_NAME_tfe_hunnic_raiders", "STATIC_MODIFIER_DESC_tfe_hunnic_raiders"} <= keys


def test_the_horde_pays_a_tenth_of_army_upkeep_for_good():
    m = re.search(r"tfe_hunnic_horde = \{(.*?)\n\}", code(MODIFIER), re.S).group(1)
    assert "category = country" in m and "army_maintenance_efficiency = 9" in m   # 1 / (1 + 9) = 10% paid
    assert "c:HNS ?= { add_country_modifier = { modifier = tfe_hunnic_horde } }" in code(ON_ACTION)
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    assert {"STATIC_MODIFIER_NAME_tfe_hunnic_horde", "STATIC_MODIFIER_DESC_tfe_hunnic_horde"} <= keys


def test_the_huns_start_with_about_20000_horse_archers_and_four_supply_carts_at_a_town_capital():
    armies = (b.MOD / "main_menu/setup/start/27_armies.txt").read_text(encoding="utf-8")
    host = re.search(r"country = HNS\s+location = adalaga\s+sub_units = \{(.*?)\n\t\t\}", armies, re.S).group(1)
    assert host.count("a_steppe_horse_archers = { strength = 1 }") * 600 == 19800   # a horse archer regiment is 600 men
    assert host.count("a_supply_carts = { strength = 1 }") == 4
    tags = (b.TOOLS / "tags.txt").read_text(encoding="utf-8")
    assert re.search(r"^HNS \| Huns \| Hunnic \| adalaga \|", tags, re.M)
    start = b.MOD / "main_menu/setup/start/07_cities_and_buildings.txt"
    text = start.read_text(encoding="utf-8")
    assert re.search(r"adalaga = \{ rank = town ", text)
    assert "barracks = { tag = HNS level = 1 location = adalaga }" in text
