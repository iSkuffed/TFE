"""Honorius's West starts in trouble: unstable, its coin already debased, its claim on the purple still green."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx, CountryFx, LocationFx
from pdx.objects_defs import Defs

STABILITY = -25
INFLATION = 0.35   # a fraction, as vanilla's inflation_mild_penalty = 0.025 (script_values/default_values.txt)
LEGITIMACY = 55
# A tenth of the empire was enslaved in the fourth century (Harper, Slavery in the Late Roman World, 2011), more in Italy.
# A slave of a culture the West accepts is freed (vanilla's Liberate Slaves treaty frees exactly those), and the start
# turns setup slaves into laborers and soldiers, so the West's slaves are cut from its peasants on day one as captives
# from beyond the frontier. The share is of the peasants, about three quarters of the West's people.
SLAVES = (("italy_region", "gothic_culture", 0.2),        # Goths sold off by the thousand after 376
          ("france_region", "alamannic", 0.14),          # captives of the Rhine wars
          ("great_britain_region", "irish", 0.14),       # taken in the Scotti's raids, and taken back
          ("maghreb_region", "kabyle", 0.14),            # Mauri
          ("balkan_region", "iazyges", 0.14))            # Sarmatians of the Tisza
SLAVES_ELSEWHERE = ("gothic_culture", 0.14)


def enslave(loc: LocationFx, culture, share):
    with loc.every_pop() as p:
        with p.limit() as t:
            t.compare("pop_type", "=", "pop_type:peasants")
        p.split_pop(fraction=share, type="pop_type:slaves", culture=f"culture:{culture}")


def on_actions():
    d = Defs()
    d.note("honorius-only: day one: the 395 opening state of Honorius's West (tools/test_western_rome.py)")
    d.note("TFE: the West opens at -25 stability, 35% inflation and 55 legitimacy: Stilicho's court holds a state\n"
           "already paying its armies in debased coin. Day one only WRE exists (Stilicho's West comes later).")
    d.hook("on_game_start", "tfe_on_start_western_state")
    with d.on_action("tfe_on_start_western_state") as a:
        with a.effect(AnyFx) as e, e.link("c:WRE", CountryFx, op="?=") as w:
            w.set_stability(STABILITY)
            w.set_inflation(INFLATION)
            w.set_legitimacy(LEGITIMACY)
            with w.every_owned_location() as loc:
                first = True
                for region, culture, share in SLAVES:
                    with (loc.if_() if first else loc.else_if()) as i:
                        with i.limit() as t:
                            t.compare("region", "=", f"region:{region}")
                        enslave(i, culture, share)
                    first = False
                with loc.else_() as i:
                    enslave(i, *SLAVES_ELSEWHERE)
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/on_action/tfe_western_start.txt": on_actions().text()}
