"""The 395 opening: dated events on named people (Stilicho, Rufinus, Gildo, Constantine III)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

EVENT = b.MOD / "in_game/events/tfe_opening.txt"
ON_ACTION = b.MOD / "in_game/common/on_action/tfe_opening.txt"
CB = b.MOD / "in_game/common/casus_belli/tfe_usurpers.txt"
MODS = b.MOD / "main_menu/common/static_modifiers/tfe_opening.txt"
FLAGS = b.MOD / "main_menu/common/coat_of_arms/coat_of_arms/tfe_countries.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_opening_l_english.yml"
SCRIPTS = (EVENT, ON_ACTION, CB, MODS)


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def test_files_are_balanced_and_bom_prefixed():
    for p in SCRIPTS + (LOC,):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in SCRIPTS:
        assert code(p).count("{") == code(p).count("}"), p.name


def test_everything_shown_is_localized_and_defined():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    ev, oa = code(EVENT), code(ON_ACTION)
    wanted = set(re.findall(r"(?:title|desc|name) = (tfe_opening\.[\w.]+)", ev))
    cbs = set(re.findall(r"^(cb_\w+) = \{", code(CB), re.M))
    wanted |= cbs | {f"{c}_desc" for c in cbs}
    mods = set(re.findall(r"^(\w+) = \{", code(MODS), re.M))
    assert mods == set(re.findall(r"country_modifier = \{ modifier = (\w+)", ev + oa)) | {"tfe_rufinus_prefecture"}
    wanted |= {f"STATIC_MODIFIER_{k}_{m}" for m in mods for k in ("NAME", "DESC")}
    for tag in re.findall(r"change_country_name = (\w+)", ev):
        wanted |= {tag, f"{tag}_ADJ"}
    assert not wanted - keys, sorted(wanted - keys)
    flags = set(re.findall(r"^(\w+) = \{", code(FLAGS), re.M))
    assert set(re.findall(r"change_country_flag = (\w+)", ev)) <= flags
    assert set(re.findall(r"casus_belli:(\w+)", ev)) <= cbs


def test_every_opening_event_is_scheduled():
    fired = set(re.findall(r"(tfe_opening\.\d+)", code(ON_ACTION) + code(EVENT).split("tfe_opening.1 = {")[1]))
    defined = set(re.findall(r"^(tfe_opening\.\d+) = \{", code(EVENT), re.M))
    assert defined and fired >= defined, defined - fired


def test_usurpers_name_their_enemy_both_ways():
    ev = code(EVENT)
    # each usurper is spawned with a claim on the Augustus, who gets one back
    assert ev.count("create_country_from_location") == 2
    assert ev.count("name = tfe_usurper_against value = root") == 2
    assert ev.count("name = tfe_usurper value = scope:tfe_usurper") == 2


def test_events_do_not_crash_the_game():
    ev = code(EVENT)
    # an unknown outcome is a load error; a scope the East's event was only handed crashed the game on the next tick
    assert set(re.findall(r"outcome = (\w+)", ev)) <= {"positive", "neutral", "negative"}
    east = ev.split("tfe_opening.4 = {")[1].split("tfe_opening.5 = {")[0]
    assert "c:WRE.var:tfe_usurper = { save_scope_as = tfe_usurper }" in east
    # spawned countries need a government, and the treasury to not go bankrupt on day one
    assert ev.count("change_government_type = government_type:monarchy") == ev.count("create_country_from_location")
    assert ev.count("add_gold = ") == ev.count("create_country_from_location")
