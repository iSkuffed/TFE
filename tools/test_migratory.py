"""Migratory peoples: army-based hosts that wander and make camp (Make Camp, Raise Warband)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

COMMON = b.MOD / "in_game/common"
ACTIONS = COMMON / "generic_actions/tfe_migratory.txt"
PRICES = COMMON / "prices/tfe_prices.txt"
AI_LIST = COMMON / "generic_action_ai_lists/tfe_migratory_list.txt"
MODTYPES = b.MOD / "main_menu/common/modifier_type_definitions/tfe_modifier_types.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_migratory_l_english.yml"
ARMIES = b.MOD / "main_menu/setup/start/27_armies.txt"
SCRIPTS = (ACTIONS, PRICES, AI_LIST, MODTYPES)
NEW_ACTIONS = ("tfe_make_camp", "tfe_raise_warband")


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def top_keys(p):
    return re.findall(r"^(\w+)\s*=\s*\{", code(p), re.M)


def test_scripts_are_bom_prefixed_and_balanced():
    for p in SCRIPTS + (LOC,):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in SCRIPTS + (ARMIES,):
        assert code(p).count("{") == code(p).count("}"), p.name


def test_actions_are_for_hosts_priced_and_known_to_the_ai():
    acts = code(ACTIONS)
    assert set(top_keys(ACTIONS)) == set(NEW_ACTIONS)
    assert acts.count("country_type = army") == len(NEW_ACTIONS) and "country_type = pop" not in acts
    assert "country_type = army" in code(AI_LIST)
    assert set(re.findall(r"price:(\w+)", acts)) == set(NEW_ACTIONS) == set(top_keys(PRICES))
    assert {f"{a}_cost_modifier" for a in NEW_ACTIONS} == set(re.findall(r"^(\w+)\s*=", code(MODTYPES), re.M))
    listed = re.search(r"actions = \{([^}]*)\}", code(AI_LIST)).group(1).split()
    assert set(listed) == set(NEW_ACTIONS)
    # a camp is only ever planted on empty land and only the old camp is given up
    assert "has_owner = no" in acts and "abandon_location" in acts and "tfe_camp" in acts


def test_warband_units_exist_in_vanilla():
    vanilla = set()
    for p in (b.GAME / "in_game/common/unit_types").glob("*.txt"):
        vanilla |= set(re.findall(r"^(\w+) = \{", p.read_text(encoding="utf-8-sig"), re.M))
    used = set(re.findall(r"type = (a_\w+)", code(ACTIONS))) | set(re.findall(r"\b(a_\w+) = \{", code(ARMIES)))
    assert used and used <= vanilla, used - vanilla


def test_everything_is_localized():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    wanted = {k for a in NEW_ACTIONS for k in (a, f"{a}_desc", f"MODIFIER_TYPE_NAME_{a}_cost_modifier",
                                               f"MODIFIER_TYPE_DESC_{a}_cost_modifier")}
    wanted |= set(re.findall(r"custom_tooltip = (\w+)", code(ACTIONS)))
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
