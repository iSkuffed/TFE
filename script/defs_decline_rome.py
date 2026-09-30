"""Rome's answers to the migrations: two scripted triggers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryTrig, LocationTrig
from pdx.objects_defs import Defs


def build():
    d = Defs()
    d.note("TFE: Rome's answers to the migrations (generic_actions/tfe_decline_rome.txt)")
    d.note("A location (scope: location) that holds the frontier works placed at start (building_types/tfe_frontier.txt)")
    with d.trigger("tfe_has_frontier_works", LocationTrig) as t:
        with t.any_buildings_in_location() as b:
            with b.or_() as o:
                o.compare("building_type", "=", "building_type:tfe_limes")  # an event target, not a documented trigger
                o.compare("building_type", "=", "building_type:tfe_hadrians_wall")
    d.note("A country (scope: country) with no land beside a stretch of frontier that an Augustus has manned (Man the Limes).\n"
           "True when the way is open, so the Migrate buttons' requirement reads right with either mark: a custom_tooltip shows\n"
           "its text as written, and \"= no\" on a barred-trigger showed \"A Roman garrison mans the frontier\" ticked green.")
    with d.trigger("tfe_frontier_unmanned", CountryTrig) as t:
        with t.custom_tooltip_block("tfe_frontier_unmanned_tt") as c:
            with c.not_() as n:
                with n.any_owned_location() as loc:
                    with loc.any_neighbor_location() as nb:
                        nb.has_location_modifier("tfe_limes_manned")
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/scripted_triggers/tfe_decline_rome.txt": build().text()}
