"""The Fall of the West's Native Decisions (script/decisions.py): Migrate into Rome and Support Stilicho's Claims."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))
import decisions  # noqa: E402
import defs_usurpers  # noqa: E402
import defs_western_rome  # noqa: E402

CATS, DOC, ACTS = decisions.build()
LOC = DOC.loc.keys


def find(name, key=None, val=None, *inside):
    return DOC.find(key, val, inside=(name, *inside))


def mod_loc():
    out = set()
    for p in (ROOT / "main_menu/localization/english").rglob("*.yml"):
        out |= set(re.findall(r"^\s+([\w.\-]+):\d*\s", p.read_text(encoding="utf-8-sig"), re.M))
    return out


def test_one_category_near_the_top_holds_them_all():
    assert CATS.find("sort_order", 0, inside="tfe_fall_of_the_west") and "tfe_fall_of_the_west" in LOC
    names = [n.key for n in DOC.nodes if n.key]
    assert names == ["tfe_illyricum_claims", "tfe_debug_stilicho_glory"]
    for n in names:
        assert find(n, "decision_category", "tfe_fall_of_the_west")
        assert {f"{n}.title", f"{n}.desc", f"{n}.a"} <= LOC.keys()
        assert find(n, "image")   # a flat illustration, not the capital's scene


def test_every_tooltip_is_localised():
    keys = mod_loc()
    shown = {n.val for d in (DOC, ACTS) for n in d.find("custom_tooltip") if isinstance(n.val, str)}
    shown |= {n.val for d in (DOC, ACTS) for n in d.find("text", inside="custom_tooltip")}
    assert shown and not shown - keys, sorted(shown - keys)


def act(key=None, val=None, *inside):
    return ACTS.find(key, val, inside=("tfe_migrate", *inside))


def test_one_migration_shown_in_the_decisions_tab():
    """Migrate into Rome is a Native Decision: a generic action in the decisions tab, replacing the East / West pair."""
    assert [n.key for n in ACTS.nodes if n.key] == ["tfe_migrate"]
    assert act("type", "owncountry") and act("show_in_decision_panel", True)
    assert act("decision_category", "tfe_fall_of_the_west")
    assert {"tfe_migrate", "tfe_migrate_desc", "tfe_migrate_choose_rome", "tfe_migrate_no_rome"} <= LOC.keys()


def test_migration_is_offered_while_any_roman_state_stands():
    assert act("tfe_is_roman_state", True, "potential", "any_country")
    assert not ACTS.find(None, "c:WRE") and not ACTS.find(None, "c:EAR")   # no Rome is named: every Roman state counts
    assert act("situation_is_active", True, "potential", "situation:tfe_decline_of_the_west")
    assert act("tfe_is_migrator", True, "potential", "scope:actor")
    assert act("has_variable", "tfe_migrating", "potential", "scope:actor", "NOT")   # once only, unless settled


def test_the_picker_lists_every_roman_state_that_holds_land():
    sel = "select_trigger"
    assert act("looking_for_a", "country", sel) and act("target_flag", "target_rome", sel)
    assert act("tfe_is_roman_state", True, sel, "interaction_source_list", "every_country", "limit")
    assert act("tfe_is_roman_state", True, sel, "visible") and act("any_owned_location", None, sel, "visible")
    assert act("name", '"tfe_migrate_choose_rome"', sel) and act("none_available_msg_key", '"tfe_migrate_no_rome"', sel)


def test_migration_waits_a_month_and_for_an_open_frontier():
    start = re.search(r'START_DATE = "395\.1\.(\d+)"',
                      (ROOT / "loading_screen/common/defines/tfe_defines.txt").read_text(encoding="utf-8-sig")).group(1)
    date = act("current_date", None, "allow", "custom_tooltip")
    assert date[0].op == ">=" and date[0].val == f"395.2.{start}"
    assert act("text", "tfe_migration_not_yet_tt", "allow", "custom_tooltip")
    assert act("is_subject", False, "allow") and act("tfe_frontier_unmanned", True, "allow")
    assert not act("any_army")   # most peoples start with no warband afield; the host gathers at the capital


def test_migration_starts_the_host_then_declares_war_on_the_chosen_rome():
    fx = [x.key for x in act(None, None, "effect", "hidden_effect", "scope:actor")]
    assert fx.index("tfe_start_migration_effect") < fx.index("declare_war_with_cb")
    assert act("target", "scope:target_rome", "effect", "declare_war_with_cb")
    assert act("type", "casus_belli:cb_tfe_migration", "effect", "declare_war_with_cb")


def test_the_ai_takes_the_road_one_people_at_a_time_and_prefers_its_neighbour():
    assert act("value", 0, "ai_will_do") and act("ai_tick", "monthly")
    assert act("has_global_variable", "tfe_host_took_the_road", "ai_will_do", "limit", "NOT")
    assert sorted(int(x.val) for x in act("add", None, "ai_will_do")) == [5, 10, 25, 45]
    assert act("tfe_is_under_the_yoke", True, "ai_will_do")
    assert act("var:tfe_unity", None, "ai_will_do")[0].op == "<"
    assert act("this", "scope:target_rome", "ai_will_do", "any_neighbor_country")   # the one across the river


def test_every_roman_state_gives_the_host_its_casus_belli():
    fx = (ROOT / "in_game/common/scripted_effects/tfe_migratory.txt").read_text(encoding="utf-8-sig")
    assert "limit = { tfe_is_roman_state = yes }" in fx and "c:EAR" not in fx


def test_successors_of_rome_are_roman_states():
    tr = defs_western_rome.triggers()
    assert tr.find("tfe_is_roman_empire", True, inside=("tfe_is_roman_state", "OR"))
    assert tr.find("has_variable", "tfe_roman_successor", inside=("tfe_is_roman_state", "OR"))
    oa = defs_usurpers.on_actions()
    assert oa.find("tfe_on_revolt_against_rome", inside=("on_revolt_start", "on_actions"))
    assert oa.find("tfe_is_roman_state", True, inside=("tfe_on_revolt_against_rome", "trigger"))
    assert oa.find("has_culture_group", "culture_group:greek_group",
                   inside=("tfe_on_revolt_against_rome", "trigger", "scope:target", "culture"))
    assert oa.find("set_variable", "tfe_roman_successor", inside=("tfe_on_revolt_against_rome", "effect", "scope:target"))
    # Gildo's Africa breaks away by no revolt: it is marked where it is made
    assert defs_usurpers.effects().find("set_variable", "tfe_roman_successor",
                                        inside=("tfe_africa_breaks_away", "create_country_from_location"))


def test_stilichos_claims_need_him_alive_and_ten_quiet_years_but_no_unity():
    n = "tfe_illyricum_claims"
    assert find(n, "tag", "WRE", "potential") and find(n, "country_exists", "c:EAR", "potential")
    assert find(n, "exists", "international_organization:tfe_roman_empire", "potential")
    assert find(n, "tfe_stilicho_serves_us", True, "allow", "custom_tooltip")
    assert find(n, "has_variable", "tfe_illyricum_claim", "allow", "custom_tooltip", "NOT")
    # user: no Unity minimum, it is a way to drive Unity down on purpose
    assert not [x for x in find(n, None, None, "allow") if "unity" in str(x.key) + str(x.val)]
    assert int(find(n, "value", None, "ai_will_do")[0].val) < 0   # the player's choice, never the AI's


def test_stilichos_claims_cost_ten_unity_on_the_empire_itself_for_a_ten_year_cb():
    n = "tfe_illyricum_claims"
    assert find(n, "years", 10, "effect", "set_variable") and find(n, "name", "tfe_illyricum_claim", "effect", "set_variable")
    assert find(n, "type", "casus_belli:cb_tfe_illyrian_claim", "effect", "add_casus_belli")
    assert find(n, "years", 10, "effect", "add_casus_belli") and find(n, "target", "c:EAR", "effect", "add_casus_belli")
    assert find(n, "add", -10, "effect", "international_organization:tfe_roman_empire", "change_variable")
    assert find(n, "custom_tooltip", "tfe_unity_down_10_tt", "effect")
    assert not DOC.find("scope:recipient") and not DOC.find("scope:actor")   # root is the country now


def test_the_buttons_are_gone_but_align_the_visigoths_stays():
    ga = (ROOT / "in_game/common/generic_actions/tfe_roman_empire.txt").read_text(encoding="utf-8-sig")
    assert re.findall(r"^(\w+) = \{", ga, re.M) == ["tfe_align_visigoths"]
    assert not (ROOT / "in_game/common/generic_actions/tfe_migratory.txt").exists()
    old = {"tfe_migrate_east", "tfe_migrate_west", "tfe_illyricum_claims", "tfe_migrate_EAR_tt", "tfe_migrate_WRE_tt"}
    assert not old & mod_loc()   # the decisions' keys are <name>.title, not the buttons' <name>


def test_the_glory_shortcut_is_for_debug_mode_only():
    assert find("tfe_debug_stilicho_glory", "debug_only", "yes")
