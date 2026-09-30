"""The Decline of the West (RoadMap #6): a situation from day one. Phase 1 shows Gildo's Africa and the peoples beyond
the rivers, who take the road from its panel. Static checks: the scripts load and say what the panel shows."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

COMMON = b.MOD / "in_game/common"
SITUATION = COMMON / "situations/tfe_decline_of_the_west.txt"
ON_ACTION = COMMON / "on_action/tfe_decline_of_the_west.txt"
TRIGGERS = COMMON / "scripted_triggers/tfe_decline_of_the_west.txt"
EFFECT = COMMON / "scripted_effects/tfe_migratory.txt"
PANEL = b.MOD / "in_game/gui/panels/situation/tfe_decline_of_the_west.gui"
LOC = b.MOD / "main_menu/localization/english/tfe_decline_of_the_west_l_english.yml"
SCRIPTS = (SITUATION, ON_ACTION, TRIGGERS)
MIGRATORS = {"ALM", "BGD", "FRK", "HAS", "SLX", "SAX", "MKM", "QAD", "LGB", "SLF", "FRS", "AGL", "TGI", "RUG", "SCR",
             "VIS", "GEP", "CRP", "IAZ"}
LISTS = ("tfe_migrators_at_home", "tfe_migrators_on_the_road", "tfe_migrators_settled")


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def test_files_are_balanced_and_bom_prefixed():
    for p in SCRIPTS + (PANEL, LOC):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in SCRIPTS + (PANEL,):
        assert code(p).count("{") == code(p).count("}"), p.name
    assert LOC.read_text(encoding="utf-8-sig").startswith("l_english:")


def test_it_starts_on_day_one_in_phase_one_and_ends_with_the_west():
    assert re.search(r"on_game_start = \{\s*on_actions = \{ tfe_on_start_decline_of_the_west \}", code(ON_ACTION))
    assert "activate_situation = situation:tfe_decline_of_the_west" in code(ON_ACTION)
    s = code(SITUATION)
    assert "set_variable = { name = tfe_decline_phase value = 1 }" in s
    assert "tfe_decline_phase value = 2" not in s   # later phases come in their own PR
    # country_exists, not exists: a landless leftover tag still "exists" (CLAUDE.md)
    can_end = re.search(r"can_end = \{(.*?)\n\t\}", s, re.S).group(1)
    assert "NOT = { country_exists = c:WRE }" in can_end
    assert re.search(r"limit = \{ NOT = \{ country_exists = c:WRE \} \}\s*end_situation = situation:tfe_decline_of_the_west", s)


def test_the_migrators_are_the_peoples_of_germania_and_dacia():
    trigger = re.search(r"tfe_is_migrator = \{(.*?)\n\}", code(TRIGGERS), re.S).group(1)
    assert set(re.findall(r"tag = (\w+)", trigger)) == MIGRATORS
    countries = (b.MOD / "main_menu/setup/start/10_countries.txt").read_text(encoding="utf-8-sig")
    assert all(f"\n\t\t{t} = {{" in countries for t in MIGRATORS)
    # the Huns push the migrators, not only the army-based Vandals
    storm = code(COMMON / "situations/tfe_hunnic_storm.txt")
    road = storm[storm.index("tag = GEP"):storm.index("tfe_hunnic_storm.2")]
    assert "tfe_is_migrator = yes" in road and "country_type = army" not in road


def test_who_sees_it():
    visible = re.search(r"visible = \{(.*?)\n\t\}", code(SITUATION), re.S).group(1)
    assert "tag = WRE" in visible and "tag = EAR" in visible and "tfe_is_migrator = yes" in visible
    assert re.search(r"country_exists = c:GILDO\s*this = c:GILDO", visible)   # Gildo's tag is made when he rises


def test_the_panel_shows_the_phase_africa_and_the_migrators():
    panel = code(PANEL)
    assert panel.startswith("situation_panel = {")
    assert "GetVariable('tfe_decline_phase')" in panel
    assert "GetVariable('tfe_gildo_revolt_fired').IsSet" in panel   # scripted_triggers/tfe_gildo.txt's trigger
    assert "tfe_gildo_progress" in LOC.read_text(encoding="utf-8-sig")
    for name in LISTS:
        assert f"GetList('{name}')" in panel, name
    # the lists are kept by one effect: the situation monthly, and at once when a host sets out
    effect = code(EFFECT)
    for name in LISTS:
        assert f"add_to_variable_list = {{ name = {name} target = scope:tfe_migrator }}" in effect, name
    assert "tfe_list_the_migrators = yes" in code(SITUATION) and effect.count("tfe_list_the_migrators = yes") == 1


def test_art_the_panel_uses_exists():
    for path in re.findall(r'texture = "(gfx/[^"]+)"', code(PANEL)):
        if "component_masks" in path:
            continue
        assert any((root / "main_menu" / path).exists() or (root / "in_game" / path).exists()
                   for root in (b.MOD, b.GAME)), path


def test_everything_shown_is_localized():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    wanted = {"tfe_decline_of_the_west", "tfe_decline_of_the_west_desc"}
    wanted |= set(re.findall(r'text = "(TFE_\w+)"', code(PANEL)))
    wanted |= set(re.findall(r'desc = "(\w+)"', code(SITUATION)))
    wanted |= set(re.findall(r"custom_tooltip = (?:\{\s*text = )?(\w+)", code(SITUATION)))
    assert not wanted - keys, sorted(wanted - keys)
