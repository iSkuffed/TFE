"""The offices of the late Roman state: the Sacrae Largitiones (tax), the Magister Officiorum (court) and the Magister
Peditum (army), with the slots to hold all three. Writes the bureaucracies, their impact modifiers' types and icons, the
slot grant and the localisation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryTrig
from pdx.objects import Doc


def roman(t: CountryTrig):
    """the two Roman empires (and Stilicho's West); vanilla's Byzantine set is behind Fate of the Phoenix and BYZ/TRE."""
    with t.or_() as o:
        o.tfe_is_western_rome()
        o.has_or_had_tag("EAR")


def offices():
    doc = Doc()
    doc.note("TFE: the offices of the late Roman state, one for the treasury, one for the court and one for the army\n"
             "(written by script/bureaucracies.py). Held by the two Roman empires (and Stilicho's West); vanilla's Byzantine\n"
             "set is behind Fate of the Phoenix and BYZ/TRE. Funded, an office pays its positive side; neglected, its\n"
             "negative side bites (scale = 1 - maintenance). The Sacrae Largitiones are the imperial treasury (the Comes\n"
             "Sacrarum Largitionum), the Magister Officiorum heads the palace offices and the post, and the Magister Peditum\n"
             "commands the infantry of the field army (Notitia Dignitatum).")
    doc.types.note("TFE: each bureaucracy has an impact modifier (vanilla's 01_byz.txt and 02_generic_bureaucracies.txt do the\n"
                   "same); written by script/bureaucracies.py")
    doc.icons.note("TFE: the Roman bureaucracies' impact modifiers, badged as vanilla's are (script/bureaucracies.py)")

    doc.bureaucracy(
        "tfe_sacrae_largitiones_bureaucracy", title="Sacrae Largitiones",
        desc="The Sacred Largesses, the treasury of the Augusti: the mints, the mines, the gold-tax on traders and the stores "
             "that pay the army and the court. Well funded, its comites and their clerks gather what the provinces owe and "
             "keep the estates quiet about it. Starved of funds, its collectors turn to extortion and neglect, and the "
             "taxpayers learn to hide what they have.",
        potential=roman, likes=["crown_estate"], dislikes=["nobles_estate", "peasants_estate"],
        neutral={"creditworthiness_bonus": 0.05},
        positive={"global_estate_max_tax": 0.05, "global_estate_target_satisfaction": 0.025},
        negative={"global_estate_max_tax": -0.05, "global_estate_target_satisfaction": -0.05})

    doc.bureaucracy(
        "tfe_magister_officiorum_bureaucracy", title="Magister Officiorum",
        desc="The Master of Offices rules the scrinia, the palace guard and the imperial post, and with them the paper that "
             "binds a far-flung empire to its capital. Funded, orders reach the frontier before the season changes and the "
             "court's favour is worth spending. Neglected, the post runs late, petitions go unanswered and the provinces "
             "learn to govern themselves.",
        potential=roman, likes=["crown_estate", "burghers_estate"], dislikes=["nobles_estate"],
        neutral={"monthly_legitimacy": 0.05},
        positive={"monthly_political_influence_gain_modifier": 0.1, "global_distance_from_capital_speed_propagation": 0.1},
        negative={"monthly_political_influence_gain_modifier": -0.15,
                  "global_distance_from_capital_speed_propagation": -0.1})

    doc.note("discipline is a Unit-category key but vanilla puts it in country blocks; the dearer upkeep is the price of drill")
    doc.bureaucracy(
        "tfe_magister_peditum_bureaucracy", title="Magister Peditum",
        desc="The Master of Foot commands the infantry of the field army and the drill that keeps it a legion rather than a "
             "mob. His camps are costly to feed and to arm, but a funded command turns recruits into soldiers who hold the "
             "line. Left to rot, the drill lapses and pay falls behind, and the army remembers that it can be bought.",
        potential=roman, likes=["nobles_estate"], dislikes=["burghers_estate"],
        neutral={"monthly_army_tradition": 0.05},
        positive={"discipline": 0.05, "army_maintenance_efficiency": -0.1},
        negative={"discipline": -0.05})
    return doc


def slots():
    doc = Doc()
    doc.note("TFE: the Roman state keeps three offices at once (bureaucracies/tfe_roman.txt). Vanilla gives no base slot and\n"
             "its sources (advances, laws, capital rank) reach the empires late, so each starts with the three it needs.")
    doc.modifier("tfe_roman_bureaucracy_slots", potential=lambda t: t.tfe_is_roman_empire(), global_max_bureaucracy_slots=3)
    return doc


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    doc = offices()
    return {"in_game/common/bureaucracies/tfe_roman.txt": doc.text(),
            "main_menu/common/modifier_type_definitions/tfe_bureaucracies.txt": doc.types.text(),
            "main_menu/common/modifier_icons/tfe_bureaucracies.txt": doc.icons.text(),
            "main_menu/localization/english/tfe_bureaucracies_l_english.yml": doc.loc.text(),
            "in_game/common/auto_modifiers/tfe_roman_bureaucracy.txt": slots().text()}
