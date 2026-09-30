"""Salvian's Romans who "flee to the barbarians": a migrating host that takes a Roman town is joined by some of its men."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryFx, CountryTrig, LocationFx, LocationTrig
from pdx.objects_defs import Defs


def on_actions():
    d = Defs()
    d.note("TFE: Salvian's Romans who \"flee to the barbarians\". When a migrating host (generic_actions/tfe_migratory.txt) takes a\n"
           "Roman town, some of its men join it: every regiment of the host regains strength, and the empire loses them. The\n"
           "West's burdens (government_reforms/tfe_late_roman_west.txt) drive more to go. A town gives men once a decade.")
    d.hook("on_siege_won", "tfe_on_host_takes_roman_town")
    d.hook("on_location_occupied", "tfe_on_host_takes_roman_town")
    d.note("root = the occupier, scope:target = the location")
    with d.on_action("tfe_on_host_takes_roman_town") as a:
        with a.trigger(CountryTrig) as t:
            t.has_variable("tfe_migrating")
            with t.not_() as n:
                n.has_variable("tfe_settled")
            t.tail("on_action/tfe_migratory.txt")
            with t.link("scope:target", LocationTrig) as loc:
                with loc.not_() as n:
                    n.has_location_modifier("tfe_fled_to_the_host")
                with loc.go_owner(op="?=") as owner:
                    with owner.or_() as o:
                        o.has_or_had_tag("WRE")
                        o.has_or_had_tag("EAR")
        with a.effect(CountryFx) as e:
            with e.link("scope:target", LocationFx) as loc:
                loc.add_location_modifier(modifier="tfe_fled_to_the_host", years=10)
                with loc.go_owner() as owner:
                    owner.save_scope_value_as(name="tfe_defectors", value="tfe_defectors_share")
                    owner.add_manpower("tfe_defectors_manpower")
            with e.every_army() as army:
                with army.every_sub_unit() as u:
                    u.add_subunit_strength_percentage("scope:tfe_defectors")
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/on_action/tfe_defectors.txt": on_actions().text()}
