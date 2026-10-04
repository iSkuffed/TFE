"""Peoples on the road: unarmed migration. An expedition walks a people across the map; its pops leave where it starts
and arrive where it ends. Germanic kings invite their people into the Roman land they took; Slavic bands drift west."""
import functools
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import (AreaFx, CharacterTrig, CountryFx, CountryTrig, CultureTrig, ExpeditionFx, InternationalOrganizationTrig,
                     LocationFx, LocationTrig, PopFx, PopTrig, RegionFx, RegionTrig, ValueFx)
from pdx.core import Cmp, Q
from pdx.objects import Doc
from pdx.objects_defs import Defs

EXPEDITION_TYPE = "tfe_wandering_people"
SETTLER_SIZE = 10  # pop_size, the unit vanilla's setup counts pops in: 1 is a thousand people
SETTLER_SHARE = 0.5  # each pop in Germania gives up to this share of itself to a band of settlers
SOURCE_MIN = 1  # a pop smaller than this has no one to spare
BAND_SIZE = 1
TRAVEL_SPEED = 0.25
# a people arrives as peasants and tribesmen: settling the tribesmen is work left for the king
ARRIVE_AS = (("peasants", 0.6), ("tribesmen", 0.4))
# who takes the road: the common folk, not the nobles, clergy or burghers
MOVERS = ("peasants", "tribesmen")
SETTLERS_PRICE = "tfe_invite_settlers_price"
SETTLERS_INCOME_MONTHS = 12  # a year of the king's trade and tax income (vanilla's scaled_gold follows population)
SETTLERS_MIN_GOLD = 50
SETTLERS_COOLDOWN = 3
BAND_CHANCE = 0.25
GERMANIC_GROUPS = {"german_group", "netherlandish_group", "scandinavian_group"}
# Germanic cultures filed outside those groups. None today: TFE moves gothic_culture into german_group
# (cultures/tfe_cultures.txt), and every other migrator people already sits in one. Add one here and the trigger follows.
GERMANIC_CULTURES: set[str] = set()
ACTOR = "scope:actor"
ACTION = "tfe_invite_germanic_settlers"
# the Carpi (Dacians) and the Iazyges (Sarmatians) are no Germanic peoples, but walk with the Barbaricum and send for
# their own kin in the Carpathians as the Germanic kings do
KIN_CULTURES = ("dacian", "iazyges")
# Germania and the Carpathians, where the settlers come from
SOURCE_REGIONS = ("north_german_region", "south_german_region", "baltic_region", "carpathia_region")
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
            settle(fx)
        with e.effects("on_fail", CountryFx) as fx:
            fx.note("no road there (an island, a strait): they cross by boat and settle all the same")
            settle(fx)


def settle(fx: CountryFx):
    """the band arrives: peasants and tribesmen at its target, or by the king's seat if the target is no longer his"""
    fx.note("the Expedition Lost popup reads on_fail again once the road is cleared: settle only while the band is there")
    with fx.if_() as g:
        g.limit(lambda t: t.link("root", CountryTrig, lambda r: r.has_variable("tfe_people_size")))
        with g.link("root.var:tfe_people_to", LocationFx) as to:
            to.save_scope_as("tfe_people_arrive")
        g.note("invited settlers whose land was lost on the way settle by the king's seat; a band settles wherever it is")
        with g.if_() as i:
            with i.limit() as t:
                t.has_variable("tfe_people_invited")
                with t.not_() as n, n.link("scope:tfe_people_arrive", LocationTrig) as arrive:
                    arrive.compare("owner", "?=", "root")
                t.exists("root.capital")
            with i.link("root.capital", LocationFx) as cap:
                cap.save_scope_as("tfe_people_arrive")
        g.note("whatever they were at home, they arrive as peasants and tribesmen; the shares are inline, since the\n"
               "Expedition Lost popup dry-runs on_fail first, where a variable set here would not be there yet")
        with g.link("scope:tfe_people_arrive", LocationFx) as arrive:
            for pop_type, share in ARRIVE_AS:
                arrive.add_pop(culture="root.var:tfe_people_culture", religion="root.var:tfe_people_religion",
                               type=f"pop_type:{pop_type}", size={"value": "root.var:tfe_people_size", "multiply": share})
    clear_the_road(fx)


def send(fx: CountryFx, *, frm: str, to: str, culture: str, religion: str, size: float | str):
    """the country sends a people from `frm` to `to`: its variables, an elder to lead it, and the walk"""
    for var, value in zip(PEOPLE_VARS, (frm, to, culture, religion, size)):
        fx.set_variable(name=var, value=value)
    fx.create_character(age=35, culture=culture, religion=religion, save_scope_as="tfe_people_leader")
    with fx.if_() as i:
        i.limit(lambda t: t.exists("scope:tfe_people_leader"))
        i.start_expedition(type=f"expedition_type:{EXPEDITION_TYPE}", leader="scope:tfe_people_leader")


def germanic_settlers(t: PopTrig):
    """a pop with people to spare: the king's own, or any Germanic one for a Germanic king (the Carpi and Iazyges send
    only for their own kin)"""
    t.pop_size(SOURCE_MIN, op=">=")
    with t.or_() as o:
        for pop_type in MOVERS:
            o.compare("pop_type", "=", f"pop_type:{pop_type}")
    with t.or_() as o:
        o.compare("culture", "=", "scope:actor.culture")
        with o.and_() as a:
            with a.go_culture() as c:
                c.tfe_is_germanic_culture(True)
            with a.link("scope:actor.culture", CultureTrig) as k:
                k.tfe_is_germanic_culture(True)


def gather(fx: PopFx):
    """this pop gives up to SETTLER_SHARE of itself, as much as the band still wants"""
    fx.save_scope_as("tfe_settler_giver")
    with fx.link(ACTOR, CountryFx) as c:
        c.set_variable(name="tfe_settlers_take", value="scope:tfe_settler_giver.pop_size")
        c.change_variable(name="tfe_settlers_take", multiply=SETTLER_SHARE)
        c.note("change_variable's max is max(), a floor: it let the first pop give 29")
        c.clamp_variable(name="tfe_settlers_take", max="var:tfe_settlers_wanted")
        c.change_variable(name="tfe_settlers_wanted", subtract="var:tfe_settlers_take")
    fx.add_pop_size(value="scope:actor.var:tfe_settlers_take", multiply=-1)


def invite_settlers(doc: Doc):
    doc.loc.add(ACTION, "Invite Settlers")
    doc.loc.add(SETTLERS_PRICE, "Inviting Settlers")
    doc.loc.add(f"{ACTION}_desc", "Our kin still live beyond the Rhine and the Danube, on poor land. Send for them: they will "
                "walk to the land we took and settle it as our own people.")
    doc.loc.add(f"{ACTION}_tt", f"Up to {SETTLER_SIZE * 1000:,} of our kin, peasants and tribesmen, leave Germania or "
                f"the Carpathians, at most {SETTLER_SHARE:.0%} of any one people, and walk to the chosen [location|e]. There "
                f"they settle as people of our [culture|e], {ARRIVE_AS[0][1]:.0%} peasants and {ARRIVE_AS[1][1]:.0%} "
                "tribesmen. If the land is no longer ours when they arrive, they settle by our [capital|e].")
    doc.loc.add(f"{ACTION}_cooldown_tt", f"We can invite settlers once every {SETTLERS_COOLDOWN} years.")
    doc.loc.add(f"{ACTION}_choose_location", "Choose the land to settle")
    doc.loc.add(f"{ACTION}_no_location", "@trigger_no! All our land is already settled by our own people.")
    doc.loc.add(f"{ACTION}_source_tt", f"Germania or the Carpathians still have {SOURCE_MIN * 1000:,} or more of our kin "
                "in one place to send")
    doc.loc.add("tfe_people_already_on_the_road_tt", "We have no people on the road already")
    doc.loc.add("tfe_invite_settlers", "Settlers Invited")
    doc.note("Invite Settlers: a Germanic (or Carpian, or Iazygian) king sends for his people in Germania to settle the land\n"
             "he took. They walk there (expedition_types/tfe_peoples.txt). Ends with the Migrations, in 500.")
    with doc.generic_action(ACTION) as a:
        a.note("a button in the Barbaricum's window: choose the Barbaricum, then the land to settle")
        a.field("type", "internationalorganization")
        a.field("icon", "migrate_pop_based_country")
        with a.triggers("potential") as t:
            t.note("a member of the Barbaricum: the button is in its window, and nobody else should send for kin")
            t.link(ACTOR, CountryTrig, lambda c: c.is_member_of_international_organization(
                "international_organization:tfe_barbaricum"))
            with t.link(ACTOR, CountryTrig) as c, c.go_culture() as cu, cu.or_() as o:
                o.tfe_is_germanic_culture(True)
                for culture in KIN_CULTURES:
                    o.compare("this", "=", f"culture:{culture}")
            with t.or_() as o:
                o.current_age("age_1_traditions")
                o.current_age("age_2_renaissance")
        with a.triggers("allow") as t:
            with t.link(ACTOR, CountryTrig) as c:
                with c.custom_tooltip_block("tfe_people_already_on_the_road_tt") as ct:
                    ct.not_(lambda n: n.has_variable("tfe_people_to"))
                c.note("decades of drain may empty Germania: then there is no one left to send. Inside scope:actor, or the\n"
                       "action's Conditions leave it out")
                with c.custom_tooltip_block(f"{ACTION}_source_tt") as ct, ct.or_() as o:
                    for region in SOURCE_REGIONS:
                        with o.link(f"region:{region}", RegionTrig) as r, r.any_location_in_region() as loc, loc.any_pop() as p:
                            germanic_settlers(p)
        a.field("ai_tick", "monthly")
        a.field("ai_tick_frequency", 12)
        a.field("automation_tick", "never")
        a.field("automation_tick_frequency", 12)
        a.data("cooldown", type="tfe_invite_settlers", years=SETTLERS_COOLDOWN)
        a.field("price", f"price:{SETTLERS_PRICE}")
        a.data("price_modifier", add={"desc": Q("tfe_one_years_income"),
                                      "value": "scope:actor.monthly_income_trade_and_tax",
                                      "multiply": SETTLERS_INCOME_MONTHS, "min": SETTLERS_MIN_GOLD})
        with a.block("select_trigger") as s:
            s.field("looking_for_a", "international_organization")
            s.field("target_flag", "recipient")
            s.field("name", Q("choose_international_organization"))
            s.data("column", data="name")
            with s.triggers("visible", InternationalOrganizationTrig) as t:
                t.compare("international_organization_type", "=", "international_organization_type:tfe_barbaricum")
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
            e.custom_tooltip(f"{ACTION}_tt")
            e.custom_tooltip(f"{ACTION}_cooldown_tt")
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
                with h.if_() as i:
                    i.limit(lambda t: t.exists("scope:tfe_settler_pop"))
                    i.note(f"they leave from the largest; up to {SETTLER_SIZE} pop_size gathers from every people of the\n"
                           "king's own culture first, then from the other Germanic peoples")
                    with i.link(ACTOR, CountryFx) as c:
                        c.set_variable(name="tfe_settlers_wanted", value=SETTLER_SIZE)
                    with i.if_() as g:
                        g.note("a tooltip's dry run sets no variable: read it only once it is there")
                        g.limit(lambda t: t.link(ACTOR, CountryTrig, lambda c: c.has_variable("tfe_settlers_wanted")))
                        for own in (True, False):
                            with g.every_in_list(PopFx, list="tfe_settler_pops") as p:
                                with p.limit() as t:
                                    t.compare("scope:actor.var:tfe_settlers_wanted", ">", 0)
                                    if own:
                                        t.compare("culture", "=", "scope:actor.culture")
                                    else:
                                        t.note("the king's own gave their share in the first pass")
                                        t.not_(lambda n: n.compare("culture", "=", "scope:actor.culture"))
                                gather(p)
                    with i.link("scope:tfe_settler_pop", PopFx) as p, p.go_location() as loc:
                        loc.save_scope_as("tfe_settler_home")
                    i.note("the settlers join the king's people (his culture), and keep their own gods")
                    with i.link(ACTOR, CountryFx) as c:
                        c.set_variable(name="tfe_settlers_gathered", value=SETTLER_SIZE)
                        c.change_variable(name="tfe_settlers_gathered", subtract="var:tfe_settlers_wanted")
                        send(c, frm="scope:tfe_settler_home", to="scope:target", culture="scope:actor.culture",
                             religion="scope:tfe_settler_pop.religion", size="var:tfe_settlers_gathered")
                        c.set_variable("tfe_people_invited")
                        for var in ("tfe_settlers_wanted", "tfe_settlers_take", "tfe_settlers_gathered"):
                            c.remove_variable(var)
        with a.effects("ai_will_do", ValueFx) as v:
            v.add(0)
            v.note("land to fill with our own people (the price is the engine's to check)")
            with v.if_() as i:
                with i.limit() as t:
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


def prices():
    """the settlers' price: one gold, which the action scales to a year of the king's income (dear for a rich king,
    within reach of a chieftain)"""
    d = Doc()
    d.note("TFE: peoples on the road. Written from script/peoples_on_the_road.py.")
    with d.entry(SETTLERS_PRICE) as e:
        e.field("gold", 1)
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
            "in_game/common/prices/tfe_peoples.txt": prices().text(),
            "main_menu/localization/english/tfe_peoples_l_english.yml": DOC.loc.text()}
