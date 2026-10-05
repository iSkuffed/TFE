"""Salvian's Romans who "flee to the barbarians": a migrating host that takes a Roman town is joined by some of its men."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryFx, CountryTrig, LocationFx, LocationTrig
from pdx.objects_defs import Defs


def host_on_the_road(t: CountryTrig):
    """a migrating host not yet settled, or the Franks raiding over the Rhine"""
    with t.or_() as o:
        with o.and_() as m:
            m.has_variable("tfe_migrating")
            m.not_(lambda n: n.has_variable("tfe_settled"))
            m.tail("on_action/tfe_migratory.txt")
        o.has_variable("tfe_rhine_war")
        o.tail("the Franks' raid over the Rhine (decisions/tfe_barbarian_kingdoms.txt)")


def roman_town(loc: LocationTrig):
    """a Roman town that has not given the host men in the last ten years"""
    with loc.not_() as n:
        n.has_location_modifier("tfe_fled_to_the_host")
    with loc.go_owner(op="?=") as owner:
        with owner.or_() as o:
            o.tfe_is_western_rome()
            o.has_or_had_tag("EAR")


def men_join(loc: LocationFx):
    """the town's men leave the empire for the host (root): every regiment of the host regains strength"""
    loc.add_location_modifier(modifier="tfe_fled_to_the_host", years=10)
    with loc.go_owner() as owner:
        owner.save_scope_value_as(name="tfe_defectors", value="tfe_defectors_share")
        owner.add_manpower("tfe_defectors_manpower")
    with loc.link("root", CountryFx) as host, host.every_army() as army, army.every_sub_unit() as u:
        u.add_subunit_strength_percentage("scope:tfe_defectors")


def on_actions():
    d = Defs()
    d.note("TFE: Salvian's Romans who \"flee to the barbarians\". When a migrating host (decisions/tfe_fall_of_the_west.txt)\n"
           "or the Franks raiding over the Rhine take a Roman town, some of its men join them: every regiment of the host\n"
           "regains strength, and the empire loses them. The West's burdens (government_reforms/tfe_late_roman_west.txt)\n"
           "drive more to go. A town gives men once a decade.")
    d.hook("on_siege_won", "tfe_on_host_takes_roman_town")
    d.hook("on_location_occupied", "tfe_on_host_takes_roman_town")
    d.note("root = the occupier, scope:target = the location")
    with d.on_action("tfe_on_host_takes_roman_town") as a:
        with a.trigger(CountryTrig) as t:
            host_on_the_road(t)
            with t.link("scope:target", LocationTrig) as loc:
                roman_town(loc)
        with a.effect(CountryFx) as e, e.link("scope:target", LocationFx) as loc:
            men_join(loc)
    d.note("The rest of a province falls to whoever holds its provincial capital, a little after, and neither hook above\n"
           "fires for it. Each month the host also gathers the men of every Roman town it holds that has not yet given any.")
    d.hook("monthly_country_pulse", "tfe_on_host_holds_roman_towns")
    with d.on_action("tfe_on_host_holds_roman_towns") as a:
        with a.trigger(CountryTrig) as t:
            host_on_the_road(t)
        with a.effect(CountryFx) as e, e.every_controlled_location() as loc:
            with loc.limit() as t:
                roman_town(t)
            men_join(loc)
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/on_action/tfe_defectors.txt": on_actions().text()}
