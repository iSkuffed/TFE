"""tfe_walls and tfe_arcadius events: Anthemius's walls offered early, and Arcadius's stats rolled at the start."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pdx.api import CharacterFx, CountryFx, CountryTrig, LocationFx, LocationTrig
from pdx.core import Q
from pdx.objects import Doc

EXT = "gfx/interface/illustrations/event/backgrounds/exterior/"

WALLS_COST = 0.67  # share of the tab's price the event charges: a third off

# Arcadius's base is 45/45/25 (05_characters.txt). History: pious, slight, led by his ministers, never took the field.
# Each stat moves from that base by one of five steps, weighted to the middle; the result lands at adm 30-50,
# dip 30-50, mil 10-30.
ARCADIUS_STEPS = ((15, -15), (20, -10), (30, -5), (20, 0), (15, 5))


def walls_doc():
    doc = Doc()
    doc.namespace("tfe_walls")
    doc.note("1 Jan 405 (on_action/tfe_opening.txt): Anthemius's land walls are offered to Constantinople's owner, eight years\n"
             "before the historical date. in_game/common/building_types/tfe_theodosian_walls.txt keeps them out of the\n"
             "buildings tab until then. Accepting starts construction at a third off the tab's price; refusing leaves the tab's price.")
    with doc.event(1, type="country_event", title="Anthemius Measures the Plain", outcome="positive",
                   desc="The praetorian prefect Anthemius has walked the ground west of the city with a rope and a surveyor. "
                        "The old wall of Constantine is a day's walk too close to the harbours, and every year the suburbs "
                        "spill further past it. He proposes a new line across the whole peninsula: a moat, an outer wall, "
                        "and behind it a great wall with towers every hundred feet.\n\n"
                        "The stone would come from the quarries of Proconnesus, and the work from every guild and every "
                        "landowner in the city, who would be taxed for their own safety. He offers to begin this spring, "
                        "and to do it for a third less than the treasury would pay if it waited and commissioned the work itself.",
                   image=EXT + "byz_burghers_exterior.dds") as e:
        with e.trigger() as t:
            t.owns("location:constantinople")
            with t.link("location:constantinople", LocationTrig) as c, c.not_() as n:
                n.has_building("building_type:theodosian_walls")
        e.note("start the walls now at a third off the tab's price")
        with e.option("a", text="Raise the walls (a third cheaper than later)") as o:
            with o.link("location:constantinople", LocationFx) as c:
                c.construct_building(building_type="building_type:theodosian_walls", cost_multiplier=WALLS_COST,
                                     cost_multiplier_reason=Q("Anthemius's levy"))
            o.add_prestige(10)
            o.ai_chance(3)
        e.note("they stay in the buildings tab at full price")
        with e.option("b", text="The old wall has held so far") as o:
            o.ai_chance(1)
    return doc


def arcadius_doc():
    doc = Doc()
    doc.namespace("tfe_arcadius")
    doc.note("Arcadius's stats are rolled when the game starts (on_action/tfe_opening.txt), so no two games have the same\n"
             "emperor, though each is the pious, guided ruler of history.")
    with doc.event(1, type="country_event", title="Arcadius's Measure", desc="Hidden roll of the emperor's stats.",
                   outcome="neutral", hidden=True) as e:
        with e.immediate() as i, i.link("character:tfe_arcadius", CharacterFx) as a:
            for stat in ("adm", "dip", "mil"):
                with a.random_list() as r:
                    for weight, delta in ARCADIUS_STEPS:
                        with r.weight(weight) as w:
                            getattr(w, f"add_{stat}")(delta)
    return doc


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    walls = walls_doc()
    arcadius = arcadius_doc()
    return {"in_game/events/tfe_walls.txt": walls.text(),
            "main_menu/localization/english/tfe_walls_l_english.yml": walls.loc.text(),
            "in_game/events/tfe_arcadius.txt": arcadius.text(),
            "main_menu/localization/english/tfe_arcadius_l_english.yml": arcadius.loc.text()}


if __name__ == "__main__":
    for rel, text in outputs().items():
        (ROOT / rel).write_text(text, encoding="utf-8-sig", newline="\n")
