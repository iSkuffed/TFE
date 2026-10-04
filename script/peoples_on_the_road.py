"""Peoples on the road: unarmed migration. An expedition walks a people across the map; its pops leave where it starts
and arrive where it ends. Germanic kings invite their people into the Roman land they took; Slavic bands drift west."""
import functools
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import (AreaFx, CharacterTrig, CountryFx, CountryTrig, CultureTrig, ExpeditionFx, LocationFx, LocationTrig, PopFx,
                     PopTrig, RegionFx, RegionTrig, ValueFx)
from pdx.core import Cmp, Q
from pdx.objects import Doc
from pdx.objects_defs import Defs

EXPEDITION_TYPE = "tfe_wandering_people"
SETTLER_SIZE = 2  # pop_size, the unit vanilla's setup counts pops in
BAND_SIZE = 1
TRAVEL_SPEED = 0.25
SETTLERS_COST = 50
SETTLERS_COOLDOWN = 3
BAND_CHANCE = 0.25
GERMANIC_GROUPS = {"german_group", "netherlandish_group", "scandinavian_group"}
# Germanic cultures filed outside those groups. None today: TFE moves gothic_culture into german_group
# (cultures/tfe_cultures.txt), and every other migrator people already sits in one. Add one here and the trigger follows.
GERMANIC_CULTURES: set[str] = set()
ACTOR = "scope:actor"
ACTION = "tfe_invite_germanic_settlers"
# Germania, where the settlers come from
SOURCE_REGIONS = ("north_german_region", "south_german_region", "baltic_region")
# the Latin peoples of the West whose land a Germanic king rules: when one of them outnumbers half his own, he invites more
ROMAN_CULTURES = ("roman_culture", "gallo_roman", "hispano_roman", "afro_roman", "romano_british", "illyro_roman",
                  "thraco_roman")
SLAVS = "culture_group:slavic_group"
# where the Slavs live in 450, and where their bands go: the lands the Germanic hosts left (balkan_region after 550)
SLAVIC_HOMELAND = ("polesia_area", "volhynia_area", "white_ruthenia_area", "red_ruthenia_area", "right_bank_ukraine_area",
                   "lesser_poland_area", "mazovia_area")
BAND_TARGETS = ("brandenburg_area", "mecklenburg_area", "pomerania_area", "upper_saxony_area", "bohemia_area",
                "moravia_area", "silesia_area")
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


def send(fx: CountryFx, *, frm: str, to: str, culture: str, religion: str, size: float):
    """the country sends a people from `frm` to `to`: its variables, an elder to lead it, and the walk"""
    for var, value in zip(PEOPLE_VARS, (frm, to, culture, religion, size)):
        fx.set_variable(name=var, value=value)
    fx.create_character(age=35, culture=culture, religion=religion, save_scope_as="tfe_people_leader")
    fx.start_expedition(type=f"expedition_type:{EXPEDITION_TYPE}", leader="scope:tfe_people_leader")


def germanic_settlers(t: PopTrig):
    t.pop_size(SETTLER_SIZE, op=">=")
    with t.go_culture() as c:
        c.tfe_is_germanic_culture(True)


def invite_settlers(doc: Doc):
    doc.loc.add(ACTION, "Invite Germanic Settlers")
    doc.loc.add(f"{ACTION}_desc", "Our kin still live beyond the Rhine and the Danube, on poor land. Send for them: they will "
                "walk to the land we took from the Romans and settle it as our own people.")
    doc.loc.add(f"{ACTION}_tt", "A band of settlers sets out from Germania and walks to the chosen [location|e]. There they "
                "settle as [peasants|e] of our [culture|e]. If the land is no longer ours when they arrive, they settle by "
                "our [capital|e].")
    doc.loc.add(f"{ACTION}_choose_location", "Choose the land to settle")
    doc.loc.add(f"{ACTION}_no_location", "All our land is already settled by our own people.")
    doc.loc.add(f"{ACTION}_source_tt", f"Germania still has a people of our kin of at least {SETTLER_SIZE} [pop_size|e] to send")
    doc.loc.add("tfe_people_already_on_the_road_tt", "We have no people on the road already")
    doc.loc.add("tfe_invite_settlers", "Settlers Invited")
    doc.note("Invite Germanic Settlers: a Germanic king sends for his people in Germania to settle the Roman land he took.\n"
             "They walk there (expedition_types/tfe_peoples.txt). Ends with the Migrations, in 500.")
    with doc.generic_action(ACTION) as a:
        a.note("a player invites from the location panel: a button there (in_game/gui/location_window.gui) passes the\n"
               "location as scope:target, so the select_trigger below is only the AI's list")
        a.field("type", "owncountry")
        with a.triggers("potential") as t:
            with t.link(ACTOR, CountryTrig) as c, c.go_culture() as cu:
                cu.tfe_is_germanic_culture(True)
            with t.or_() as o:
                o.current_age("age_1_traditions")
                o.current_age("age_2_renaissance")
        with a.triggers("allow") as t:
            with t.link(ACTOR, CountryTrig) as c:
                with c.custom_tooltip_block("tfe_people_already_on_the_road_tt") as ct:
                    ct.not_(lambda n: n.has_variable("tfe_people_to"))
                c.gold(SETTLERS_COST, op=">=")
            t.note("decades of drain may empty Germania: then there is no one left to send")
            with t.custom_tooltip_block(f"{ACTION}_source_tt") as ct, ct.or_() as o:
                for region in SOURCE_REGIONS:
                    with o.link(f"region:{region}", RegionTrig) as r, r.any_location_in_region() as loc, loc.any_pop() as p:
                        germanic_settlers(p)
        a.field("ai_tick", "monthly")
        a.field("ai_tick_frequency", 12)
        a.field("automation_tick", "never")
        a.field("automation_tick_frequency", 12)
        a.data("cooldown", type="tfe_invite_settlers", years=SETTLERS_COOLDOWN)
        a.note("any land of ours whose people are not yet ours")
        with a.block("select_trigger") as s:
            s.field("looking_for_a", "location")
            s.field("source", "actor")
            s.field("target_flag", "target")
            s.field("name", Q(f"{ACTION}_choose_location"))
            s.field("none_available_msg_key", Q(f"{ACTION}_no_location"))
            s.data("column", data="name")
            s.data("column", data="population")
            with s.triggers("visible", LocationTrig) as t:
                t.compare("owner", "?=", ACTOR)
                t.not_(lambda n: n.compare("dominant_culture", "?=", "scope:actor.culture"))
        with a.effects("effect") as e:
            with e.link(ACTOR, CountryFx) as c:
                c.add_gold(-SETTLERS_COST)
            e.custom_tooltip(f"{ACTION}_tt")
            with e.hidden_effect() as h:
                h.note("the source: the largest pop of the king's own people in Germania, else the largest Germanic one")
                for region in SOURCE_REGIONS:
                    with h.link(f"region:{region}", RegionFx) as r, r.every_location_in_region() as loc, loc.every_pop() as p:
                        with p.limit() as t:
                            germanic_settlers(t)
                        p.add_to_temporary_list("tfe_settler_pops")
                with h.ordered_in_list(PopFx, list="tfe_settler_pops", order_by="pop_size") as p:
                    with p.limit() as t:
                        t.compare("culture", "=", "scope:actor.culture")
                    p.save_scope_as("tfe_settler_pop")
                with h.if_() as i:
                    with i.limit() as t:
                        t.not_(lambda n: n.exists("scope:tfe_settler_pop"))
                    with i.ordered_in_list(PopFx, list="tfe_settler_pops", order_by="pop_size") as p:
                        p.save_scope_as("tfe_settler_pop")
                with h.link("scope:tfe_settler_pop", PopFx, op="?=") as p:
                    with p.go_location() as loc:
                        loc.save_scope_as("tfe_settler_home")
                    p.note("the settlers join the king's people (his culture), and keep their own gods")
                    with p.link(ACTOR, CountryFx) as c:
                        send(c, frm="scope:tfe_settler_home", to="scope:target", culture="scope:actor.culture",
                             religion="scope:tfe_settler_pop.religion", size=SETTLER_SIZE)
                        c.set_variable("tfe_people_invited")
                    p.add_pop_size(value=-SETTLER_SIZE)
        with a.effects("ai_will_do", ValueFx) as v:
            v.add(0)
            v.note("gold to spare, and Roman land to fill with our own people")
            with v.if_() as i:
                with i.limit() as t:
                    with t.link(ACTOR, CountryTrig) as c:
                        c.gold(2 * SETTLERS_COST, op=">=")
                    with t.link("scope:target", LocationTrig) as loc, loc.not_() as n, n.go_dominant_culture(op="?=") as cu:
                        cu.tfe_is_germanic_culture(True)
                i.add(10)
                i.note("the Romans we rule outnumber half our own people: settle more before they swallow us")
                with i.if_() as j:
                    with j.limit() as t, t.link(ACTOR, CountryTrig) as c, c.or_() as o:
                        for rc in ROMAN_CULTURES:
                            with o.and_() as r:
                                r.has_accepted_culture(f"culture:{rc}")
                                r.culture_percentage_in_country(culture="scope:actor.culture", value=Cmp("<", {
                                    "value": Q(f"culture_percentage_in_country(culture:{rc})"), "multiply": 2}))
                    j.add(10)


def slavic_band(t: PopTrig):
    t.pop_size(BAND_SIZE, op=">=")
    with t.go_culture() as c:
        c.has_culture_group(SLAVS)


def in_homeland(t: LocationTrig):
    with t.or_() as o:
        for area in SLAVIC_HOMELAND:
            o.compare("area", "=", f"area:{area}")


def band_target(loc: LocationFx):
    """dry land a band can walk to, whoever owns it"""
    with loc.limit() as t:
        t.is_land(True)
        t.is_passable(True)
    loc.add_to_temporary_list("tfe_band_targets")


def slavic_bands():
    d = Defs()
    d.note("TFE: peoples on the road. From 450 to 700 the Slavs drift west and south into the lands the Germanic hosts left:\n"
           "each year a Slavic country with its people in the homeland may send a band (expedition_types/tfe_peoples.txt).\n"
           "A band only adds people where it settles: nobody loses land. Written from script/peoples_on_the_road.py.")
    d.hook("yearly_country_pulse", "tfe_on_slavic_band")
    with d.on_action("tfe_on_slavic_band") as a:
        with a.trigger(CountryTrig) as t:
            t.current_date("450.1.1", op=">=")
            t.current_date("700.1.1", op="<")
            with t.go_culture() as c:
                c.has_culture_group(SLAVS)
            t.not_(lambda n: n.has_variable("tfe_people_to"))
            with t.any_owned_location() as loc:
                in_homeland(loc)
                with loc.any_pop() as p:
                    slavic_band(p)
        with a.effect(CountryFx) as e, e.random(round(BAND_CHANCE * 100)) as r:
            r.note("from the largest Slavic pop in our homeland")
            with r.ordered_pop(order_by="pop_size") as p:
                with p.limit() as t:
                    slavic_band(t)
                    with t.go_location() as loc:
                        in_homeland(loc)
                p.save_scope_as("tfe_band_pop")
                with p.go_location() as loc:
                    loc.save_scope_as("tfe_band_home")
            r.note("to the land the hosts emptied, the emptier the likelier")
            for area in BAND_TARGETS:
                with r.link(f"area:{area}", AreaFx) as ar, ar.every_location_in_area() as loc:
                    band_target(loc)
            with r.if_() as i:
                with i.limit() as t:
                    t.current_date("550.1.1", op=">=")
                i.note("over the Danube, once Justinian's forts stand empty")
                with i.link("region:balkan_region", RegionFx) as rg, rg.every_location_in_region() as loc:
                    band_target(loc)
            with r.random_in_list(LocationFx, list="tfe_band_targets",
                                  weight={"base": 1, "modifier": {"add": {"value": 20, "subtract": "population", "min": 0}}}) as loc:
                loc.save_scope_as("tfe_band_to")
            with r.if_() as i:
                with i.limit() as t:
                    t.exists("scope:tfe_band_pop")
                    t.exists("scope:tfe_band_to")
                send(i, frm="scope:tfe_band_home", to="scope:tfe_band_to", culture="scope:tfe_band_pop.culture",
                     religion="scope:tfe_band_pop.religion", size=BAND_SIZE)
                with i.link("scope:tfe_band_pop", PopFx) as p:
                    p.add_pop_size(value=-BAND_SIZE)
    return d


def build():
    """the expedition type and the generic action; one loc for both"""
    exp, doc = Doc(), Doc()
    exp.note("TFE: peoples on the road. Written from script/peoples_on_the_road.py.")
    wandering_people(exp)
    doc.loc = exp.loc
    doc.note("TFE: peoples on the road. Written from script/peoples_on_the_road.py.")
    invite_settlers(doc)
    return exp, doc


EXPEDITION, DOC = build()
BANDS = slavic_bands()


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/expedition_types/tfe_peoples.txt": EXPEDITION.text(),
            "in_game/common/scripted_triggers/tfe_peoples.txt": triggers().text(),
            "in_game/common/generic_actions/tfe_peoples.txt": DOC.text(),
            "in_game/common/on_action/tfe_peoples.txt": BANDS.text(),
            "main_menu/localization/english/tfe_peoples_l_english.yml": DOC.loc.text()}
