"""The Fall of the West decisions (script/decisions.py): Migrate into the East / West and Support Stilicho's Claims."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))
import decisions  # noqa: E402

CATS, DOC = decisions.build()
LOC = DOC.loc.keys


def find(name, key=None, val=None, *inside):
    return DOC.find(key, val, inside=(name, *inside))


def mod_loc():
    out = set()
    for p in (ROOT / "main_menu/localization/english").rglob("*.yml"):
        out |= set(re.findall(r"^\s+([\w.\-]+):\d*\s", p.read_text(encoding="utf-8-sig"), re.M))
    return out


def test_one_category_near_the_top_holds_all_three():
    assert CATS.find("sort_order", 0, inside="tfe_fall_of_the_west") and "tfe_fall_of_the_west" in LOC
    names = [n.key for n in DOC.nodes if n.key]
    assert names == ["tfe_migrate_east", "tfe_migrate_west", "tfe_illyricum_claims", "tfe_debug_stilicho_glory"]
    for n in names:
        assert find(n, "decision_category", "tfe_fall_of_the_west")
        assert {f"{n}.title", f"{n}.desc", f"{n}.a"} <= LOC.keys()
        assert find(n, "image")   # a flat illustration, not the capital's scene


def test_every_tooltip_is_localised():
    keys = mod_loc()
    shown = {n.val for n in DOC.find("custom_tooltip") if isinstance(n.val, str)}
    shown |= {n.val for n in DOC.find("text", inside="custom_tooltip")}
    assert shown and not shown - keys, sorted(shown - keys)


def test_each_migration_is_hidden_once_its_rome_is_gone():
    assert find("tfe_migrate_east", "country_exists", "c:EAR", "potential")
    assert find("tfe_migrate_west", "tfe_is_western_rome", True, "potential", "any_country")
    assert not DOC.find(None, "c:WRE") and not DOC.find("c:WRE")   # Stilicho's West counts as the West too
    for n in ("tfe_migrate_east", "tfe_migrate_west"):
        assert find(n, "situation_is_active", True, "potential", "situation:tfe_decline_of_the_west")
        assert find(n, "tfe_is_migrator", True, "potential")
        assert find(n, "has_variable", "tfe_migrating", "potential", "NOT")   # once only: the host never comes back


def test_migration_waits_a_month_and_for_an_open_frontier():
    start = re.search(r'START_DATE = "395\.1\.(\d+)"',
                      (ROOT / "loading_screen/common/defines/tfe_defines.txt").read_text(encoding="utf-8-sig")).group(1)
    for n in ("tfe_migrate_east", "tfe_migrate_west"):
        date = find(n, "current_date", None, "allow", "custom_tooltip")
        assert date[0].op == ">=" and date[0].val == f"395.2.{start}"
        assert find(n, "text", "tfe_migration_not_yet_tt", "allow", "custom_tooltip")
        assert find(n, "is_subject", False, "allow") and find(n, "tfe_frontier_unmanned", True, "allow")
        assert not find(n, "any_army")   # most peoples start with no warband afield; the host gathers at the capital


def test_migration_starts_the_host_then_declares_war_on_the_right_rome():
    for n, victim in (("tfe_migrate_east", "c:EAR"), ("tfe_migrate_west", "scope:tfe_victim")):
        fx = find(n, None, None, "option", "effect", "hidden_effect")
        keys = [x.key for x in fx]
        assert keys.index("tfe_start_migration_effect") < keys.index("declare_war_with_cb")
        assert find(n, "target", victim, "option", "effect", "declare_war_with_cb")
        assert find(n, "type", "casus_belli:cb_tfe_migration", "option", "effect", "declare_war_with_cb")
    # the West: the western Rome next door, else the richest one
    assert find("tfe_migrate_west", "tfe_is_western_rome", True, "random_neighbor_country", "limit")
    assert find("tfe_migrate_west", "order_by", "country_economical_base", "ordered_country")
    fx = [x.key for x in find("tfe_migrate_west", None, None, "hidden_effect")]
    assert fx.index("save_scope_as") < fx.index("tfe_start_migration_effect")


def test_the_ai_takes_the_road_one_people_at_a_time():
    for n in ("tfe_migrate_east", "tfe_migrate_west"):
        assert find(n, "value", 0, "ai_will_do")
        assert find(n, "has_global_variable", "tfe_host_took_the_road", "ai_will_do", "limit", "NOT")
        adds = sorted(int(x.val) for x in find(n, "add", None, "ai_will_do"))
        assert adds == [5, 10, 25, 45]
        assert find(n, "tfe_is_under_the_yoke", True, "ai_will_do")
        assert find(n, "var:tfe_unity", None, "ai_will_do")[0].op == "<"


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
    old = {"tfe_migrate_east", "tfe_migrate_west", "tfe_illyricum_claims"}
    assert not old & mod_loc()   # the decisions' keys are <name>.title, not the buttons' <name>


def test_the_glory_shortcut_is_for_debug_mode_only():
    assert find("tfe_debug_stilicho_glory", "debug_only", "yes")
