"""The Roman empires start able to recruit their Comitatenses and Limitanei (unit_types/tfe_roman_units.txt)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx
from pdx.objects_defs import Defs

# advances/tfe_roman_units.txt, one per unit
ADVANCES = ["tfe_unlock_comitatenses_advance", "tfe_unlock_limitanei_advance"]


def on_actions():
    d = Defs()
    d.note("TFE: the empires' Footmen and Archers are their Comitatenses and Limitanei. Vanilla's are barred to them, so\n"
           "both start with the advances that unlock their own.")
    d.hook("on_game_start", "tfe_on_start_roman_units")
    with d.on_action("tfe_on_start_roman_units") as a:
        with a.effect(AnyFx) as e, e.every_country() as c:
            with c.limit() as t, t.or_() as o:
                o.tfe_is_western_rome(True)
                o.has_or_had_tag("EAR")
            for adv in ADVANCES:
                with c.if_() as i:
                    with i.limit() as t, t.not_() as n:
                        n.has_advance(adv)
                    i.research_advance(f"advance_type:{adv}")
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/on_action/tfe_roman_units.txt": on_actions().text()}
