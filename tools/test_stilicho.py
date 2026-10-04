"""Stilicho's Glory (RoadMap #27): the bar, its causes, the showdown, the rising and the win (script/defs_stilicho.py,
script/stilicho_events.py, script/defs_usurpers.py)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))


def flat(rel):
    """a script file without comments, whitespace collapsed: `a = {\n\tb = c\n}` reads `a = { b = c }`."""
    return " ".join(re.sub(r"#[^\n]*", "", (ROOT / rel).read_text(encoding="utf-8-sig")).split())


def block(text, head):
    """the `{ ... }` body that follows `head` in flattened text (brace-matched)."""
    i = text.index(head) + len(head)
    i = text.index("{", i)
    depth = 0
    for j in range(i, len(text)):
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        if depth == 0:
            return text[i + 1:j]
    raise ValueError(head)


DEFS = "in_game/common/scripted_effects/tfe_stilicho.txt"
TRIG = "in_game/common/scripted_triggers/tfe_stilicho.txt"
MODS = "in_game/common/auto_modifiers/tfe_stilicho.txt"
ONA = "in_game/common/on_action/tfe_stilicho.txt"
EVENTS = "in_game/events/tfe_stilicho.txt"
YML = "main_menu/localization/english/tfe_stilicho_l_english.yml"
GLORY = "situation:tfe_decline_of_the_west"


def yml_keys():
    return set(re.findall(r"^ ([\w.]+):", (ROOT / YML).read_text(encoding="utf-8-sig"), re.M))


# --- the bar ---------------------------------------------------------------------------------------------------------

def test_glory_starts_at_50_with_the_decline():
    s = flat("in_game/common/situations/tfe_decline_of_the_west.txt")
    assert "set_variable = { name = tfe_stilicho_glory value = 50 }" in block(s, "on_start =")


def test_glory_is_clamped_and_only_moves_for_stilichos_country():
    fx = block(flat(DEFS), "tfe_add_stilicho_glory =")
    assert "tfe_stilicho_serves_us = yes" in fx
    assert "change_variable = { name = tfe_stilicho_glory add = $amount$ }" in fx
    assert "clamp_variable = { name = tfe_stilicho_glory min = 0 max = 100 }" in fx
    assert "trigger_event_non_silently = tfe_stilicho.1" in fx and "trigger_event_non_silently = tfe_stilicho.2" in fx
    # the warning is about Honorius: never after the showdown, when Stilicho may rule his own West
    warn = fx[fx.index("tfe_stilicho_warned"):fx.index("trigger_event_non_silently = tfe_stilicho.1")]
    assert "NOT = { has_global_variable = tfe_stilicho_showdown }" in warn


def test_stilicho_serves_the_country_that_employs_him():
    t = block(flat(TRIG), "tfe_stilicho_serves_us =")
    assert "character:tfe_stilicho ?= { is_alive = yes employer ?= prev }" in t


def test_tiers_cover_the_bar_and_set_morale():
    mods = flat(MODS)
    want = {"tfe_glory_discredited": (None, 25, "-0.1"), "tfe_glory_wanes": (25, 50, "-0.05"),
            "tfe_glory_rises": (75, 90, "0.1"), "tfe_glory_idol": (90, None, "0.2")}
    for name, (lo, hi, morale) in want.items():
        b = block(mods, f"{name} =")
        assert "tfe_stilicho_serves_us = yes" in b, name
        assert (lo is None) or f"var:tfe_stilicho_glory >= {lo}" in b, name
        assert (hi is None) or f"var:tfe_stilicho_glory < {hi}" in b, name
        assert f"land_morale_modifier = {morale}" in b, name
    reg = block(mods, "tfe_stilicho_regency =")
    assert "tfe_stilicho_serves_us = yes" in reg and "land_morale_modifier = 0.1" in reg


def test_the_regency_runs_to_408():
    assert "extend_regency = 8" in flat(ONA)
    opening = flat("in_game/common/on_action/tfe_opening.txt")
    assert "tfe_stilicho_regency" not in opening   # an auto-modifier now: it follows Stilicho
    assert "tfe_stilicho_regency" not in flat("main_menu/common/static_modifiers/tfe_opening.txt")


def test_every_modifier_is_named():
    keys = yml_keys()
    for name in re.findall(r"^(\w+) = \{", (ROOT / MODS).read_text(encoding="utf-8-sig"), re.M):
        assert {f"AUTO_MODIFIER_NAME_{name}", f"AUTO_MODIFIER_DESC_{name}"} <= keys, name


def test_the_panel_shows_glory_while_it_is_open():
    gui = (ROOT / "in_game/gui/panels/situation/tfe_decline_of_the_west.gui").read_text(encoding="utf-8-sig")
    assert "GetVariable('tfe_stilicho_glory').IsSet" in gui
    assert "progressbar" in gui and "TFE_DECLINE_GLORY" in gui
    loc = (ROOT / "main_menu/localization/english/tfe_decline_of_the_west_l_english.yml").read_text(encoding="utf-8-sig")
    for key in ("TFE_DECLINE_GLORY", "TFE_DECLINE_GLORY_VALUE", "TFE_DECLINE_GLORY_TT"):
        assert f" {key}:" in loc, key


# --- what moves it ---------------------------------------------------------------------------------------------------

def test_every_cause_is_hooked():
    ona = flat(ONA)
    for hook in ("on_battle_won", "on_battle_lost", "on_great_battle_won", "on_great_battle_lost",
                 "on_ending_war", "on_took_location_in_peace_treaty"):
        assert f"{hook} = {{ on_actions = {{" in ona, hook
    battle = block(ona, "tfe_on_stilicho_battle_won =")
    assert "leader ?= character:tfe_stilicho" in battle and "amount = 2" in battle
    assert "amount = -3" in block(ona, "tfe_on_stilicho_battle_lost =")
    # a great battle fires only its own hook, so its amount is the whole of it (the Glory tooltip's +5 / -6)
    assert "amount = 5" in block(ona, "tfe_on_stilicho_great_battle_won =")
    assert "amount = -6" in block(ona, "tfe_on_stilicho_great_battle_lost =")
    wars = block(ona, "tfe_on_stilicho_war_ended =")
    for amount in ("amount = 5", "amount = -8", "amount = 10", "amount = -10"):
        assert amount in wars, amount
    assert "tag = GILDO" in wars and "tag = HNS" in wars
    # a settled people keeps tfe_migrating: its later wars are ordinary wars
    assert "has_variable = tfe_migrating NOT = { has_variable = tfe_settled }" in wars


def test_ceded_core_land_costs_glory_but_our_own_transfers_do_not():
    ceded = block(flat(ONA), "tfe_on_stilicho_land_ceded =")
    assert "is_core_of = scope:loser" in ceded and "amount = -1" in ceded
    # a migration's loss is already its -8, but land a settled people takes costs Glory like anyone's
    assert "NOT = { AND = { has_variable = tfe_migrating NOT = { has_variable = tfe_settled } } }" in ceded
    assert "has_variable = tfe_usurper_against" in ceded   # Gildo's Africa is its -10


def test_hospitalitas_costs_glory():
    ev = flat("in_game/events/tfe_decline_rome.txt")
    assert "scope:tfe_rome = { tfe_add_stilicho_glory = { amount = -5 } }" in block(ev, "tfe_decline_rome.1 =")


# --- the showdown ----------------------------------------------------------------------------------------------------

def test_showdown_fires_three_ways_and_once():
    ona, fx = flat(ONA), flat(DEFS)
    assert "trigger_event_non_silently = { id = tfe_stilicho.2 days = 4961 }" in ona   # 22 Aug 408
    yearly = block(ona, "tfe_on_stilicho_yearly =")
    assert "var:tfe_stilicho_glory >= 90" in yearly and "random = { chance = 50" in yearly
    assert "trigger_event_non_silently = tfe_stilicho.2" in block(fx, "tfe_add_stilicho_glory =")   # at 100
    ev = block(flat(EVENTS), "tfe_stilicho.2 =")
    assert "has_global_variable = tfe_stilicho_showdown" in block(ev, "trigger =")
    assert "set_global_variable = tfe_stilicho_showdown" in block(ev, "immediate =")


def test_standing_with_stilicho_needs_70_and_the_ai_never_does():
    ev = flat(EVENTS)
    a = ev[ev.index("name = tfe_stilicho.2.a"):ev.index("name = tfe_stilicho.2.b")]
    assert "var:tfe_stilicho_glory >= 70" in a and "tfe_stilicho_rises = yes" in a
    assert "ai_chance = { base = 0 }" in a
    # with no land in Gaul (or Hispania at 90) no revolt could form, and the showdown would be spent for nothing
    assert "any_owned_location = { OR = { region = region:france_region" in a
    b = ev[ev.index("name = tfe_stilicho.2.b"):]
    assert "tfe_the_west_loses_stilicho = yes" in b and "add = 20" in b
    # the East's thanks are for putting him down: checked before the execution, so not paid if he already died
    assert b.index("is_alive = yes") < b.index("add = 20") < b.index("tfe_the_west_loses_stilicho = yes")


def test_losing_stilicho_brings_olympius_and_the_collapse():
    fx = block(flat(DEFS), "tfe_the_west_loses_stilicho =")
    for want in ("remove_variable = tfe_stilicho_glory", "set_regent = scope:tfe_olympius", "add_stability = -50",
                 "set_global_variable = tfe_stilicho_fell", "reason = execution"):
        assert want in fx, want
    assert "tfe_olympius_regency =" in flat(MODS)
    death = block(flat(ONA), "tfe_on_stilicho_dies =")
    assert "tfe_the_west_loses_stilicho = yes" in death and "tfe_stilicho_showdown" in death


def test_everything_the_events_show_is_localised():
    keys, ev = yml_keys(), flat(EVENTS)
    # `name =` only for option names: set_variable's and change_variable's `name =` is a variable, not text
    shown = {a or b for a, b in re.findall(r"(?:title|desc|custom_tooltip|text) = ([\w.]+)|name = (tfe_stilicho\.[\w.]+)", ev)}
    assert shown <= keys, sorted(shown - keys)


# --- the rising ------------------------------------------------------------------------------------------------------

def test_stilicho_rises_as_a_revolter_in_gaul():
    rise = block(flat(DEFS), "tfe_stilicho_rises =")
    assert "create_rebel = {" in rise and "start_revolt = yes" in rise and "declare_war" not in rise
    assert "trigger_event_silently = { id = tfe_stilicho.3 days = 1 }" in rise
    # the revolter is marked the moment it forms: it may come out landless, and a host in Gaul is at war with us too
    assert rise.index("set_variable = tfe_old_enemy") < rise.index("start_revolt") < rise.index(
        "set_variable = tfe_stilicho_revolter")
    assert "remove_variable = tfe_old_enemy" in rise
    land = block(flat(TRIG), "tfe_stilicho_base_land =")
    assert "region = region:france_region" in land and "region = region:iberia_region" in land


def test_the_crowning_moves_the_player_and_keeps_honorius_the_west():
    ev = block(flat(EVENTS), "tfe_stilicho.3 =")
    for want in ("define_unique_country_tag = STILI", "set_variable = tfe_western_rome",
                 "name = tfe_usurper_against value = root", "set_new_ruler = character:tfe_stilicho",
                 "set_as_designated_heir = character:tfe_eucherius", "leave_war = { war = scope:tfe_stilicho_war actor = root }",
                 "change_player = scope:tfe_stilicho_west", "set_new_ruler = character:tfe_honorius",
                 "tfe_constantine_rises = yes", "tfe_africa_breaks_away = yes", "add_core = scope:tfe_stilicho_west"):
        assert want in ev, want
    assert "is_ai = no" in ev
    assert "limit = { has_variable = tfe_stilicho_revolter }" in ev


def test_constantine_rises_once():
    op = flat("in_game/events/tfe_opening.txt")
    five = block(op, "tfe_opening.5 =")
    assert "tfe_constantine_rises = yes" in five and "NOT = { country_exists = c:CONST }" in block(five, "trigger =")
    us = flat("in_game/common/scripted_effects/tfe_usurpers.txt")
    assert "define_unique_country_tag = AFRIC" in us
    assert "define_unique_country_tag = CONST" in block(op, "tfe_opening.9 =")


def test_constantine_rises_as_an_annexable_revolter():
    # user: Britain just left, with no revolt and no war. It is a revolt, as Gildo's: only a revolt war offers Annex Revolter
    rise = block(flat("in_game/common/scripted_effects/tfe_usurpers.txt"), "tfe_constantine_rises =")
    assert "create_rebel = {" in rise and "start_revolt = yes" in rise and "declare_war" not in rise
    assert "region = region:great_britain_region" in rise and "trigger_event_silently = tfe_opening.9" in rise
    # the revolter is marked the moment it forms (it may come out landless), and the wars we were in are not his
    assert rise.index("set_variable = tfe_old_enemy") < rise.index("start_revolt") < rise.index(
        "set_variable = tfe_constantine_revolter")
    assert "remove_variable = tfe_old_enemy" in rise
    crown = block(flat("in_game/events/tfe_opening.txt"), "tfe_opening.9 =")
    for want in ("limit = { has_variable = tfe_constantine_revolter }", "change_location_owner = scope:tfe_usurper",
                 "leave_war = { war = scope:tfe_constantine_war actor = root }", "cancel_subject = prev",
                 "name = tfe_usurper_against value = root", "set_capital = location:london"):
        assert want in crown, want
    # recognising him ends the revolt war
    five = block(flat("in_game/events/tfe_opening.txt"), "tfe_opening.5 =")
    assert "white_peace = scope:tfe_constantine_war" in five


def test_a_usurper_that_takes_the_capital_wins_the_west():
    ona = flat(ONA)
    for hook in ("on_location_occupied", "on_siege_won"):
        assert f"{hook} = {{ on_actions = {{ tfe_on_constantine_takes_the_capital }} }}" in ona, hook
    take = block(ona, "tfe_on_constantine_takes_the_capital =")
    assert "tag = CONST" in take and "capital = scope:target" in take and "tfe_stilicho.5" in take
    ev = block(flat(EVENTS), "tfe_stilicho.5 =")
    assert "annex_country = { country = c:WRE reason = CivilWar }" in block(ev, "immediate =")
    assert "set_variable = tfe_western_rome" in block(ev, "immediate ="), "the annexer is a new tag: only the variable says it is the West"
    for opt in "abc":
        assert f"name = tfe_stilicho.5.{opt}" in ev


def test_stilicho_has_a_dynasty_and_so_do_his_children():
    chars = (ROOT / "main_menu/setup/395/05_characters.txt").read_text(encoding="utf-8-sig")
    for who in ("stilicho", "maria", "thermantia", "eucherius"):
        assert "dynasty = stilichonian_dynasty" in re.search(rf"\ttfe_{who} = \{{(.*?)\n\t\}}", chars, re.S).group(1), who


# --- the win ---------------------------------------------------------------------------------------------------------

def test_taking_honorius_capital_wins_the_west():
    ona = flat(ONA)
    for hook in ("on_location_occupied", "on_siege_won"):
        assert f"{hook} = {{ on_actions = {{ tfe_on_stilicho_takes_the_capital }} }}" in ona, hook
    take = block(ona, "tfe_on_stilicho_takes_the_capital =")
    assert "has_variable = tfe_western_rome" in take and "capital = scope:target" in take
    assert "is_at_war_with = c:WRE" in take and "tfe_stilicho.4" in take


def test_the_victor_takes_everything_and_decides_honorius_fate():
    ev = block(flat(EVENTS), "tfe_stilicho.4 =")
    imm = block(ev, "immediate =")
    for want in ("annex_country = { country = c:WRE reason = CivilWar }", "change_country_name = WRE",
                 "change_country_adjective = WRE_ADJ", "change_country_flag = WRE"):
        assert want in imm, want
    assert imm.index("save_scope_as = tfe_honorius_seat") < imm.index("annex_country")
    a = ev[ev.index("name = tfe_stilicho.4.a"):ev.index("name = tfe_stilicho.4.b")]
    b = ev[ev.index("name = tfe_stilicho.4.b"):ev.index("name = tfe_stilicho.4.c")]
    c = ev[ev.index("name = tfe_stilicho.4.c"):]
    assert "kill_character" in a and "tfe_honorius_executed" in a and "is_alive = yes" in a
    assert "move_country = c:EAR" in b and "is_alive = yes" in b
    assert "is_alive = no" in c or "NOT = { character:tfe_honorius ?= { is_alive = yes } }" in c
