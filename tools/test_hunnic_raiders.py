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
