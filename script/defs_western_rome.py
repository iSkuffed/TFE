"""Which countries are the Western Roman Empire: Honorius's WRE, and Stilicho's West once he rises (RoadMap #27)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryTrig
from pdx.objects_defs import Defs


def triggers():
    d = Defs()
    d.note("honorius-only: this file says which West is which (tools/test_western_rome.py)")
    d.note("TFE: Stilicho's Glory (events/tfe_stilicho.txt). Scope: a country. The West is Honorius's WRE and, once Stilicho\n"
           "rises, Stilicho's West (tfe_western_rome, set by tfe_stilicho.3). The barbarians march on both, and Rome's answers\n"
           "to them (Hospitalitas, Man the Limes) belong to both. The Imperium Romanum's seat stays with WRE.")
    with d.trigger("tfe_is_western_rome", CountryTrig) as t, t.or_() as o:
        o.tag("WRE")
        o.has_variable("tfe_western_rome")
    d.note("Either Roman empire, as the Roman offices and the fisc see it: the West (by its tag or its variable) or the East.\n"
           "has_or_had_tag keeps a renamed empire Roman.")
    with d.trigger("tfe_is_roman_empire", CountryTrig) as t, t.or_() as o:
        o.has_or_had_tag("WRE")
        o.has_variable("tfe_western_rome")
        o.has_or_had_tag("EAR")
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/scripted_triggers/tfe_western_rome.txt": triggers().text()}
