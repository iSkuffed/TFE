"""Africa's granaries start fully worked: the scripted effect that works one, and the on_action that lists them."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx, LocationFx
from pdx.objects_defs import Defs

# location -> the Roman name, where the file gives one
GRANARIES = {"tunis": "Carthage", "mateur": "", "tebourba": "", "medjez_el_bab": "", "beja_TUN": "Vaga",
             "el_kef": "Sicca Veneria", "el_fahs": "Thuburbo Maius", "tebessa": "Theveste", "sbiba": "",
             "kairouan": "", "gabes": "Tacapae"}


def effects():
    d = Defs()
    d.note("TFE: a granary of Rome (on_action/tfe_lands.txt) starts with its RGO worked to the limit. Its wheat and its\n"
           "Granary of Rome modifier come from its template (tools/location_templates.py).")
    with d.effect("tfe_work_granary_to_the_limit", LocationFx) as e:
        with e.while_() as w:
            with w.limit() as t:
                t.is_full_expanded_rgo(False)
            w.change_max_raw_material_workers(1)
    return d


def on_actions():
    d = Defs()
    d.note("TFE: Africa's granaries start fully worked (scripted_effects/tfe_lands.txt). The lands' modifiers themselves are\n"
           "template modifiers (tools/location_templates.py), so they show on the map; this list is its GRANARIES.")
    d.hook("on_game_start", "tfe_on_start_lands")
    with d.on_action("tfe_on_start_lands") as a:
        with a.effect(AnyFx) as e:
            for loc, name in GRANARIES.items():
                with e.link(f"location:{loc}", LocationFx) as l:
                    l.tfe_work_granary_to_the_limit(True)
                if name:
                    e.tail(name)
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/scripted_effects/tfe_lands.txt": effects().text(),
            "in_game/common/on_action/tfe_lands.txt": on_actions().text()}
