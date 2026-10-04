import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
sys.path.insert(0, str(ROOT / "tools"))
import peoples_on_the_road as pr  # noqa: E402
import defs_decline_of_the_west as dw  # noqa: E402

OUT = pr.outputs()
EXP = OUT["in_game/common/expedition_types/tfe_peoples.txt"]
TRIG = OUT["in_game/common/scripted_triggers/tfe_peoples.txt"]
LOC = OUT["main_menu/localization/english/tfe_peoples_l_english.yml"]
# the Carpi are Dacians and the Iazyges Sarmatians: migrators, but no Germanic king's people
NOT_GERMANIC = {"CRP", "IAZ"}


def test_the_people_walk_slowly_overland():
    assert "travel_mode = land" in EXP and f"travel_speed = {pr.TRAVEL_SPEED}" in EXP
    assert "dynamic_first_waypoint = yes" in EXP and "origin = none" in EXP


def test_the_walk_starts_where_the_people_live():
    waypoints = pr.EXPEDITION.find("add_new_waypoint", None, inside=("tfe_wandering_people", "on_start"))
    assert [w.val for w in waypoints] == ["root.var:tfe_people_from", "root.var:tfe_people_to"]


def test_settlers_whose_land_was_lost_go_to_the_capital():
    on_end = EXP.split("on_end = {", 1)[1]
    assert "root.capital" in on_end and "tfe_people_invited" in on_end


def test_every_migrator_people_is_germanic():
    countries = "\n".join(p.read_text(encoding="utf-8-sig") for p in (ROOT / "in_game/setup/countries").glob("*.txt"))
    for tag in dw.MIGRATORS:
        culture = re.search(rf"^{tag} = \{{.*?culture_definition = (\w+)", countries, re.S | re.M)
        assert culture, tag
        assert pr.is_germanic(culture.group(1)) == (tag not in NOT_GERMANIC), (tag, culture.group(1))


def test_the_trigger_is_written_from_the_groups():
    for group in pr.GERMANIC_GROUPS:
        assert f"culture_group:{group}" in TRIG
    assert pr.is_germanic("gothic_culture") and not pr.is_germanic("venedi") and not pr.is_germanic("gallo_roman")


def test_the_road_has_a_name():
    assert re.search(r"^ tfe_wandering_people: ", LOC, re.M) and re.search(r"^ tfe_wandering_people_desc: ", LOC, re.M)


ACTION = "tfe_invite_germanic_settlers"


def test_invite_ends_with_the_migrations():
    assert pr.DOC.find("current_age", "age_2_renaissance", inside=(ACTION,))
    assert not pr.DOC.find("current_age", "age_3_discovery", inside=(ACTION,))


def test_no_settlers_from_an_empty_germania():
    allow = pr.DOC.find("allow", None, inside=(ACTION,))
    assert allow and "pop_size" in str(allow[0].val) and "north_german_region" in str(allow[0].val)


def test_settlers_drain_germania_and_cost_gold():
    assert pr.DOC.find("add_pop_size", None, inside=(ACTION,))
    assert pr.DOC.find("add_gold", str(-pr.SETTLERS_COST), inside=(ACTION,))
    assert pr.DOC.find("cooldown", None, inside=(ACTION,))
    assert pr.DOC.find("start_expedition", None, inside=(ACTION,))


def test_settlers_are_invited_and_join_the_kings_people():
    assert pr.DOC.find("set_variable", "tfe_people_invited", inside=(ACTION, "effect"))
    culture = pr.DOC.find("value", "scope:actor.culture", inside=(ACTION, "effect"))
    assert culture


def test_the_actions_loc_exists():
    for key in (ACTION, f"{ACTION}_desc"):
        assert re.search(rf"^ {key}: ", LOC, re.M), key


ON_ACTION = "in_game/common/on_action/tfe_peoples.txt"


def test_slavic_bands_only_in_their_window():
    text = OUT[ON_ACTION]
    assert "450.1.1" in text and "700.1.1" in text
    assert "slavic_group" in text and "tfe_people_invited" not in text


def test_bands_never_take_land():
    text = OUT[ON_ACTION]
    assert "change_location_owner" not in text and "create_country" not in text


def test_bands_go_south_of_the_danube_only_after_550():
    balkans = pr.BANDS.find(None, None, inside=("tfe_on_slavic_band", "effect", "if"))
    assert any(n.key == "current_date" and n.val == "550.1.1" for n in balkans)
    assert any(n.key == "region:balkan_region" for n in balkans)


def test_bands_drain_their_homeland_and_walk():
    assert pr.BANDS.find("add_pop_size", None, inside=("tfe_on_slavic_band",))
    assert pr.BANDS.find("start_expedition", None, inside=("tfe_on_slavic_band",))
    assert pr.BANDS.find("chance", str(round(pr.BAND_CHANCE * 100)), inside=("tfe_on_slavic_band",))
