"""Every country starts able to tax: Taxation and the advances it requires are researched on day one."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx
from pdx.objects_defs import Defs

# vanilla in_game/common/advances/0_age_of_traditions.txt, in the order each requires the one before
ADVANCES = ["written_alphabet", "codified_laws", "taxation_advance"]


def on_actions():
    d = Defs()
    d.note("TFE: in 395 every people from Rome to the steppe raises some tribute. Without Taxation a country has no taxes\n"
           "and no stability investment, so every country starts with it and the advances it requires.")
    d.hook("on_game_start", "tfe_on_start_taxation")
    with d.on_action("tfe_on_start_taxation") as a:
        with a.effect(AnyFx) as e, e.every_country() as c:
            for adv in ADVANCES:
                with c.if_() as i:
                    with i.limit() as t, t.not_() as n:
                        n.has_advance(adv)  # bare key, as vanilla situation_effects.txt
                    i.research_advance(f"advance_type:{adv}")
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/on_action/tfe_start_advances.txt": on_actions().text()}
