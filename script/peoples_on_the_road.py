"""Peoples on the road: unarmed migration. An expedition walks a people across the map; its pops leave where it starts
and arrive where it ends. Germanic kings invite their people into the Roman land they took; Slavic bands drift west."""
import functools
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CharacterTrig, CountryFx, CountryTrig, CultureTrig, ExpeditionFx, LocationFx, LocationTrig
from pdx.objects import Doc
from pdx.objects_defs import Defs

EXPEDITION_TYPE = "tfe_wandering_people"
SETTLER_SIZE = 2  # pop_size, the unit vanilla's setup counts pops in
BAND_SIZE = 1
TRAVEL_SPEED = 0.25
SETTLERS_COST = 150
SETTLERS_COOLDOWN = 3
BAND_CHANCE = 0.25
GERMANIC_GROUPS = {"german_group", "netherlandish_group", "scandinavian_group"}
# Germanic cultures filed outside those groups. None today: TFE moves gothic_culture into german_group
# (cultures/tfe_cultures.txt), and every other migrator people already sits in one. Add one here and the trigger follows.
GERMANIC_CULTURES: set[str] = set()
# the variables a people on the road carries, on the country that sent it
PEOPLE_VARS = ("tfe_people_from", "tfe_people_to", "tfe_people_culture", "tfe_people_religion", "tfe_people_size")


@functools.cache
def culture_groups():
    """culture -> its groups, from vanilla and tfe_cultures.txt (a REPLACE: there wins)."""
    import borders as b  # numpy, so only when a test asks
    files = [*sorted((b.GAME / "in_game/common/cultures").glob("*.txt")), b.MOD / "in_game/common/cultures/tfe_cultures.txt"]
    groups = {}
    for p in files:
        for m in re.finditer(r"^(?:REPLACE:)?(\w+)\s*=\s*\{(.*?)^\}", p.read_text(encoding="utf-8-sig"), re.M | re.S):
            g = re.search(r"culture_groups\s*=\s*\{([^}]*)\}", m.group(2))
            groups[m.group(1)] = set(g.group(1).split()) if g else set()
    return groups


def is_germanic(culture: str) -> bool:
    """the Python mirror of tfe_is_germanic_culture"""
    return culture in GERMANIC_CULTURES or bool(culture_groups().get(culture, set()) & GERMANIC_GROUPS)


def triggers():
    d = Defs()
    d.note("TFE: peoples on the road (expedition_types/tfe_peoples.txt). Scope: a culture. The Germanic peoples, whose kings may\n"
           "invite settlers from Germania (generic_actions/tfe_peoples.txt). Written from script/peoples_on_the_road.py.")
    with d.trigger("tfe_is_germanic_culture", CultureTrig) as t, t.or_() as o:
        for group in sorted(GERMANIC_GROUPS):
            o.has_culture_group(f"culture_group:{group}")
        for culture in sorted(GERMANIC_CULTURES):
            o.compare("this", "=", f"culture:{culture}")
    return d


def clear_the_road(fx: CountryFx):
    """the band is home or gone: its variables go, and the elder made only to lead it leaves the court"""
    for var in (*PEOPLE_VARS, "tfe_people_invited"):
        fx.remove_variable(var)
    with fx.link("scope:expedition", ExpeditionFx) as x, x.go_expedition_leader(op="?=") as leader:
        leader.save_scope_as("tfe_people_leader_done")
    with fx.if_() as i:
        with i.limit() as t:
            t.exists("scope:tfe_people_leader_done")
        i.kill_character_silently("scope:tfe_people_leader_done")


def wandering_people(doc: Doc):
    doc.loc.add(EXPEDITION_TYPE, "A People on the Road")
    doc.loc.add(f"{EXPEDITION_TYPE}_desc", "Families, herds and wagons on the move, looking for land to settle.")
    doc.note("A people on the road: the country sets the variables (tfe_people_*), then starts it with a new character as its\n"
             "leader. It walks overland from tfe_people_from to tfe_people_to and settles there as peasants.\n"
             "GAP: no expedition-type builder (doc.entry)")
    with doc.entry(EXPEDITION_TYPE) as e:
        e.note("one band at a time per country; it also keeps the player from starting a second one in the Expeditions panel")
        e.field("unique", True)
        e.field("travel_speed", TRAVEL_SPEED)
        e.field("travel_mode", "land")
        e.note("the first waypoint is the departure: the people's homeland, not the capital")
        e.field("dynamic_first_waypoint", True)
        e.field("origin", "none")
        e.field("ai", False)
        e.field("show_start_message", False)
        e.field("show_end_message", False)
        with e.triggers("potential", CountryTrig) as t:
            t.has_variable("tfe_people_to")
        with e.triggers("leader", CharacterTrig) as t:
            t.is_expedition_leader(False)
        with e.effects("on_start", CountryFx) as fx, fx.link("scope:expedition", ExpeditionFx) as x:
            x.add_new_waypoint("root.var:tfe_people_from")
            x.add_new_waypoint("root.var:tfe_people_to")
        with e.effects("on_end", CountryFx) as fx:
            with fx.link("root.var:tfe_people_to", LocationFx) as to:
                to.save_scope_as("tfe_people_arrive")
            fx.note("invited settlers whose land was lost on the way settle by the king's seat; a band settles wherever it is")
            with fx.if_() as i:
                with i.limit() as t:
                    t.has_variable("tfe_people_invited")
                    with t.not_() as n, n.link("scope:tfe_people_arrive", LocationTrig) as arrive:
                        arrive.compare("owner", "?=", "root")
                    t.exists("root.capital")
                with i.link("root.capital", LocationFx) as cap:
                    cap.save_scope_as("tfe_people_arrive")
            with fx.link("scope:tfe_people_arrive", LocationFx) as arrive:
                arrive.add_pop(culture="root.var:tfe_people_culture", religion="root.var:tfe_people_religion",
                               type="pop_type:peasants", size="root.var:tfe_people_size")
            clear_the_road(fx)
        with e.effects("on_fail", CountryFx) as fx:
            fx.note("lost on the road: the people who left are gone")
            clear_the_road(fx)


def build():
    """the expedition type and the generic action; one loc for both"""
    exp, doc = Doc(), Doc()
    exp.note("TFE: peoples on the road. Written from script/peoples_on_the_road.py.")
    wandering_people(exp)
    doc.loc = exp.loc
    return exp, doc


EXPEDITION, DOC = build()


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/expedition_types/tfe_peoples.txt": EXPEDITION.text(),
            "in_game/common/scripted_triggers/tfe_peoples.txt": triggers().text(),
            "main_menu/localization/english/tfe_peoples_l_english.yml": DOC.loc.text()}
