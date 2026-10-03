"""Honorius's West starts in trouble: unstable, its coin already debased, its claim on the purple still green."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx, CountryFx
from pdx.objects_defs import Defs

STABILITY = -25
INFLATION = 0.35   # a fraction, as vanilla's inflation_mild_penalty = 0.025 (script_values/default_values.txt)
LEGITIMACY = 55


def on_actions():
    d = Defs()
    d.note("TFE: the West opens at -25 stability, 35% inflation and 55 legitimacy: Stilicho's court holds a state\n"
           "already paying its armies in debased coin. Day one only WRE exists (Stilicho's West comes later).")
    d.hook("on_game_start", "tfe_on_start_western_state")
    with d.on_action("tfe_on_start_western_state") as a:
        with a.effect(AnyFx) as e, e.link("c:WRE", CountryFx, op="?=") as w:
            w.set_stability(STABILITY)
            w.set_inflation(INFLATION)
            w.set_legitimacy(LEGITIMACY)
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/on_action/tfe_western_start.txt": on_actions().text()}
