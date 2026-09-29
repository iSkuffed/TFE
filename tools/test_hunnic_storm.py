"""The Hunnic Storm (RoadMap #10): a situation, the Hunnic Yoke IO and its wars. Static checks: the scripts load."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

COMMON = b.MOD / "in_game/common"
SITUATION = COMMON / "situations/tfe_hunnic_storm.txt"
YOKE = COMMON / "international_organizations/tfe_hunnic_yoke.txt"
STATUS = COMMON / "international_organization_special_statuses/tfe_hunnic_yoke.txt"
TRIBUTE = COMMON / "international_organization_payments/tfe_hunnic_tribute.txt"
PRICE = COMMON / "prices/tfe_hunnic_storm.txt"
CB = COMMON / "casus_belli/tfe_hunnic_storm.txt"
WARGOAL = COMMON / "wargoals/tfe_hunnic_storm.txt"
TREATY = COMMON / "peace_treaties/tfe_hunnic_storm.txt"
ACTIONS = COMMON / "generic_actions/tfe_hunnic_storm.txt"
RAID = COMMON / "generic_actions/tfe_hunnic_raid.txt"
TRAIT = COMMON / "traits/tfe_scourge_of_god.txt"
ON_ACTION = COMMON / "on_action/tfe_hunnic_storm.txt"
MIGRATION = COMMON / "scripted_effects/tfe_migratory.txt"
END = COMMON / "scripted_triggers/tfe_hunnic_storm.txt"
EVENT = b.MOD / "in_game/events/tfe_hunnic_storm.txt"
MODIFIER = b.MOD / "main_menu/common/static_modifiers/tfe_hunnic_storm.txt"
PANEL = b.MOD / "in_game/gui/panels/situation/tfe_hunnic_storm.gui"
LOC = b.MOD / "main_menu/localization/english/tfe_hunnic_storm_l_english.yml"
START = b.MOD / "main_menu/setup/start"
SCRIPTS = (SITUATION, END, YOKE, STATUS, TRIBUTE, PRICE, CB, WARGOAL, TREATY, ACTIONS, RAID, TRAIT, ON_ACTION, MIGRATION, EVENT,
           MODIFIER)
TRIBUTARIES = {"ANE", "CRP", "MRD", "IMK", "SRT"}


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def top_keys(p):
    return re.findall(r"^(\w+)\s*=\s*\{", code(p), re.M)


def test_files_are_balanced_and_bom_prefixed():
    for p in SCRIPTS + (LOC,):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in SCRIPTS + (PANEL,):
        assert code(p).count("{") == code(p).count("}"), p.name


def test_everything_shown_is_localized():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    wanted = {"tfe_hunnic_storm", "tfe_hunnic_storm_desc", "tfe_hunnic_yoke", "tfe_hunnic_yoke_desc",
              "tfe_hunnic_yoke_LEADER_MALE", "tfe_hunnic_yoke_LEADER_FEMALE"}
    wanted |= {f"TFE_STORM_PHASE_{n}{d}" for n in (1, 2, 3) for d in ("", "_DESC")}
    wanted |= {k for s in top_keys(STATUS) for k in (s, f"{s}_plural", f"{s}_desc")}
    wanted |= {k for p in top_keys(TRIBUTE) for k in (p, f"{p}_desc")} | set(top_keys(PRICE))
    wanted |= {k for c in top_keys(CB) for k in (c, f"{c}_desc")}
    wanted |= {k for g in top_keys(WARGOAL) for k in (f"war_goal_{g}", f"war_goal_{g}_desc")}
    wanted |= {k for t in top_keys(TREATY) for k in (t, f"{t}_entry", f"{t}_entry_short", f"{t}_desc")}
    wanted |= {k for a in top_keys(ACTIONS) + top_keys(RAID) for k in (a, f"{a}_desc")}
    wanted |= {k for t in top_keys(TRAIT) for k in (t, f"desc_{t}", f"{t}_die_desc")}
    wanted |= {f"STATIC_MODIFIER_{k}_{m}" for m in top_keys(MODIFIER) for k in ("NAME", "DESC")}
    for p in SCRIPTS:
        text = code(p)
        wanted |= set(re.findall(r'desc = "(\w+)"', text))
        wanted |= set(re.findall(r"custom_tooltip = (?:\{\s*text = )?(\w+)", text))
    wanted |= set(re.findall(r"(?:title|desc|name) = (tfe_hunnic_storm\.[\w.]+)", code(EVENT)))
    wanted |= set(re.findall(r'text = "(TFE_\w+)"', code(PANEL)))
    wanted -= {"UPKEEP_BASE_VALUE", "DIPLOREASON_BASE", "tfe_start_migration_tt"}   # vanilla's and tfe_migratory's
    assert not wanted - keys, sorted(wanted - keys)


def test_the_yoke_is_seeded_with_the_huns_and_their_tributaries():
    setup = code(START / "15_international_organizations.txt")
    m = re.search(r"type = tfe_hunnic_yoke.*?members = \{([^}]*)\}\s*tfe_hunnic_overlord = \{\s*HNS\s*\}", setup, re.S)
    assert m and set(m.group(1).split()) == {"HNS"}      # the tribes are the Huns' subjects, not members
    dip = code(START / "12_diplomacy.txt")
    assert set(re.findall(r"first = HNS second = (\w+) subject_type = tributary", dip)) == TRIBUTARIES
    assert not (START / "12_diplomacy.txt").read_bytes().startswith(b"\xef\xbb\xbf")
    yoke = code(YOKE)
    assert re.search(r"payments_implemented = \{\s*tfe_hunnic_tribute\s*\}", yoke)
    assert re.search(r"special_statuses_implemented = \{\s*tfe_hunnic_overlord\s*\}", yoke)
    assert "can_join_trigger = {\n\t\talways = no" in yoke and "can_leave_trigger = {\n\t\talways = no" in yoke
    assert "cannot_declare_no_cb_wars_on_members = yes" in yoke
    # tribute: payers are the non-leaders, the payee the leader, about 1% of the members' income
    tribute = code(TRIBUTE)
    assert "NOT = {\n\t\t\t\t\tis_leader_of_international_organization = root" in tribute
    assert "leader_country ?= {" in tribute and "multiply = 0.01" in tribute
    assert re.search(r"price = (\w+)", tribute).group(1) in top_keys(PRICE)


def test_every_war_has_its_goal_and_its_treaty():
    vanilla = set(top_keys(b.GAME / "in_game/common/wargoals/00_default.txt"))
    ours = set(top_keys(WARGOAL))
    cbs = code(CB)
    goals = dict(re.findall(r"^(cb_\w+) = \{.*?war_goal_type = (\w+)", cbs, re.M | re.S))
    assert set(goals) == set(top_keys(CB))
    assert all(g in ours | vanilla for g in goals.values()), goals
    assert ours <= set(goals.values())                                      # no orphan war goal
    treaties = code(TREATY)
    by_cb = set(re.findall(r"casus_belli \?= casus_belli:(\w+)", treaties))
    assert by_cb == set(goals) - {"cb_tfe_stand_against_the_scourge"}     # that one is a plain superiority war
    assert "add_country_to_international_organization = scope:loser" in treaties
    assert "tfe_hunnic_subsidy" not in treaties
    assert "reason = WonFreedom" in treaties
    # the Break the Yoke action and the Reckoning's rising declare the same war
    for p in (ACTIONS, EVENT):
        assert "type = casus_belli:cb_tfe_break_the_yoke" in code(p), p.name


def test_the_phases_open_on_named_causes():
    s = code(SITUATION)
    assert "set_variable = { name = tfe_storm_phase value = 1 }" in s
    assert re.search(r"tfe_yoke_size >= 8\s*international_organization:tfe_hunnic_yoke \?= \{\s*any_international_organization_member = \{ OR = \{ tag = WRE tag = EAR \} \}", s)
    assert re.search(r"current_date >= 434\.1\.1\s*tfe_yoke_size >= 6", s)
    assert "var:tfe_scourge = { is_alive = no }" in s and "has_variable = tfe_reckoning_due" in s
    assert "set_variable = { name = tfe_reckoning_clock value = yes years = 10 }" in s
    for n in (1, 2, 3, 4, 5):
        assert f"tfe_hunnic_storm.{n}" in s and f"tfe_hunnic_storm.{n} = {{" in code(EVENT), n
    assert "modifier = tfe_huns_endure" in s and "destroy_international_organization" in s
    # can_end alone is checked too rarely: the monthly tick ends it by the same trigger
    assert "current_date >= 480.1.1" in code(END) and "has_variable = tfe_storm_resolved" in code(END)
    assert re.search(r"can_end = \{\s*tfe_hunnic_storm_is_over = yes", s)
    assert re.search(r"limit = \{ tfe_hunnic_storm_is_over = yes \}\s*end_situation = situation:tfe_hunnic_storm", s)
    on = code(ON_ACTION)
    assert "activate_situation = situation:tfe_hunnic_storm" in on
    assert re.search(r"on_ruler_death = \{\s*on_actions = \{ tfe_on_ruler_death_reckoning_due \}", on)
    # the subsidy's Unity driver in the Imperium Romanum
    rome = code(COMMON / "international_organizations/tfe_roman_empire.txt")
    assert "is_member_of_international_organization = international_organization:tfe_hunnic_yoke" in rome and 'desc = "TFE_UNITY_HUNNIC_SUBSIDY"' in rome


def test_the_scourge_is_a_title_not_a_roll():
    trait = code(TRAIT)
    assert top_keys(TRAIT) == ["tfe_scourge_of_god"] and "always = no" in trait and "category = ruler" in trait
    assert "add_trait = trait:tfe_scourge_of_god" in code(ACTIONS)


def test_migration_is_one_effect_shared_by_action_and_event():
    assert top_keys(MIGRATION) == ["tfe_start_migration_effect"]
    assert "tfe_start_migration_effect = yes" in code(COMMON / "generic_actions/tfe_migratory.txt")
    assert "tfe_start_migration_effect = yes" in code(EVENT)
    assert "abandon_location" in code(MIGRATION)


def test_panel_and_art_exist():
    assert PANEL.read_text(encoding="utf-8-sig").startswith("situation_panel = {")
    assert "GetVariable('tfe_storm_phase')" in PANEL.read_text(encoding="utf-8-sig")
    for d in ("illustrations/situation", "icons/situations"):
        art = b.MOD / f"main_menu/gfx/interface/{d}/tfe_hunnic_storm.dds"
        assert art.read_bytes()[:4] == b"DDS ", art



def test_the_grand_raid_is_a_paid_button_not_a_free_cb():
    raid, cb = code(RAID), code(CB)
    assert "type = casus_belli:cb_tfe_grand_raid" in raid and "source_flags = neighbor" in raid
    assert "price = price:tfe_hunnic_raid_prestige" in raid and "value = 10" in raid
    assert re.search(r"tfe_hunnic_raid_prestige = \{\s*prestige = 1", code(PRICE))
    grand = cb[cb.index("cb_tfe_grand_raid"):]
    assert re.search(r"create_visible = \{\s*always = no", grand.split("cb_tfe_break_the_yoke")[0])
