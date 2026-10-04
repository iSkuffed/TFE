"""Rome's answers on the Decline of the West's panel: Hospitalitas and Man the Limes. Static checks: the scripts load."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

COMMON = b.MOD / "in_game/common"
ACTIONS = COMMON / "generic_actions/tfe_decline_rome.txt"
PRICE = COMMON / "prices/tfe_decline_rome.txt"
TRIGGERS = COMMON / "scripted_triggers/tfe_decline_rome.txt"
MODIFIER = b.MOD / "main_menu/common/static_modifiers/tfe_decline_rome.txt"
EVENT = b.MOD / "in_game/events/tfe_decline_rome.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_decline_rome_l_english.yml"
FRONTIER = COMMON / "building_types/tfe_frontier.txt"
SCRIPTS = (ACTIONS, PRICE, TRIGGERS, MODIFIER, EVENT)


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def top_keys(p):
    return re.findall(r"^(\w+)\s*=\s*\{", code(p), re.M)


def test_files_are_balanced_and_bom_prefixed():
    for p in SCRIPTS + (LOC,):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in SCRIPTS:
        assert code(p).count("{") == code(p).count("}"), p.name


def test_everything_shown_is_localized():
    text = LOC.read_text(encoding="utf-8-sig")
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", text, re.M))
    wanted = {k for a in top_keys(ACTIONS) for k in (a, f"{a}_desc", f"{a}_tt")} | set(top_keys(PRICE))
    wanted |= {f"STATIC_MODIFIER_{n}_{m}" for m in top_keys(MODIFIER) for n in ("NAME", "DESC")}
    wanted |= set(re.findall(r'(?:title|desc) = (tfe_decline_rome\.\d\.\w+)', code(EVENT)))
    wanted |= set(re.findall(r'name = (tfe_decline_rome\.\d\.\w+)', code(EVENT)))
    wanted |= set(re.findall(r'text = (tfe_\w+_tt)', code(TRIGGERS)))
    wanted |= set(re.findall(r'(?:name|none_available_msg_key) = "(tfe_\w+)"', code(ACTIONS)))
    wanted |= set(re.findall(r'desc = "(tfe_\w+)"', code(ACTIONS)))
    assert wanted <= keys, sorted(wanted - keys)


def test_both_answers_hang_on_the_situation_panel():
    acts = code(ACTIONS)
    assert top_keys(ACTIONS) == ["tfe_hospitalitas", "tfe_man_the_limes"]
    assert acts.count("type = situation") == 2
    assert acts.count("situation:tfe_decline_of_the_west = { situation_is_active = yes }") == 2
    assert acts.count("looking_for_a = situation") == 2


def test_hospitalitas_lets_the_host_refuse_and_makes_a_foedus():
    acts, ev = code(ACTIONS), code(EVENT)
    assert "tfe_migrating" in acts and "NOT = { has_variable = tfe_settled }" in acts
    assert "trigger_event_non_silently = { id = tfe_decline_rome.1 }" in acts
    assert re.search(r"cooldown = \{\s*type = tfe_hospitalitas\s*years = 5", acts)
    # the accepting option hands the land over and swears the foedus; the refusing one tells the actor
    accept = re.search(r"tfe_decline_rome\.1\.a\s*(.*?)\n\t\}\n", ev, re.S).group(1)
    assert "change_location_owner" in accept and "subject_type:tfe_foederati" in accept
    # peace and the oath before the land: the first location won disbands the host (on_action/tfe_migratory.txt)
    assert accept.index("leave_all_wars_with") < accept.index("change_location_owner")
    assert accept.index("make_subject_of") < accept.index("change_location_owner")
    assert "tfe_decline_rome.2" in ev.split("name = tfe_decline_rome.1.b")[1]
    assert ev.count("outcome = neutral") == 2
    # a saved scope does not reach a child event: the offer travels as variables and is re-derived
    assert "var:tfe_hospitalitas_from" in ev and "var:tfe_hospitalitas_refused_by" in ev
    # user: accepting names the lands; refusing mid-war says the war goes on
    # user: a whole area, not one province; nobody gives up a migration for a single province
    assert "looking_for_a = area" in acts and "looking_for_a = province" not in acts
    assert "name = tfe_hospitalitas_area value = scope:target_area" in acts
    assert "var:tfe_hospitalitas_area ?= { save_scope_as = tfe_land }" in ev
    assert "[tfe_land.GetName]" in LOC.read_text(encoding="utf-8-sig")
    refuse = ev.split("name = tfe_decline_rome.1.b")[1]
    assert re.search(r"limit = \{\s*exists = scope:tfe_rome\s*is_at_war_with = scope:tfe_rome\s*\}\s*custom_tooltip = tfe_decline_rome\.1\.b\.war_tt", refuse)


def test_hospitalitas_keeps_to_its_own_war_and_the_east_to_the_balkans():
    acts, ev = code(ACTIONS), code(EVENT)
    hosp = acts[:acts.index("tfe_man_the_limes = {")]
    # user: the Franks march on the West, and the East bought them off; a host at war with the other Rome is not ours
    assert re.search(r"NOT = \{\s*this = scope:actor\s*\}\s*is_at_war_with = prev", hosp)
    # user: the East gave Syria away; it offers only Balkan land
    assert re.search(r"scope:actor = \{ NOT = \{ tag = EAR \} \}\s*region = region:balkan_region", hosp)
    # user: the hosts took every offer; refusal outweighs a bare offer, and a weak Rome is refused the more
    accept = ev.split("name = tfe_decline_rome.1.a")[1].split("name = tfe_decline_rome.1.b")[0]
    refuse = ev.split("name = tfe_decline_rome.1.b")[1]
    assert re.search(r"ai_chance = \{\s*base = 1\b", accept) and re.search(r"ai_chance = \{\s*base = 3\b", refuse)
    assert re.search(r"factor = 0\.5\s*scope:tfe_rome = \{\s*is_in_losing_war = yes\s*\}", accept)
    assert re.search(r"factor = 0\.5\s*military_strength > scope:tfe_rome\.military_strength", accept)
    assert "num_regiments" not in accept
    # the land its people truly took sways both sides
    assert re.search(r"tfe_is_historical_land_of = \{\s*WHO = root\s*\}", accept)
    assert re.search(r"tfe_is_historical_land_of = \{\s*WHO = scope:host\s*\}", hosp)


def test_man_the_limes_costs_and_marks_the_frontier():
    acts, price, mod = code(ACTIONS), code(PRICE), code(MODIFIER)
    assert "gold" in price and "manpower" in price
    # `name =` (as effects.log says) is silently dropped: the modifier key is `modifier =`
    assert "add_location_modifier = { modifier = tfe_limes_manned years = 1 " in acts
    # a whole diocese at a time, every fort we hold in it
    limes = acts[acts.index("tfe_man_the_limes = {"):]
    assert "looking_for_a = region" in limes and "looking_for_a = location" not in limes
    assert "scope:limes_region = {\n\t\t\t\tevery_location_in_region = {" in limes
    assert "game_data = { category = location }" in mod
    types = set(top_keys(FRONTIER))
    for t in re.findall(r"building_type:(\w+)", code(TRIGGERS)):
        assert t in types, t


def test_the_limes_bars_the_peoples_beyond_it():
    trig = code(TRIGGERS)
    assert re.search(r"tfe_frontier_unmanned = \{\s*custom_tooltip", trig) and "NOT = {" in trig
    assert "any_owned_location" in trig and "any_neighbor_location" in trig and "has_location_modifier = tfe_limes_manned" in trig


def test_actions_script_parses_equal_to_the_committed_file(tmp_path):
    # script/decline_rome_actions.py writes ACTIONS: same tree as the file, and pyright clean
    sys.path.insert(0, str(b.MOD / "script"))
    import decline_rome_actions
    import lint_script as ls
    from test_pdx_events import pyright, tree
    doc = decline_rome_actions.build()
    assert tree(ls.parse(doc.text())) == tree(ls.parse(ACTIONS.read_text(encoding="utf-8-sig")))
    assert [n.val for n in doc.find("target_flag")] == ["recipient", "host", "target_area", "recipient", "limes_region"]
    assert pyright(tmp_path, b.MOD / "script/decline_rome_actions.py") == []
