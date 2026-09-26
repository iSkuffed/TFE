"""Migratory peoples: pop-based tribes that wander with their host (Make Camp, Raise Warband)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

COMMON = b.MOD / "in_game/common"
ACTIONS = COMMON / "generic_actions/tfe_migratory.txt"
PRICES = COMMON / "prices/tfe_prices.txt"
AI_LIST = COMMON / "generic_action_ai_lists/tfe_migratory_list.txt"
ADVANCE = COMMON / "advances/tfe_migratory_advances.txt"
MODTYPES = b.MOD / "main_menu/common/modifier_type_definitions/tfe_modifier_types.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_migratory_l_english.yml"
ARMIES = b.MOD / "main_menu/setup/start/27_armies.txt"
SCRIPTS = (ACTIONS, PRICES, AI_LIST, ADVANCE, MODTYPES)
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


def test_actions_are_pop_based_priced_and_known_to_the_ai():
    acts = code(ACTIONS)
    assert set(top_keys(ACTIONS)) == set(NEW_ACTIONS)
    assert acts.count("country_type = pop") == len(NEW_ACTIONS)
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


def test_migration_law_unlocked_in_the_first_age():
    adv = code(ADVANCE)
    assert "age = age_1_traditions" in adv and "unlock_law = tribal_migration_law" in adv


def test_everything_is_localized():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    wanted = {k for a in NEW_ACTIONS for k in (a, f"{a}_desc", f"MODIFIER_TYPE_NAME_{a}_cost_modifier",
                                               f"MODIFIER_TYPE_DESC_{a}_cost_modifier")}
    wanted |= {k for a in top_keys(ADVANCE) for k in (a, f"{a}_desc")}
    wanted |= set(re.findall(r"custom_tooltip = (\w+)", code(ACTIONS)))
    assert not wanted - keys, sorted(wanted - keys)


def test_vandal_host_starts_among_its_people():
    text = (b.MOD / "main_menu/setup/start/10_countries.txt").read_text(encoding="utf-8")
    block = text[text.index("\t\tHAS = {"):].split("\n\t\t}\n")[0]
    people = set(re.search(r"add_pops_from_locations = \{([^}]*)\}", block).group(1).split())
    hosts = re.findall(r"army = \{\s*country = HAS\s+location = (\w+)", code(ARMIES))
    assert hosts and set(hosts) <= people
