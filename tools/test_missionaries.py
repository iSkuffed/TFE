"""The Christianisation of Europe (RoadMap #30): Nicene and Arian movements, missionaries who walk to a pagan place and
preach there, two decisions and a conversion event. Static checks on what script/missionaries.py writes."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
sys.path.insert(0, str(ROOT / "tools"))
import missionaries as m  # noqa: E402
import borders as b  # noqa: E402

OUT = m.outputs()
MOV = OUT["in_game/common/movements/tfe_christianisation.txt"]
TRIG = OUT["in_game/common/scripted_triggers/tfe_christianisation.txt"]
LOC = OUT["main_menu/localization/english/tfe_christianisation_l_english.yml"]
TYPES = OUT["main_menu/common/modifier_type_definitions/tfe_christianisation.txt"]


def religions():
    files = [*(b.GAME / "in_game/common/religions").glob("*.txt"), ROOT / "in_game/common/religions/tfe_religions.txt"]
    return {k for p in files for k in re.findall(r"^(?:REPLACE:)?(\w+)\s*=\s*\{", p.read_text(encoding="utf-8-sig"), re.M)}


def locations():
    text = (ROOT / "in_game/map_data/location_templates.txt").read_text(encoding="utf-8-sig")
    return set(re.findall(r"^(\w+)\s*=", text, re.M))


def test_every_faith_named_exists():
    known = religions()
    for faith, converts in m.CONVERTS.items():
        assert faith in known, faith
        assert not set(converts) - known, set(converts) - known


def test_each_movement_converts_its_list_and_the_rival_only_as_a_minority():
    for faith, key in m.MOVEMENT.items():
        names = [n.key for n in m.MOVEMENTS.find(None, None, inside=(key, "required_religions"))]
        assert names == list(m.CONVERTS[faith]), key
    assert m.ARIAN in m.CONVERTS[m.NICENE] and m.NICENE in m.CONVERTS[m.ARIAN]
    assert "celtic_paganism" not in m.CONVERTS[m.ARIAN]  # Gaul's Celts are left to the Nicenes


def test_every_pop_type_has_a_multiplier():
    """a movement skips pop types it does not list (movements/readme.txt)"""
    for key in m.MOVEMENT.values():
        listed = {n.val for n in m.MOVEMENTS.find("pop_type", None, inside=(key, "specific_pop_type_effect"))}
        assert listed == set(m.POP_TYPES), key


def test_arians_never_convert_nicenes_under_a_nicene_king():
    r0 = MOV.split("tfe_arian_movement", 1)[1].split("calc_interval_days", 1)[0]
    assert "multiply = 0" in r0 and "religion:orthodox" in r0 and "religion:arianism" in r0


def test_the_cult_centres_exist_and_resist():
    known = locations()
    for loc in m.CULT_CENTRES + m.SEES:
        assert loc in known, loc
    assert all(f"location:{c}" in MOV for c in m.CULT_CENTRES)


def test_growth_modifiers_have_a_type_and_a_name():
    for key in m.MOVEMENT.values():
        for scope in ("local", "national"):
            mod = f"{scope}_{key}_growth_modifier"
            assert f"{mod} = {{" in TYPES, mod
            assert f"MODIFIER_TYPE_NAME_{mod}:" in LOC, mod


def test_the_pagan_trigger_lists_every_pagan():
    for faith in m.PAGANS:
        assert f"religion:{faith}" in TRIG, faith


def pulse():
    return OUT["in_game/common/on_action/tfe_christianisation.txt"]


def test_every_see_is_seeded_with_its_own_believers():
    start = m.PULSES.find("spawn_movement", None, inside=("tfe_on_start_christianisation", "effect"))
    text = pulse().split("tfe_on_start_christianisation = {", 1)[1]
    for loc in m.SEES:
        assert f"location:{loc}" in text, loc
    assert "religion_percentage(religion:orthodox)" in text and len(start) == len(m.SEES) + len(m.ARIAN_SEEDS)


def test_the_arian_peoples_are_seeded_in_their_capitals():
    text = pulse().split("tfe_on_start_christianisation = {", 1)[1]
    for tag in m.ARIAN_SEEDS:
        assert f"c:{tag} ?= {{" in text, tag


def expedition():
    return OUT["in_game/common/expedition_types/tfe_missionaries.txt"]


def effects():
    return OUT["in_game/common/scripted_effects/tfe_christianisation.txt"]


def test_the_missionary_walks_overland_one_at_a_time():
    for field in ("travel_mode = land", "dynamic_first_waypoint = yes", "origin = none", "unique = yes", "ai = no"):
        assert field in expedition(), field


def test_he_preaches_on_arrival_and_even_when_the_road_fails():
    for block in ("on_end", "on_fail"):
        assert m.EXPEDITION.find("tfe_preach_effect", None, inside=(m.EXPEDITION_TYPE, block)), block
        guard = m.EXPEDITION.find("has_variable", "tfe_mission_to", inside=(m.EXPEDITION_TYPE, block, "limit"))
        assert guard, block  # the Expedition Lost popup's dry run of on_fail finds no destination


def test_the_spreader_follows_the_missionarys_own_faith():
    preach = effects().split("tfe_preach_effect = {", 1)[1].split("tfe_end_mission_effect = {", 1)[0]
    for faith in m.MOVEMENT:
        assert f"religion:{faith}" in preach
    assert "add_spreader" in preach and "scope:tfe_missionary" in preach


def test_a_dead_missionary_stops_preaching_at_once():
    assert m.PULSES.find("on_actions", None, inside="on_character_death")
    dies = pulse().split("tfe_on_missionary_dies = {", 1)[1]
    assert "tfe_end_mission_effect = yes" in dies


def test_a_mission_ends_by_removing_the_spreader_and_the_modifier():
    end = effects().split("tfe_end_mission_effect = {", 1)[1]
    assert "remove_spreader = scope:tfe_missionary" in end
    assert "remove_location_modifier = tfe_mission_preaching" in end


def test_a_missionary_walks_on_at_most_three_times():
    assert m.PULSES.find("var:tfe_missions", None, inside="tfe_on_missions_end")
    assert f"var:tfe_missions < {m.MAX_MISSIONS}" in pulse()


def test_preaching_speeds_both_movements_where_he_stands():
    for key in m.MOVEMENT.values():
        assert m.MODIFIERS.find(f"local_{key}_growth_modifier", None, inside=m.PREACHING), key


def test_a_retired_missionary_is_killed_from_the_country():
    """kill_character_silently = yes in character scope fails PostValidate (Task 2 probe)"""
    assert "kill_character_silently = yes" not in pulse()
    assert "kill_character_silently = scope:tfe_missionary" in pulse()


def test_the_mani_is_named_as_a_province_definition():
    assert "province_definition = province_definition:laconia_province" in MOV


PULSE = pulse()


def areas_and_regions():
    t = (b.GAME / "in_game/map_data/definitions.txt").read_text(encoding="utf-8-sig")
    return set(re.findall(r"(\w+_(?:area|region))\s*=\s*\{", t))


def test_every_saint_starts_and_ends_somewhere_real():
    locs, ar = locations(), areas_and_regions()
    for s in m.SAINTS:
        assert s.start in locs, s.key
        for target in s.targets:
            assert target in (ar if target.endswith(("_area", "_region")) else locs), (s.key, target)
        assert s.faith in m.MOVEMENT


def test_every_saint_has_a_name():
    for s in m.SAINTS:
        assert f"name_{s.key}" in LOC or s.key in m.VANILLA_NAMES, s.key


def test_each_saint_goes_once_within_his_window():
    for s in m.SAINTS:
        assert f"tfe_saint_{s.key}" in PULSE
        assert f"{s.year + s.wait}.1.1" in PULSE


def test_martin_goes_in_the_first_year():
    assert m.SAINTS[0].key == "martin" and m.SAINTS[0].year == 395


def test_random_missionaries_are_rarer_without_the_edict():
    rnd = PULSE.split("tfe_on_random_missionary", 1)[1]
    assert f"chance = {m.RANDOM_CHANCE}" in rnd and f"chance = {m.RANDOM_CHANCE + m.TEMPLES_BONUS}" in rnd


def test_one_saint_per_court_per_year():
    """a saved scope:tfe_mission_to outlives its saint's block: the next saint must see the road is taken"""
    guards = m.PULSES.find("has_variable", "tfe_mission_to", inside=("tfe_on_saints", "effect", "if", "limit", "NOT"))
    assert len(guards) == len(m.SAINTS)


def test_the_temples_closed_speed_the_nicenes():
    assert m.MODIFIERS.find("national_tfe_nicene_movement_growth_modifier", None, inside=m.TEMPLES)
    assert f"STATIC_MODIFIER_NAME_{m.TEMPLES}:" in LOC


def decisions():
    return OUT["in_game/common/decisions/tfe_christianisation.txt"]


def test_a_mission_costs_months_of_income_with_a_floor():
    vals = OUT["in_game/common/script_values/tfe_christianisation.txt"]
    assert f"multiply = {m.MISSION_INCOME_MONTHS}" in vals and f"min = {m.MISSION_MIN_GOLD}" in vals


def test_sponsor_a_mission_has_a_cooldown_and_waits_for_the_last_missionary():
    allow = decisions().split("tfe_sponsor_mission", 1)[1].split("ai_will_do", 1)[0]
    assert "tfe_mission_sponsored" in allow and "tfe_mission_to" in allow
    assert f"years = {m.MISSION_COOLDOWN}" in decisions()


def test_close_the_temples_is_for_a_nicene_rome():
    pot = decisions().split("tfe_close_the_temples", 1)[1].split("allow", 1)[0]
    assert "tfe_is_roman_empire = yes" in pot and "religion:orthodox" in pot


def test_close_the_temples_angers_the_pagans_and_can_raise_them():
    eff = decisions().split("tfe_close_the_temples", 1)[1]
    assert "add_pop_satisfaction" in eff and f"chance = {m.RISING_CHANCE}" in eff


def conversion():
    return OUT["in_game/events/tfe_conversion.txt"]


def test_a_pagan_king_is_asked_once_a_decade_when_his_people_have_turned():
    king = pulse().split("tfe_on_pagan_king = {", 1)[1]
    assert "tfe_christian_share > 0.5" in king and "tfe_conversion_asked" in king
    assert f"years = {m.CONVERSION_EVERY}" in king


def test_taking_the_faith_changes_the_king_too():
    a = conversion().split("option", 1)[1].split("option", 1)[0]
    assert "change_religion = scope:tfe_new_faith" in a and "change_religion_for_ruler_and_family" in a


def test_holding_out_speeds_the_drift():
    assert "tfe_old_gods_kept" in conversion()
    for key in m.MOVEMENT.values():
        assert m.MODIFIERS.find(f"national_{key}_growth_modifier", None, inside="tfe_old_gods_kept"), key


def test_no_saint_is_too_old_to_reach_his_field():
    """a man of 79 died at home within the year (probe): a saint who never preaches is a wasted saint"""
    ages = [int(n.val) for n in m.PULSES.find("age", None, inside=("tfe_on_saints",))]
    assert len(ages) == len(m.SAINTS) and max(ages) <= m.SAINT_MAX_AGE
