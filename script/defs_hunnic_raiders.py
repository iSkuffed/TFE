"""The Huns raid for captives from day one: the start modifiers and the on_action that drives peasants off as slaves."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryFx, CountryTrig, LocationFx, LocationTrig
from pdx.objects_defs import Defs


def on_actions():
    d = Defs()
    d.note("TFE: the Huns raid for captives from day one (static_modifiers/tfe_hunnic_raiders.txt). Vanilla's own slave raid\n"
           "sends captives only to a slave market near the front, and the Huns' one market is at Kaffa, so they also drive\n"
           "off a share of the peasants and labourers of every land they take to their capital, as slaves.")
    d.hook("on_game_start", "tfe_on_start_hunnic_raiders")
    with d.on_action("tfe_on_start_hunnic_raiders") as a:
        with a.effect(CountryFx) as e:
            for modifier in ("tfe_hunnic_raiders", "tfe_hunnic_horde"):
                with e.link("c:HNS", CountryFx, op="?=") as c:
                    c.add_country_modifier(modifier=modifier)
    d.hook("on_location_occupied", "tfe_on_hunnic_raid")
    d.hook("on_siege_won", "tfe_on_hunnic_raid")
    with d.on_action("tfe_on_hunnic_raid") as a:
        with a.trigger(CountryTrig) as t:
            t.has_country_modifier("tfe_hunnic_raiders")
            t.exists("root.capital")
            with t.link("scope:target", LocationTrig) as loc:
                loc.exists("owner")
                with loc.not_() as n:
                    n.compare("owner", "=", "root")
        with a.effect(CountryFx) as e:
            with e.link("scope:target", LocationFx) as loc:
                with loc.every_pop() as p:
                    with p.limit() as t:
                        with t.or_() as o:
                            o.compare("pop_type", "=", "pop_type:peasants")  # an event target, not a documented trigger
                            o.compare("pop_type", "=", "pop_type:laborers")
                    p.split_pop(fraction=0.15, type="pop_type:slaves", location="root.capital")
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/on_action/tfe_hunnic_raiders.txt": on_actions().text()}
