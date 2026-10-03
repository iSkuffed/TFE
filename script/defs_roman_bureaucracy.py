"""The Roman empires start already staffed: the three offices (bureaucracies/tfe_roman.txt) are held, and old."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx
from pdx.objects_defs import Defs

OFFICES = ["tfe_sacrae_largitiones_bureaucracy", "tfe_magister_officiorum_bureaucracy", "tfe_magister_peditum_bureaucracy"]
ENTRENCHMENT = 60   # the offices are older than the bookmark; vanilla's six_boards starts at 60 (situation_effects.txt)
MAINTENANCE = 0.5   # and at the same funding


def on_actions():
    d = Defs()
    d.note("TFE: the Roman state was staffed long before 395, so both empires start with their three offices, entrenched\n"
           "and half funded, as vanilla's situation_effects.txt starts a Chinese dynasty's six boards. add_bureaucracy ignores the slot limit.")
    d.hook("on_game_start", "tfe_on_start_roman_bureaucracy")
    with d.on_action("tfe_on_start_roman_bureaucracy") as a:
        with a.effect(AnyFx) as e, e.every_country() as c:
            with c.limit() as t, t.or_() as o:
                o.tfe_is_western_rome(True)
                o.has_or_had_tag("EAR")
            for office in OFFICES:
                c.add_bureaucracy(f"bureaucracy_type:{office}")
            with c.every_current_bureaucracy() as b:
                b.set_entrenchment(ENTRENCHMENT)
                b.set_maintenance(MAINTENANCE)
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/on_action/tfe_roman_bureaucracy.txt": on_actions().text()}
