"""tfe_walls and tfe_arcadius events: the great land walls offered early, and Arcadius's stats rolled at the start."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pdx.api import CharacterFx, CountryFx, CountryTrig, LocationFx, LocationTrig
from pdx.core import Q
from pdx.objects import Doc

EXT = "gfx/interface/illustrations/event/backgrounds/exterior/"

WALLS_FEE = 150  # gold; the event pays for the whole build, so construction itself costs nothing more

# Arcadius's base is 45/45/25 (05_characters.txt). History: pious, slight, led by his ministers, never took the field.
# Each stat moves from that base by one of five steps, weighted to the middle; the result lands at adm 30-50,
# dip 30-50, mil 10-30.
ARCADIUS_STEPS = ((15, -15), (20, -10), (30, -5), (20, 0), (15, 5))


def walls_doc():
    doc = Doc()
    doc.namespace("tfe_walls")
    doc.note("1 Jan 405 (on_action/tfe_opening.txt): the great land walls are offered to Constantinople's owner, eight years\n"
             "before the historical date. in_game/common/building_types/tfe_theodosian_walls.txt keeps them out of the\n"
             "buildings tab until then. Accepting pays a fixed fee and starts construction at no further cost; refusing leaves the tab's price.")
    with doc.event(1, type="country_event", title="A Wall Across the Peninsula", outcome="positive",
                   desc="Constantine's wall, raised seventy years ago, now stands inside the city: the suburbs, the harbours and "
                        "the granaries have all spilled past it into open fields. Gothic bands raid Thrace within sight of the gates, "
                        "and the Huns are on the Danube. The Emperor's ministers have a plan: a single great line of wall "
                        "from the Propontis to the Golden Horn, with a moat, an outer wall, and behind it a high inner wall "
                        "with towers every hundred feet. If it stands, no army will take the city from the land.\n\n"
                        "The stone would come from the quarries of Proconnesus and the labour from every guild in the city, "
                        "who would be taxed for their own safety. The ministers can begin this spring and have the work done "
                        "for a fixed 150 gold, far less than the treasury would pay if it waited and commissioned it later. Or the old "
                        "wall may hold for a few more years, and the Theodosian Walls can still be raised later, at full price.",
                   image=EXT + "byz_burghers_exterior.dds") as e:
        with e.trigger() as t:
            t.owns("location:constantinople")
            with t.link("location:constantinople", LocationTrig) as c, c.not_() as n:
                n.has_building("building_type:theodosian_walls")
        e.note("a fixed fee, then the walls start building with no further cost")
        with e.option("a", text="Raise the walls") as o:
            with o.trigger() as t:
                t.gold(WALLS_FEE, op=">=")
            o.add_gold(-WALLS_FEE)
            with o.link("location:constantinople", LocationFx) as c:
                c.construct_building(building_type="building_type:theodosian_walls", cost_multiplier=0,
                                     cost_multiplier_reason=Q("The wall levy"))
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
            for add in (CharacterFx.add_adm, CharacterFx.add_dip, CharacterFx.add_mil):
                with a.random_list() as r:
                    for weight, delta in ARCADIUS_STEPS:
                        with r.weight(weight) as w:
                            add(w, delta)
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
