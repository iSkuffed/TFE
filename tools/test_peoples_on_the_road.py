import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
sys.path.insert(0, str(ROOT / "tools"))
import peoples_on_the_road as pr  # noqa: E402
import defs_decline_of_the_west as dw  # noqa: E402
from pdx.core import find  # noqa: E402

OUT = pr.outputs()
EXP = OUT["in_game/common/expedition_types/tfe_peoples.txt"]
TRIG = OUT["in_game/common/scripted_triggers/tfe_peoples.txt"]
LOC = OUT["main_menu/localization/english/tfe_peoples_l_english.yml"]
# the Carpi are Dacians and the Iazyges Sarmatians: migrators, but no Germanic king's people
NOT_GERMANIC = {"CRP", "IAZ"}
PRICES = OUT["in_game/common/prices/tfe_peoples.txt"]


def test_the_people_walk_slowly_overland():
    assert "travel_mode = land" in EXP and f"travel_speed = {pr.TRAVEL_SPEED}" in EXP
    assert "dynamic_first_waypoint = yes" in EXP and "origin = none" in EXP


def test_the_walk_starts_where_the_people_live():
    waypoints = pr.EXPEDITION.find("add_new_waypoint", None, inside=("tfe_wandering_people", "on_start"))
    assert [w.val for w in waypoints] == ["root.var:tfe_people_from", "root.var:tfe_people_to"]


def test_settlers_whose_land_was_lost_go_to_the_capital():
    on_end = EXP.split("on_end = {", 1)[1]
    assert "root.capital" in on_end and "tfe_people_invited" in on_end


def test_every_migrator_people_may_invite_settlers():
    """the Germanic ones by their group, the Carpi and Iazyges by name"""
    countries = "\n".join(p.read_text(encoding="utf-8-sig") for p in (ROOT / "in_game/setup/countries").glob("*.txt"))
    for tag in dw.MIGRATORS:
        culture = re.search(rf"^{tag} = \{{.*?culture_definition = (\w+)", countries, re.S | re.M).group(1)
        assert pr.is_germanic(culture) or culture in pr.KIN_CULTURES, (tag, culture)
    for culture in pr.KIN_CULTURES:
        assert pr.DOC.find(None, f"culture:{culture}", inside=(ACTION, "potential")), culture


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


def test_only_the_barbaricum_sends_for_kin():
    assert pr.DOC.find("is_member_of_international_organization", "international_organization:tfe_barbaricum",
                       inside=(ACTION, "potential"))


def test_the_common_folk_take_the_road_and_arrive_as_peasants_and_tribesmen():
    allow = str(pr.DOC.find("allow", None, inside=(ACTION,))[0].val)
    assert "peasants" in allow and "tribesmen" in allow and "nobles" not in allow
    types = [n.val for n in pr.EXPEDITION.find("type", None, inside=("tfe_wandering_people", "on_end"))]
    assert types == ["pop_type:peasants", "pop_type:tribesmen"]
    assert sum(share for _, share in pr.ARRIVE_AS) == 1
    assert pr.EXPEDITION.find("multiply", "0.4", inside=("tfe_wandering_people", "on_end"))


def test_the_carpi_send_only_for_their_own_kin():
    """Germanic pops are a source only when the king is Germanic"""
    allow = str(pr.DOC.find("allow", None, inside=(ACTION,))[0].val)
    assert "scope:actor.culture" in allow and allow.count("tfe_is_germanic_culture") >= 2 * len(pr.SOURCE_REGIONS)


def test_no_settlers_from_an_empty_carpathia_either():
    allow = str(pr.DOC.find("allow", None, inside=(ACTION,))[0].val)
    assert "carpathia_region" in allow and "scope:actor.culture" in allow


def test_settlers_are_thousands_gathered_from_many_peoples():
    """10 pop_size (ten thousand people), at most half of any one pop, the king's own people first"""
    assert pr.SETTLER_SIZE >= 10 and pr.SETTLER_SHARE <= 0.5
    loops = pr.DOC.find("every_in_list", None, inside=(ACTION, "effect"))
    assert len(loops) == 2
    own, rest = (str(loop.val) for loop in loops)
    assert "NOT" not in own and "NOT" in rest, "no pop gives a second share in the second pass"
    assert pr.DOC.find("multiply", str(pr.SETTLER_SHARE), inside=(ACTION, "effect"))
    assert pr.DOC.find("value", "var:tfe_settlers_gathered", inside=(ACTION, "effect"))


def test_settlers_cost_a_year_of_income():
    """vanilla's scaled_gold follows population (25 gold for 400,000 Alamanni): a year of trade and tax is the wealth"""
    assert pr.DOC.find("price", f"price:{pr.SETTLERS_PRICE}", inside=(ACTION,))
    assert pr.DOC.find("value", "scope:actor.monthly_income_trade_and_tax", inside=(ACTION, "price_modifier"))
    assert pr.DOC.find("min", pr.SETTLERS_MIN_GOLD, inside=(ACTION, "price_modifier"))
    assert re.search(rf"^{pr.SETTLERS_PRICE} = {{\s*gold = 1\s*}}", PRICES, re.M)
    assert not pr.DOC.find("add_gold", None, inside=(ACTION,))


def test_every_price_has_its_cost_modifier_and_name():
    """1.4 logs a price with no <price>_cost_modifier type or no loc"""
    types = (ROOT / "main_menu/common/modifier_type_definitions/tfe_statuses_and_prices.txt").read_text(encoding="utf-8-sig")
    loc = "".join(f.read_text(encoding="utf-8-sig") for f in (ROOT / "main_menu/localization/english").glob("tfe_*.yml"))
    for f in (ROOT / "in_game/common/prices").glob("tfe_*.txt"):
        for price in re.findall(r"^(\w+) = \{", f.read_text(encoding="utf-8-sig"), re.M):
            assert f"{price}_cost_modifier=" in types, price
            assert f" {price}:" in loc, price


def test_a_tooltip_reads_no_unset_variable():
    """the tooltip's dry run sets no variable and makes no leader: 900,000 errors in ten minutes of hovering"""
    guard = [n for n in pr.DOC.find("if", None, inside=(ACTION, "effect"))
             if find(n.val, "has_variable", "tfe_settlers_wanted", inside=("limit",))]
    assert guard and len(find(guard[0].val, "every_in_list")) == 2
    assert pr.DOC.find("exists", "scope:tfe_people_leader", inside=(ACTION, "effect"))


def test_a_band_with_no_road_settles_all_the_same():
    """the Rugii's bands for Crete found no road and vanished, 10,000 people at a time"""
    on_fail = EXP[EXP.index("on_fail"):]
    assert "add_pop" in on_fail


def test_the_tooltip_names_the_source_and_the_cooldown():
    for key in (f"{ACTION}_source_tt", f"{ACTION}_cooldown_tt"):
        assert re.search(rf"^ {key}: ", LOC, re.M), key
    assert pr.DOC.find("custom_tooltip", f"{ACTION}_cooldown_tt", inside=(ACTION, "effect"))
    assert f"{pr.SETTLERS_COOLDOWN} years" in LOC


def test_settlers_drain_germania():
    assert pr.DOC.find("add_pop_size", None, inside=(ACTION,))
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


def test_a_player_invites_from_the_barbaricums_window():
    """an IO action: choose the Barbaricum, then the land; no GUI file of ours"""
    assert pr.DOC.find("type", "internationalorganization", inside=(ACTION,))
    assert pr.DOC.find(None, "international_organization_type:tfe_barbaricum", inside=(ACTION, "select_trigger"))
    flags = [n.val for n in pr.DOC.find("target_flag", None, inside=(ACTION, "select_trigger"))]
    assert flags == ["recipient", "target"]
    assert not (ROOT / "in_game/gui/location_window.gui").exists()


def test_no_people_gives_more_than_is_wanted():
    """change_variable's max is an operation (max(), a floor), so a band came to 29: the cap is clamp_variable"""
    assert pr.DOC.find("clamp_variable", None, inside=(ACTION,))
    assert not pr.DOC.find("max", "var:tfe_settlers_wanted", inside=(ACTION, "change_variable"))


def test_the_arrival_sizes_are_set_on_the_country():
    """on_fail runs in another scope: the sizes set there were never read, and the pops arrived at the wrong size"""
    for hook in ("on_end", "on_fail"):
        assert pr.EXPEDITION.find("set_variable", None, inside=(hook, "root"))
