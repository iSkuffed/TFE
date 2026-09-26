"""Migratory peoples: an army-based host gives up its homeland for a large host that costs nothing while landless."""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

COMMON = b.MOD / "in_game/common"
ACTIONS = COMMON / "generic_actions/tfe_migratory.txt"
AUTO = COMMON / "auto_modifiers/tfe_migratory.txt"
AI_LIST = COMMON / "generic_action_ai_lists/tfe_migratory_list.txt"
CB = COMMON / "casus_belli/tfe_migration.txt"
WARGOAL = COMMON / "wargoals/tfe_migration.txt"
SETTLE = COMMON / "on_action/tfe_migratory.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_migratory_l_english.yml"
ARMIES = b.MOD / "main_menu/setup/start/27_armies.txt"
SCRIPTS = (ACTIONS, AUTO, AI_LIST, CB, WARGOAL, SETTLE)
NEW_ACTIONS = ("tfe_start_migration",)


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def top_keys(p):
    return re.findall(r"^(\w+)\s*=\s*\{", code(p), re.M)


def test_scripts_are_bom_prefixed_and_balanced():
    for p in SCRIPTS + (LOC,):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in SCRIPTS + (ARMIES,):
        assert code(p).count("{") == code(p).count("}"), p.name


def test_start_migration_is_a_one_way_trip_for_hosts():
    acts = code(ACTIONS)
    assert top_keys(ACTIONS) == list(NEW_ACTIONS)
    assert "country_type = army" in acts and "country_type = pop" not in acts
    listed = re.search(r"actions = \{([^}]*)\}", code(AI_LIST)).group(1).split()
    assert listed == list(NEW_ACTIONS) and "country_type = army" in code(AI_LIST)
    potential = re.search(r"potential = \{(.*?)\n\t\}", acts, re.S).group(1)
    assert "NOT = { has_variable = tfe_migrating }" in potential   # once only: the host never comes back
    assert "set_variable = tfe_migrating" in acts and "every_owned_location" in acts and "abandon_location" in acts


def test_the_host_disbands_back_to_its_old_warband_once_it_takes_land():
    # user: force disband the special troops after the migration; otherwise one location has to pay 16,000 men
    on = code(SETTLE)
    assert re.search(r"on_location_changed_owner = \{\s*on_actions = \{\s*tfe_on_host_settles\s*\}", on)
    trigger = re.search(r"tfe_on_host_settles = \{\s*trigger = \{(.*?)\n\t\}", on, re.S).group(1)
    assert "has_variable = tfe_migrating" in trigger and "NOT = { has_variable = tfe_settled }" in trigger   # once
    assert "set_variable = tfe_settled" in on
    host = re.search(r"country = HAS.*?sub_units = \{(.*?)\n\t\t\}", code(ARMIES), re.S).group(1)
    # destroying sub-units one by one crashed the game a tick later; vanilla drops whole armies (destroy_unit)
    assert "destroy_subunit" not in on and "every_army = { destroy_unit = yes }" in on
    raised = re.findall(r"count = (\d+)\s*create_sub_unit_with_owner = \{ type = (\w+)", on)
    assert Counter({t: int(n) for n, t in raised}) == Counter(re.findall(r"(a_\w+) = \{", host))
    trigger = re.search(r"potential_trigger = \{(.*?)\n\t\}", code(AUTO), re.S).group(1)
    assert "NOT = { has_variable = tfe_settled }" in trigger   # losing the land again does not make it free


def test_camp_warband_and_their_prices_are_gone():
    # the host is finite by design: no replenishing, so no Make Camp / Raise Warband and nothing to price
    assert not (COMMON / "prices/tfe_prices.txt").exists()
    assert not (b.MOD / "main_menu/common/modifier_type_definitions/tfe_modifier_types.txt").exists()
    for p in SCRIPTS + (LOC,):
        assert not re.search(r"make_camp|raise_warband|tfe_camp", p.read_text(encoding="utf-8-sig")), p.name


def test_a_landless_migrating_host_is_free_to_keep_and_hardy():
    auto = code(AUTO)
    trigger = re.search(r"potential_trigger = \{(.*?)\n\t\}", auto, re.S).group(1)
    assert "has_variable = tfe_migrating" in trigger and "any_owned_location" in trigger   # off once it owns land
    # the per-category *_maintenance_cost_modifier values change nothing in the budget; efficiency e makes the
    # country pay 1 / (1 + e) of upkeep (seen in-game: -7.5% -> paying 108.1%, +99 -> paying 1.00%)
    efficiency = float(re.search(r"army_maintenance_efficiency = ([\d.]+)", auto).group(1))
    # at +99 (1%) the host still sank ~1 gold/month with no income to pay it
    assert 1 / (1 + efficiency) <= 0.002 and "maintenance_cost_modifier" not in auto
    assert float(re.search(r"land_unit_attrition = (-[\d.]+)", auto).group(1)) <= -0.9


def test_a_landless_host_has_a_cheap_casus_belli_for_new_land():
    # without one it can only declare a no-CB war: a heavy stability hit and a plain superiority goal
    cb = code(CB)
    assert top_keys(CB) == ["cb_tfe_migration"]
    visible = re.search(r"create_visible = \{(.*?)\n\t\}", cb, re.S).group(1)
    assert "has_variable = tfe_migrating" in visible and "any_owned_location" in visible   # gone once settled
    # the game never offers it on its own (a landless host has no neighbours to scan), so migrating grants it
    grants = re.findall(r"add_casus_belli = \{[^}]*target = c:(\w+)[^}]*type = casus_belli:cb_tfe_migration", code(ACTIONS))
    assert sorted(grants) == ["EAR", "WRE"], grants
    goal = re.search(r"war_goal_type = (\w+)", cb).group(1)
    assert top_keys(WARGOAL) == [goal] and "type = superiority" in code(WARGOAL)
    attacker = re.search(r"attacker = \{(.*?)\n\t\}", code(WARGOAL), re.S).group(1)
    assert float(re.search(r"conquer_cost = ([\d.]+)", attacker).group(1)) < 1   # land is the whole point


def test_warband_units_exist_in_vanilla():
    vanilla = set()
    for p in (b.GAME / "in_game/common/unit_types").glob("*.txt"):
        vanilla |= set(re.findall(r"^(\w+) = \{", p.read_text(encoding="utf-8-sig"), re.M))
    used = set(re.findall(r"type = (a_\w+)", code(ACTIONS))) | set(re.findall(r"\b(a_\w+) = \{", code(ARMIES)))
    assert used and used <= vanilla, used - vanilla


def test_everything_is_localized():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    wanted = {k for a in NEW_ACTIONS for k in (a, f"{a}_desc")}
    wanted |= set(re.findall(r"custom_tooltip = (\w+)", code(ACTIONS)))
    wanted |= {f"AUTO_MODIFIER_NAME_{k}" for k in top_keys(AUTO)}
    wanted |= {k for c in top_keys(CB) for k in (c, f"{c}_desc")}
    wanted |= {k for g in top_keys(WARGOAL) for k in (f"war_goal_{g}", f"war_goal_{g}_desc")}
    assert not wanted - keys, sorted(wanted - keys)


def test_vandal_host_starts_in_its_homeland():
    text = (b.MOD / "main_menu/setup/start/10_countries.txt").read_text(encoding="utf-8")
    block = text[text.index("\t\tHAS = {"):].split("\n\t\t}\n")[0]
    land = set(re.search(r"own_control_core = \{([^}]*)\}", block).group(1).split())
    hosts = re.findall(r"army = \{\s*country = HAS\s+location = (\w+)", code(ARMIES))
    assert hosts and set(hosts) <= land


def test_pop_based_leftovers_are_gone():
    # the first-age migration-law advance only served pop-based countries, which cannot be played
    assert not (COMMON / "advances/tfe_migratory_advances.txt").exists()


GUI = b.MOD / "in_game/gui/form_new_country.gui"
GUI_BEGIN, GUI_END = "\t\t\t\t\t# TFE: migratory host actions\n", "\t\t\t\t\t# TFE: end\n"


def test_host_actions_have_buttons_in_the_settle_panel():
    # owncountry actions are only reachable where a GUI file places a button for them by name
    text = GUI.read_text(encoding="utf-8")
    for a in NEW_ACTIONS:
        assert f'left_click_and_hold_action = {{ action_name = "{a}" }}' in text, a
    # the override is vanilla plus our one block, so a game patch that changes the file shows up here
    start, end = text.index(GUI_BEGIN), text.index(GUI_END) + len(GUI_END)
    assert text[:start] + text[end:] == (b.GAME / "in_game/gui/form_new_country.gui").read_text(encoding="utf-8")
