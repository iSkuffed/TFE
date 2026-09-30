"""Migratory peoples: a people beyond the rivers gives up its homeland for a large host that costs nothing while landless."""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

COMMON = b.MOD / "in_game/common"
ACTIONS = COMMON / "generic_actions/tfe_migratory.txt"
EFFECT = COMMON / "scripted_effects/tfe_migratory.txt"   # Start Migration's effect, shared with the Hunnic Storm's events
AUTO = COMMON / "auto_modifiers/tfe_migratory.txt"
AI_LIST = COMMON / "generic_action_ai_lists/tfe_migratory_list.txt"
CB = COMMON / "casus_belli/tfe_migration.txt"
WARGOAL = COMMON / "wargoals/tfe_migration.txt"
SETTLE = COMMON / "on_action/tfe_migratory.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_migratory_l_english.yml"
ARMIES = b.MOD / "main_menu/setup/start/27_armies.txt"
SCRIPTS = (ACTIONS, EFFECT, AUTO, AI_LIST, CB, WARGOAL, SETTLE)
NEW_ACTIONS = ("tfe_migrate_east", "tfe_migrate_west")


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def top_keys(p):
    return re.findall(r"^(\w+)\s*=\s*\{", code(p), re.M)


def test_scripts_are_bom_prefixed_and_balanced():
    for p in SCRIPTS + (LOC,):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in SCRIPTS + (ARMIES,):
        assert code(p).count("{") == code(p).count("}"), p.name


def test_start_migration_is_a_one_way_trip_for_the_peoples_beyond_the_rivers():
    acts = code(ACTIONS)
    assert top_keys(ACTIONS) == list(NEW_ACTIONS)
    listed = re.search(r"actions = \{([^}]*)\}", code(AI_LIST)).group(1).split()
    assert listed == list(NEW_ACTIONS) and "tfe_is_migrator = yes" in code(AI_LIST)
    potential = re.search(r"potential = \{(.*?)\n\t\}", acts, re.S).group(1)
    assert "tfe_is_migrator = yes" in potential and "country_type" not in potential   # not only the Vandals now
    assert "NOT = { has_variable = tfe_migrating }" in potential   # once only: the host never comes back
    allow = re.search(r"allow = \{(.*?)\n\t\}", acts, re.S).group(1)
    assert all(s in allow for s in ("is_subject = no", "tfe_frontier_unmanned = yes"))
    assert "any_army" not in allow   # most peoples start with no warband afield; the host gathers at the capital
    assert "tfe_start_migration_effect = yes" in acts
    effect = code(EFFECT)
    assert "set_variable = tfe_migrating" in effect and "every_owned_location" in effect and "abandon_location" in effect
    # a landed people must become army-based before it abandons its last location, or it is gone
    assert effect.index("change_country_type = army") < effect.index("change_location_owner")
    # the homeland passes to a neighbouring people, never to Rome or another host; empty only with no neighbour
    heir = re.search(r"random_neighbor_country = \{(.*?)\n\t\}", effect, re.S).group(1)
    assert all(s in heir for s in ("NOT = { tag = WRE }", "NOT = { tag = EAR }", "NOT = { has_variable = tfe_migrating }"))
    assert effect.index("change_location_owner = scope:tfe_heir_to_the_land") < effect.index("abandon_location")


def test_one_button_per_empire_declares_war_on_it_after_the_first_month():
    # user: two buttons, not clickable until a month after the game start, each starts a migration war at once
    start = re.search(r'START_DATE = "395\.1\.(\d+)"', (b.MOD / "loading_screen/common/defines/tfe_defines.txt").read_text(encoding="utf-8-sig"))
    acts = code(ACTIONS).split("tfe_migrate_west = {")
    for act, tag in zip(acts, ("EAR", "WRE")):
        assert f"country_exists = c:{tag}" in act
        assert f"current_date >= 395.2.{start.group(1)}" in act and "text = tfe_migration_not_yet_tt" in act
        assert f"declare_war_with_cb = {{ target = c:{tag} type = casus_belli:cb_tfe_migration }}" in act
        assert act.index("tfe_start_migration_effect = yes") < act.index("declare_war_with_cb")   # the CB first


def test_the_ai_takes_the_road_one_people_at_a_time():
    # pace the chaos: ~19 peoples may migrate; the AI waits 4 years after any host sets out, then needs a push
    assert "set_global_variable = { name = tfe_host_took_the_road value = yes years = 4 }" in code(EFFECT)
    ai = re.search(r"ai_will_do = \{(.*?)\n\t\}", code(ACTIONS), re.S).group(1)
    assert re.search(r"value = 0\s*if = \{\s*limit = \{\s*NOT = \{ has_global_variable = tfe_host_took_the_road \}", ai)
    assert "tfe_is_under_the_yoke = yes" in ai and "var:tfe_unity < 50" in ai


def test_the_host_disbands_back_to_its_old_warband_once_it_takes_land():
    # user: force disband the special troops after the migration; otherwise one location has to pay 16,000 men
    on = code(SETTLE)
    assert re.search(r"on_location_changed_owner = \{\s*on_actions = \{\s*tfe_on_host_settles\b", on)
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
    grants = re.findall(r"add_casus_belli = \{[^}]*target = c:(\w+)[^}]*type = casus_belli:cb_tfe_migration", code(EFFECT))
    assert sorted(grants) == ["EAR", "WRE"], grants
    goal = re.search(r"war_goal_type = (\w+)", cb).group(1)
    assert top_keys(WARGOAL) == [goal] and "type = superiority" in code(WARGOAL)
    attacker = re.search(r"attacker = \{(.*?)\n\t\}", code(WARGOAL), re.S).group(1)
    assert float(re.search(r"conquer_cost = ([\d.]+)", attacker).group(1)) < 1   # land is the whole point


def test_warband_units_exist_in_vanilla():
    vanilla = set()
    for p in (b.GAME / "in_game/common/unit_types").glob("*.txt"):
        vanilla |= set(re.findall(r"^(\w+) = \{", p.read_text(encoding="utf-8-sig"), re.M))
    used = set(re.findall(r"type = (a_\w+)", code(EFFECT))) | set(re.findall(r"\b(a_\w+) = \{", code(ARMIES)))
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


def test_start_migration_is_a_button_on_the_decline_of_the_west():
    # user: the Migrate interaction moves from the Form New Country panel into the Decline of the West situation
    acts = code(ACTIONS)
    assert "type = situation" in acts and "type = owncountry" not in acts
    assert "situation:tfe_decline_of_the_west = { situation_is_active = yes }" in acts
    assert re.search(r"looking_for_a = situation\s*interaction_source_list = \{\s*situation:tfe_decline_of_the_west", acts)
    # the override held only our button, so it is gone and vanilla's panel is used as is
    assert not (b.MOD / "in_game/gui/form_new_country.gui").exists()


def test_roman_towns_taken_by_a_host_send_it_men():
    # on_action/tfe_defectors.txt: the host regains strength, Rome loses manpower, the town is marked for a decade
    defect = COMMON / "on_action/tfe_defectors.txt"
    values = COMMON / "script_values/tfe_defectors.txt"
    modifier = b.MOD / "main_menu/common/static_modifiers/tfe_defectors.txt"
    loc = b.MOD / "main_menu/localization/english/tfe_defectors_l_english.yml"
    for p in (defect, values, modifier, loc):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
        assert code(p).count("{") == code(p).count("}"), p.name
    on_action = code(defect)
    for hook in ("on_siege_won", "on_location_occupied"):   # forts and open towns
        assert re.search(rf"^{hook} = \{{\s*on_actions = \{{ tfe_on_host_takes_roman_town \}}", on_action, re.M), hook
    assert "has_variable = tfe_migrating" in on_action and "NOT = { has_variable = tfe_settled }" in on_action
    assert "NOT = { has_location_modifier = tfe_fled_to_the_host }" in on_action   # once per town per decade
    assert "modifier = tfe_fled_to_the_host years = 10" in on_action
    assert set(top_keys(modifier)) == {"tfe_fled_to_the_host"}
    text = loc.read_text(encoding="utf-8-sig")
    assert all(f"STATIC_MODIFIER_{k}_tfe_fled_to_the_host:" in text for k in ("NAME", "DESC"))
    # each of the West's burdens drives more men to the host
    burdens = set(top_keys(COMMON / "government_reforms/tfe_late_roman_west.txt"))
    assert set(re.findall(r"has_reform = government_reform:(\w+)", code(values))) == burdens


def test_barbaricum_lets_the_peoples_beyond_the_rivers_pass():
    # user: fuzzy borders in Germania, as the HRE; a landless host must never be exiled (it cannot siege when it is)
    io = COMMON / "international_organizations/tfe_barbaricum.txt"
    assert io.read_bytes().startswith(b"\xef\xbb\xbf") and code(io).count("{") == code(io).count("}")
    body = code(io)
    assert top_keys(io) == ["tfe_barbaricum"] and "has_leader_country = no" in body
    access = re.search(r"has_military_access = \{(.*?)\n\t\}", body, re.S).group(1)
    assert "is_member_of_international_organization = root" in access   # members pass through members
    assert "has_variable = tfe_migrating" in access and "NOT = { has_variable = tfe_settled }" in access   # a host anywhere
    for s in ("can_join_trigger = { always = no }", "can_leave_trigger = { always = no }", "gives_food_access_to_members = yes"):
        assert s in body, s
    assert "expel_members_who_are_attackers_at_war_with_other_members = no" in body   # the tribes fight each other
    setup = code(b.MOD / "main_menu/setup/start/15_international_organizations.txt")
    members = re.search(r"type = tfe_barbaricum.*?members = \{([^}]*)\}", setup, re.S).group(1).split()
    trigger = re.search(r"tfe_is_migrator = \{(.*?)\n\}", code(COMMON / "scripted_triggers/tfe_decline_of_the_west.txt"), re.S).group(1)
    assert sorted(members) == sorted(re.findall(r"tag = (\w+)", trigger))
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    assert {"tfe_barbaricum", "tfe_barbaricum_desc"} <= keys


def test_a_fifth_of_the_people_follow_the_host_and_settle_its_first_lands():
    # user: taking land shifts its people towards the host's culture and faith, by how many already live there
    effect = code(EFFECT)
    assert "limit = { culture = scope:tfe_host.culture }" in effect
    taken = re.search(r"add = \{ value = scope:tfe_leaver\.pop_size multiply = ([\d.]+) \}", effect).group(1)
    left = re.search(r"add_pop_size = \{ value = pop_size multiply = -([\d.]+) \}", effect).group(1)
    assert taken == left   # the people are moved, not copied
    assert effect.index("tfe_host_people") < effect.index("change_location_owner")   # counted before the land goes
    assert "set_variable = { name = tfe_host_plantings value = 0 }" in effect   # change_variable fails on an unset one
    on = code(SETTLE)
    assert re.search(r"on_actions = \{ tfe_on_host_settles tfe_on_host_plants_its_people \}", on)
    plant = on[on.index("tfe_on_host_plants_its_people = {"):]
    assert "culture = scope:winner.culture" in plant and "religion = scope:winner.religion" in plant
    share = float(re.search(r"multiply = ([\d.]+)", plant).group(1))
    rounds = int(re.search(r"var:tfe_host_plantings >= (\d+)", plant).group(1))
    assert share * rounds == 1   # every settler is planted, and no more
