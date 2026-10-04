"""The hosts become kingdoms (script/barbarian_kingdoms.py): settlers spread with the land won, a settled host may move on
until it reforms into a monarchy, takes its subjects' tongue and faith, and the Salian Franks raid over the Rhine."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))
import barbarian_kingdoms as bk  # noqa: E402
import decisions  # noqa: E402
import decline_rome_events  # noqa: E402
import defs_defectors  # noqa: E402
import defs_migratory  # noqa: E402
import hunnic_storm_events  # noqa: E402
from pdx.core import fmt  # noqa: E402

DOC, EVENTS, CB, MODS = bk.build()
MUSTER, ENDING = bk.muster(), bk.on_actions()
START, SETTLE = defs_migratory.effects(), defs_migratory.on_actions()
_, _, FALL = decisions.build()
MIGRATE = ("tfe_migrate",)


def keys(nodes):
    return [n.key for n in nodes]


def test_settlers_scale_with_the_land_won():
    # the on_action waits a day, so the whole peace (or Hospitalitas) has handed over its land before anyone is counted
    fire = SETTLE.find("trigger_event_silently", inside=("tfe_on_host_settles", "scope:winner"))
    assert fire and fire[0].val is not None and {(n.key, n.val) for n in fire[0].val} == {("id", "tfe_barbarian_kingdoms.1"), ("days", "1")}
    assert not SETTLE.find("add_pop")
    ev = "tfe_barbarian_kingdoms.1"
    assert EVENTS.find("hidden", True, inside=ev) and EVENTS.find("has_variable", "tfe_host_people", inside=(ev, "trigger"))
    limit = EVENTS.find("num_locations", None, inside=(ev, "if", "limit"))
    assert limit[0].op == ">=" and limit[0].val == fmt(bk.FULL_AT * bk.MAX_SHARE)
    assert EVENTS.find("multiply", bk.MAX_SHARE, inside=(ev, "if")) and EVENTS.find("divide", "num_locations", inside=(ev, "if"))
    assert EVENTS.find("divide", bk.FULL_AT, inside=(ev, "else"))
    assert EVENTS.find("size", "root.var:tfe_host_share", inside=(ev, "every_owned_location", "add_pop"))
    assert EVENTS.find("remove_variable", "tfe_host_people", inside=ev)
    # what the branches add up to: people x min(locations / 5, 2) in all, spread evenly
    for n in range(1, 40):
        each = 1000 * bk.MAX_SHARE / n if n >= bk.FULL_AT * bk.MAX_SHARE else 1000 / bk.FULL_AT
        assert abs(each * n - 1000 * min(n / bk.FULL_AT, bk.MAX_SHARE)) < 1e-6, n


def test_one_muster_raises_the_host_for_migrants_and_franks():
    assert MUSTER.find("count", 24, inside=("tfe_muster_the_host_effect", "while"))
    assert MUSTER.find("type", "a_footmen", inside="tfe_muster_the_host_effect")
    assert MUSTER.find("type", "a_tribal_cavalry", inside="tfe_muster_the_host_effect")
    assert START.find("tfe_muster_the_host_effect", True, inside="tfe_start_migration_effect")
    assert not START.find("create_sub_unit_with_owner", inside="tfe_start_migration_effect")
    assert DOC.find("tfe_muster_the_host_effect", True, inside="tfe_cross_the_rhine")


def test_the_host_keeps_no_core_on_the_land_it_leaves():
    assert START.find("remove_core", "scope:tfe_host", inside=("tfe_start_migration_effect", "every_core_location"))


def test_no_cheap_cores_but_no_endless_integration():
    # accepting the land's tongue brings the capacity for it; the host's settled land integrates fast, for good
    assert DOC.find("add_country_modifier", None, inside=("tfe_accept_majority_culture", "effect"))
    assert MODS.find("cultures_capacity", bk.LORDS_CAPACITY, inside=bk.LORDS)
    assert EVENTS.find("add_location_modifier", None, inside=("tfe_barbarian_kingdoms.1", "immediate", "every_owned_location"))
    assert MODS.find("local_integration_speed_modifier", bk.SETTLED_INTEGRATION, inside=bk.SETTLED)
    # Rome's grant arrives integrated, never cored
    ev = decline_rome_events.build()
    assert ev.find("change_integration_level", "integrated")
    assert not ev.find("add_core")


def test_a_settled_host_may_move_on_until_it_is_a_kingdom():
    for n in MIGRATE:
        assert FALL.find("has_variable", "tfe_settled", inside=(n, "potential", "OR"))
        # a reformed host never migrates, whether or not it was ever on the road
        assert FALL.find("has_variable", "tfe_host_kingdom", inside=(n, "potential", "NOT"))
        assert not FALL.find("has_variable", "tfe_host_kingdom", inside=(n, "potential", "OR"))
        # the AI's settled hosts stay put
        assert FALL.find("has_variable", "tfe_settled", inside=(n, "ai_will_do", "limit", "NOT"))
    # then the host is on the road again: the settle hook, free upkeep, CB and defectors all key on NOT tfe_settled
    body = START.find("tfe_start_migration_effect")[0].val
    assert isinstance(body, list)
    removes = [i for i, n in enumerate(body) if n.key == "if" and isinstance(n.val, list)
               and any(c.key == "remove_variable" and c.val == "tfe_settled" for c in n.val)]
    assert removes and keys(body).index("every_country") < removes[0] < keys(body).index("tfe_list_the_migrators")


def test_the_reform_ends_the_road_and_opens_tongue_and_faith():
    r = "tfe_reform_into_a_monarchy"
    assert DOC.find("has_variable", "tfe_settled", inside=(r, "potential"))
    assert DOC.find("has_variable", "tfe_host_kingdom", inside=(r, "potential", "NOT"))
    assert DOC.find("change_government_type", "government_type:monarchy", inside=(r, "effect"))
    assert DOC.find("set_variable", "tfe_host_kingdom", inside=(r, "effect"))
    # the monarchy counts only from the next day, so the privilege comes a day later, with the Knights advance its
    # allow needs (rechecked on a change of faith, which revoked it in game)
    ev = "tfe_barbarian_kingdoms.2"
    assert DOC.find("id", ev, inside=(r, "effect", "trigger_event_silently"))
    assert EVENTS.find("grant_estate_privilege", "estate_privilege:auxilium_et_consilium", inside=(ev, "immediate", "if"))
    for adv in ("feudalism_advance", "noble_knights"):
        assert EVENTS.find("research_advance", f"advance_type:{adv}", inside=(ev, "immediate", "if"))
    for n, link, change in (("tfe_accept_majority_culture", "dominant_culture", "add_accepted_culture"),
                            ("tfe_convert_to_majority_religion", "dominant_religion", "change_religion")):
        assert DOC.find("only_once", True, inside=n) and DOC.find("has_variable", "tfe_host_kingdom", inside=(n, "potential"))
        assert DOC.find(link, None, inside=(n, "potential", "NOT")) and DOC.find("exists", link, inside=(n, "potential"))
        assert DOC.find(change, None, inside=(n, "effect"))
    # accepted beside our own, never swapped for it
    c = "tfe_accept_majority_culture"
    assert DOC.find("add_accepted_culture", "scope:tfe_new_culture", inside=(c, "effect"))
    assert not DOC.find("change_culture", None, inside=c)
    assert DOC.find("has_accepted_culture", "dominant_culture", inside=(c, "potential", "NOT"))
    assert DOC.find("change_religion_for_ruler_and_family", inside="tfe_convert_to_majority_religion")


def test_the_salians_cross_the_rhine_instead_of_migrating():
    for n in MIGRATE:
        assert FALL.find("tag", "SLF", inside=(n, "potential", "NOT"))
    assert hunnic_storm_events.build().find("tag", "SLF", inside=("tfe_hunnic_storm.2", "trigger", "NOT"))
    d = "tfe_cross_the_rhine"
    assert DOC.find("tag", "SLF", inside=(d, "potential"))
    assert DOC.find("situation_is_active", True, inside=(d, "potential"))
    assert DOC.find("at_war", False, inside=(d, "allow")) and DOC.find("is_subject", False, inside=(d, "allow"))
    assert DOC.find("has_variable", "tfe_crossed_the_rhine", inside=(d, "allow", "custom_tooltip", "NOT"))
    assert DOC.find("years", bk.RHINE_YEARS, inside=(d, "effect", "set_variable"))
    assert DOC.find("set_variable", bk.RHINE_WAR, inside=(d, "effect"))
    fx = keys(DOC.find("hidden_effect", inside=d)[0].val)   # type: ignore[arg-type]
    assert fx.index("set_variable") < fx.index("declare_war_with_cb")   # the CB is visible only while the raid is on
    assert DOC.find("type", f"casus_belli:{bk.RHINE_CB}", inside=(d, "declare_war_with_cb"))
    assert DOC.find("var:tfe_unity", None, inside=(d, "ai_will_do"))[0].op == "<"
    # the CB: the migration's war goal, only during the raid
    assert CB.find("has_variable", bk.RHINE_WAR, inside=(bk.RHINE_CB, "create_visible"))
    assert CB.find("war_goal_type", "superiority_tfe_migration", inside=bk.RHINE_CB)
    # free for that war only, fed by Roman towns, and the upkeep comes back when it ends
    auto = (ROOT / "in_game/common/auto_modifiers/tfe_migratory.txt").read_text(encoding="utf-8-sig")
    rhine = re.search(r"tfe_rhine_host = \{(.*?)\n\}", auto, re.S).group(1)
    assert "has_variable = tfe_rhine_war" in rhine and "at_war = yes" in rhine and "army_maintenance_efficiency = 999" in rhine
    assert defs_defectors.on_actions().find("has_variable", bk.RHINE_WAR, inside=("tfe_on_host_takes_roman_town", "trigger", "OR"))
    assert ENDING.find("on_actions", inside="on_ending_war") and ENDING.find("remove_variable", bk.RHINE_WAR, inside="tfe_on_rhine_war_ended")


def test_everything_new_is_localised():
    loc = DOC.loc.keys
    shown = {n.val for n in DOC.find("custom_tooltip") if isinstance(n.val, str)}
    shown |= {n.val for n in DOC.find("text", inside="custom_tooltip")}
    assert shown and not shown - loc.keys(), sorted(shown - loc.keys())
    assert {bk.RHINE_CB, f"{bk.RHINE_CB}_desc", "AUTO_MODIFIER_NAME_tfe_rhine_host"} <= loc.keys()
    for n in ("tfe_reform_into_a_monarchy", "tfe_accept_majority_culture", "tfe_convert_to_majority_religion", "tfe_cross_the_rhine"):
        assert {f"{n}.title", f"{n}.desc", f"{n}.a"} <= loc.keys()
    assert not loc.keys() & FALL.loc.keys   # new keys live in their own file


def test_the_homeland_becomes_a_remnant_not_a_neighbours_prize():
    eff = ("tfe_start_migration_effect",)
    assert START.find("create_country_from_location", None, inside=eff)
    assert not START.find("save_scope_as", "tfe_heir_to_the_land", inside=eff)
    assert not START.find("random_neighbor_country", None, inside=eff)
    assert START.find("change_location_owner", "scope:tfe_remnant", inside=eff)
    assert START.find("add_core", "scope:tfe_remnant", inside=eff)
    # only once the remnant is real: a tooltip's dry run makes none, and add_core on the capital spammed error.log
    assert START.find("set_variable", "tfe_left_a_remnant", inside=(*eff, "create_country_from_location", "scope:tfe_host"))
    assert START.find("add_core", "scope:tfe_remnant", inside=(*eff, "if", "every_owned_location"))
    assert START.find("has_variable", "tfe_left_a_remnant", inside=(*eff, "if", "limit"))
    assert START.find("add_core", "scope:tfe_remnant", inside=(*eff, "if", "scope:tfe_old_capital"))   # its capital too


def test_the_remnant_is_of_the_people_who_stayed():
    new = ("tfe_start_migration_effect", "create_country_from_location")
    assert START.find("change_culture", "scope:tfe_old_capital.dominant_culture", inside=new)
    assert START.find("change_religion", "scope:tfe_host.religion", inside=new)
    assert START.find("change_government_type", "government_type:tribe", inside=new)
    assert START.find("set_variable", None, inside=new)[0].val is not None
    assert START.find("save_scope_as", "tfe_remnant", inside=new)


def test_a_landless_host_leaves_no_remnant_and_abandons_nothing_it_does_not_hold():
    ifs = START.find("if", None, inside=("tfe_start_migration_effect",))
    assert any("capital" in str(i.val) and "create_country_from_location" in str(i.val) for i in ifs)
    assert START.find("abandon_location", None, inside=("tfe_start_migration_effect", "else"))
