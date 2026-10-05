"""tfe_decline_rome generic actions: Rome's answers on the Decline of the West's panel, Hospitalitas and Man the Limes."""
import sys
from pathlib import Path
from contextlib import contextmanager
from typing import Callable, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx, AreaFx, AreaTrig, CountryFx, CountryTrig, LocationTrig, RegionFx, RegionTrig, SituationTrig, ValueFx
from pdx.core import Q, Scope
from pdx.objects import Doc, GenericAction

ACTOR = "scope:actor"
SITUATION = "situation:tfe_decline_of_the_west"
HEADER = """TFE: Rome's answers on the Decline of the West's panel (situations/tfe_decline_of_the_west.txt). An Augustus may settle a
migrating host on Roman land as foederati (Hospitalitas; the host may refuse, events/tfe_decline_rome.txt), or pay to
garrison a stretch of the frontier so that no people beyond it may take the road (scripted_triggers/tfe_decline_rome.txt)."""


def is_rome(t: CountryTrig):
    """either Augustus: any western Rome (Stilicho's West too) or the East."""
    with t.or_() as o:
        o.tfe_is_western_rome()
        o.tag("EAR")


def head(a: GenericAction):
    """the fields both buttons open with: shown while the Decline runs, to either Augustus."""
    a.field("type", "situation")
    with a.triggers("potential") as t:
        with t.go_situation("tfe_decline_of_the_west") as s:
            s.situation_is_active(True)
        with t.link(ACTOR, CountryTrig) as c:
            is_rome(c)


def ticks(a: GenericAction):
    a.field("ai_tick", "monthly")
    a.field("ai_tick_frequency", 6)
    a.field("automation_tick", "never")
    a.field("automation_tick_frequency", 12)


def choose_situation(a: GenericAction):
    with a.select_trigger("situation", SituationTrig, name="choose_situation", source=SITUATION) as t:
        t.compare(SITUATION, "=", "this")
        t.situation_is_active(True)


@contextmanager
def select[T: Scope](a: GenericAction, looking_for_a: str, visible: type[T], *, source: Callable[[AnyFx], object],
                     flag: str, name: str, none: str) -> Iterator[T]:
    """a select_trigger whose choices are gathered by an effect (source), with a message when there are none."""
    with a.block("select_trigger") as s:
        s.field("looking_for_a", looking_for_a)
        with s.effects("interaction_source_list") as i:
            source(i)
        s.field("target_flag", flag)
        s.field("name", Q(name))
        s.field("none_available_msg_key", Q(none))
        s.data("column", data="name")
        with s.triggers("visible", visible) as t:
            yield t


def migrating_hosts(i: AnyFx):
    with i.every_country() as c:
        with c.limit() as t:
            t.has_variable("tfe_migrating")
            t.not_(lambda n: n.has_variable("tfe_settled"))
        c.add_to_list("source")


def actor_areas(i: AnyFx):
    with i.link(ACTOR, CountryFx) as c, c.every_area_with_owned_province() as ar:
        ar.add_to_list("source")


def frontier_regions(i: AnyFx):
    with i.link(ACTOR, CountryFx) as c, c.every_owned_location() as loc:
        with loc.limit() as t:
            t.tfe_has_frontier_works()
        with loc.go_region() as r:
            r.add_to_list("source")


ISLAND_AREAS = ("aegean_archipelago_area", "balearics_area", "sardinia_area")   # Crete, Rhodes and the Aegean; the Balearics
ISLAND_PROVINCES = ("pumonte_province", "cismonte_province", "cyprus_province")   # Corsica and Cyprus share mainland areas
ISLAND_LOCATIONS = ("malta",)   # in Sicily's Noto province; Sicily itself and Britain stay fair


def island(t: LocationTrig):
    """user: exiling a host to a small island is cheese, it can never again march without ships and dies landing"""
    with t.or_() as o:
        for a in ISLAND_AREAS:
            o.compare("area", "=", f"area:{a}")
        for p in ISLAND_PROVINCES:
            o.compare("province_definition", "=", f"province_definition:{p}")
        for loc in ISLAND_LOCATIONS:
            o.compare("this", "=", f"location:{loc}")


def offered(t: LocationTrig):
    """a location of the area Hospitalitas would hand over: the actor's, and no small island"""
    t.compare("owner", "?=", ACTOR)
    t.not_(island)


def hospitalitas(doc: Doc):
    doc.note("Hospitalitas: an area of the Empire for a host on the road, as Rome settled the Visigoths in Aquitaine in 418")
    with doc.generic_action("tfe_hospitalitas") as a:
        head(a)
        with a.triggers("allow") as t, t.link(ACTOR, CountryTrig) as c:
            c.is_subject(False)
        ticks(a)
        a.note("the land itself is the price; the cooldown paces the giving")
        a.data("cooldown", type="tfe_hospitalitas", years=5)
        choose_situation(a)
        a.note("the host: on the road, not yet settled, free and with no offer already before it, and not at war with the other\n"
               "Rome (the East may not buy off a host that marches on the West, nor the West one that marches on the East)")
        with select(a, "country", CountryTrig, source=migrating_hosts, flag="host",
                    name="tfe_hospitalitas_choose_host", none="tfe_hospitalitas_no_host") as t:
            t.has_variable("tfe_migrating")
            t.not_(lambda n: n.has_variable("tfe_settled"))
            t.is_subject(False)
            t.not_(lambda n: n.has_variable("tfe_hospitalitas_from"))
            with t.not_() as n, n.any_country() as r:
                is_rome(r)
                r.not_(lambda x: x.compare("this", "=", ACTOR))
                r.is_at_war_with("prev")
        a.note("the land: a whole area where the actor holds provinces (a single province is too little to buy off a people),\n"
               "never the one that holds the capital. The East gives only Illyricum, Thrace and Greece (the Balkans), never Anatolia,\n"
               "Syria or Egypt: the peoples come over the Danube, and the East's heartlands are not for them. No small island:\n"
               "an island area is never offered, and a mixed one hands over only its mainland (Sicily and Britain are fair)")
        with select(a, "area", AreaTrig, source=actor_areas, flag="target_area",
                    name="tfe_hospitalitas_choose_area", none="tfe_hospitalitas_no_area") as t:
            with t.any_location_in_area() as loc:
                offered(loc)
            with t.not_() as n, n.any_location_in_area() as loc:
                loc.compare("owner", "?=", ACTOR)
                loc.is_capital(True)
            with t.or_() as o:
                with o.link(ACTOR, CountryTrig) as c:
                    c.not_(lambda n: n.tag("EAR"))
                o.compare("region", "=", "region:balkan_region")
        with a.effects("effect") as e:
            e.custom_tooltip("tfe_hospitalitas_tt")
            with e.hidden_effect() as h:
                h.note("what the host's event needs travels as variables on the host (a saved scope does not reach it)")
                with h.link("scope:host", CountryFx) as host:
                    host.set_variable(name="tfe_hospitalitas_from", value=ACTOR, months=3)
                    host.set_variable(name="tfe_hospitalitas_area", value="scope:target_area", months=3)
                    host.tail("named in the event")
                with h.link("scope:target_area", AreaFx) as ar, ar.every_location_in_area() as loc:
                    with loc.limit() as t:
                        offered(t)
                    with loc.link("scope:host", CountryFx) as host:
                        host.add_to_variable_list(name="tfe_hospitalitas_land", target="prev", months=3)
                with h.link("scope:host", CountryFx) as host:
                    host.trigger_event_non_silently(id="tfe_decline_rome.1")
        with a.effects("ai_will_do", ValueFx) as v:
            v.add(0)
            v.note("a host at our gates, and the war going badly: settle it before it settles itself")
            with v.if_() as i:
                with i.limit() as t, t.link("scope:host", CountryTrig) as host:
                    host.is_at_war_with(ACTOR)
                i.add(30)
            with v.if_() as i:
                with i.limit() as t:
                    with t.link("scope:host", CountryTrig) as host:
                        host.is_at_war_with(ACTOR)
                    with t.link(ACTOR, CountryTrig) as c:
                        c.is_in_losing_war(True)
                i.add(40)
            v.note("give what Rome barely holds (the frontier, the deserted fields), never an area it truly rules")
            with v.if_() as i:
                with i.limit() as t, t.link("scope:target_area", AreaTrig) as ar:
                    ar.compare("\"area_average_control(scope:actor)\"", "<", 0.3)  # 1.4: control is per country
                i.add(20)
            with v.else_if() as i:
                with i.limit() as t, t.link("scope:target_area", AreaTrig) as ar:
                    ar.compare("\"area_average_control(scope:actor)\"", ">", 0.6)
                i.add(-100)
            v.note("the land the host's people truly took (scripted_triggers/tfe_historical_lands.txt): it is likelier to accept")
            with v.if_() as i:
                with i.limit() as t, t.link("scope:target_area", AreaTrig) as ar:
                    ar.tfe_is_historical_land_of(WHO="scope:host")
                i.add(40)


def man_the_limes(doc: Doc):
    doc.note("Man the Limes: gold and men to garrison one stretch of the frontier for a year")
    with doc.generic_action("tfe_man_the_limes") as a:
        head(a)
        with a.triggers("allow") as t, t.link(ACTOR, CountryTrig) as c, c.any_owned_location() as loc:
            loc.tfe_has_frontier_works()
        a.field("price", "price:tfe_man_the_limes_price")
        a.data("price_modifier", add={"desc": Q("tfe_man_the_limes_cost"), "value": 100})
        ticks(a)
        a.data("cooldown", type="tfe_man_the_limes", years=1)
        choose_situation(a)
        a.note("a whole diocese (region) at a time: one fort was too little to matter")
        with select(a, "region", RegionTrig, source=frontier_regions, flag="limes_region",
                    name="tfe_man_the_limes_choose_region", none="tfe_man_the_limes_no_region") as t:
            with t.any_location_in_region() as loc:
                loc.compare("owner", "?=", ACTOR)
                loc.tfe_has_frontier_works()
                loc.not_(lambda n: n.has_location_modifier("tfe_limes_manned"))
        with a.effects("effect") as e:
            e.custom_tooltip("tfe_man_the_limes_tt")
            with e.hidden_effect() as h, h.link("scope:limes_region", RegionFx) as r, r.every_location_in_region() as loc:
                with loc.limit() as t:
                    t.compare("owner", "?=", ACTOR)
                    t.tfe_has_frontier_works()
                loc.add_location_modifier(modifier="tfe_limes_manned", years=1, mode="replace")
        with a.effects("ai_will_do", ValueFx) as v:
            v.add(0)
            v.note("a people still at home across that stretch of the frontier, and gold to spare")
            with v.if_() as i:
                with i.limit() as t:
                    with t.link(ACTOR, CountryTrig) as c:
                        c.gold(150, op=">=")
                    with t.link("scope:limes_region", RegionTrig) as r, r.any_location_in_region() as loc:
                        loc.compare("owner", "?=", ACTOR)
                        loc.tfe_has_frontier_works()
                        with loc.any_neighbor_location() as nb, nb.go_owner(op="?=") as o:
                            o.tfe_is_migrator()
                            o.not_(lambda n: n.has_variable("tfe_migrating"))
                i.add(30)


def build():
    doc = Doc()
    doc.note(HEADER)
    hospitalitas(doc)
    man_the_limes(doc)
    return doc


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/generic_actions/tfe_decline_rome.txt": build().text()}
