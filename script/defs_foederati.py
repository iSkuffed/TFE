"""Foederati: a foedus dies with either of its rulers, so every foedus opens lapsed and lapses again at each death."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryFx
from pdx.objects_defs import Defs

LAPSE = "tfe_foederati.1"


def on_actions():
    d = Defs()
    d.note("TFE: a foedus (subject_types/tfe_foederati.txt) is sworn between two rulers and dies with either of them.\n"
           "Theodosius died on 17 January 395, the day before the game starts: every foedus opens already lapsed.")
    d.hook("on_game_start", "tfe_on_start_theodosius_dead")
    with d.on_action("tfe_on_start_theodosius_dead") as a:
        with a.effect(CountryFx) as e:
            with e.every_country() as c:
                with c.limit() as t:
                    t.is_subject_type("tfe_foederati")
                c.set_variable("tfe_sworn_to_theodosius")
                c.tail("read by the event's AI weights, cleared by its options")
                c.trigger_event_non_silently(LAPSE)
    d.hook("on_ruler_death", "tfe_on_ruler_death_foedus_lapses")
    with d.on_action("tfe_on_ruler_death_foedus_lapses") as a:
        with a.effect(CountryFx) as e:
            with e.if_() as i:
                with i.limit() as t:
                    t.is_subject_type("tfe_foederati")
                i.trigger_event_non_silently(LAPSE)
            with e.every_subject() as s:
                with s.limit() as t:
                    t.is_subject_type("tfe_foederati")
                s.trigger_event_non_silently(LAPSE)
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/on_action/tfe_foederati.txt": on_actions().text()}
