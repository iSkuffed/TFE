"""The Decline of the West: who may take the road, and the on_action that starts the situation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx, CountryTrig
from pdx.objects_defs import Defs

# the peoples of Germania and Dacia, in the file's order
MIGRATORS = "ALM BGD FRK HAS SLX SAX MKM QAD LGB SLF FRS AGL TGI RUG SCR VIS GEP CRP IAZ".split()


def triggers():
    d = Defs()
    d.note("TFE: the Decline of the West (situations/tfe_decline_of_the_west.txt).")
    d.note("Scope: a country. The peoples of Germania and Dacia who may take the road into the Empire\n"
           "(generic_actions/tfe_migratory.txt's Start Migration, on the Decline's panel).")
    with d.trigger("tfe_is_migrator", CountryTrig) as t:
        with t.or_() as o:
            for tag in MIGRATORS:
                o.tag(tag)
    return d


def on_actions():
    d = Defs()
    d.note("TFE: the Decline of the West (situations/tfe_decline_of_the_west.txt) begins on day one.")
    d.hook("on_game_start", "tfe_on_start_decline_of_the_west")
    with d.on_action("tfe_on_start_decline_of_the_west") as a:
        with a.effect(AnyFx) as e:
            with e.if_() as i:
                with i.limit() as t:
                    t.country_exists("c:WRE")
                i.activate_situation("situation:tfe_decline_of_the_west")
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/scripted_triggers/tfe_decline_of_the_west.txt": triggers().text(),
            "in_game/common/on_action/tfe_decline_of_the_west.txt": on_actions().text()}
