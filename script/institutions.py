"""Vanilla's 18 institutions in 395-895: same keys, ages and spread values, a late-antique theme, and a plausible-only
spawn rule (one scripted trigger per institution, `tfe_<key>_plausible_location`).

Writes REPLACE: copies read from vanilla each run (location fallback and old can_spawn dropped), the 18 triggers and the
names. The root advance of each institution is renamed with it (`ADVANCE_RENAME` feeds the table in advances.py).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))
import borders as b  # noqa: E402
from advances import _kids  # noqa: E402
from lint_script import parse  # noqa: E402
from pdx.core import Node, from_entries, render  # noqa: E402

OUT = "in_game/common/institution/tfe_institutions.txt"
TRIGGERS = "in_game/common/scripted_triggers/tfe_institution_triggers.txt"
LOC = "main_menu/localization/english/replace/tfe_institutions_l_english.yml"

OWNED_CULTURE = ("custom_tooltip = { text = dominant_culture_is_owners_culture dominant_culture = owner.culture }")
CITY = "OR = { location_rank = location_rank:city location_rank = location_rank:megalopolis }"
CLERGY, NOBLES, BURGHERS, PEASANTS = ("num_pop_type:clergy > 0", "num_pop_type:nobles > 0", "num_pop_type:burghers > 0",
                                      "num_pop_type:peasants > 0")
PORT = "is_port = yes"


def regions(*names: str) -> str:
    return "OR = { " + " ".join(f"region = region:{n}" for n in names) + " }"


def tfe(*conds: str, culture: bool = True) -> str:
    """has_owner, the conditions, and (usually) the vanilla tooltip: an institution is born where its people live."""
    return "\n".join(["has_owner = yes", *conds, *([OWNED_CULTURE] if culture else [])])


GERMANIC = "owner = { culture = { has_culture_group = culture_group:german_group } }"
BORDERS_ROME = "any_neighbor_location = { owner ?= { tfe_is_roman_empire = yes } }"

# key -> (name, description, the body of its plausible trigger). Brief: ages-and-peoples task 1.4.
THEMES: dict[str, tuple[str, str, str]] = {
    "feudalism": ("Patrocinium",
        "Where the state cannot protect the poor, a great landlord can. Peasants and small owners commend themselves "
        "and their land to a patron, pay him rent and service, and are defended in return. The patron's estate "
        "grows into a power of its own.",
        tfe(NOBLES, "OR = { sub_continent = sub_continent:western_europe region = region:italy_region }")),
    "legalism": ("Roman Law",
        "Rome's jurists have written down how a citizen may sue, marry, bequeath and contract, and the codes of "
        "the emperors bind the whole Empire. Where the law is known and its courts sit, a stranger can trust a "
        "bargain and a governor can be held to a rule.",
        tfe(CITY, "owner = { OR = { tag = EAR tfe_is_western_rome = yes } }")),
    "meritocracy": ("The Nine Ranks",
        "Officials are graded in nine ranks by the quality of their character and learning, and the court rises "
        "by recommendation rather than by blood. The system began under the kings of Wei and shapes the "
        "governments of the east.",
        tfe(CITY, "sub_continent = sub_continent:east_asia")),
    "renaissance": ("Monasticism",
        "Men and women leave the world for a life of prayer and labour under a rule. Their houses clear land, copy "
        "books, shelter travellers and keep the learning of an older age alive.",
        tfe(CLERGY, regions("egypt_region", "crescent_region", "anatolia_region", "france_region"))),
    "banking": ("The Solidus",
        "Constantine's gold coin has kept its weight for generations, and the world prices its goods by it. Where "
        "the solidus circulates, bankers lend against it and merchants trust a bargain made in it.",
        tfe(CITY, BURGHERS, regions("balkan_region", "anatolia_region", "crescent_region", "egypt_region"))),
    "professional_armies": ("Foederati",
        "Whole peoples are settled within the frontier and bound by treaty to fight for the emperor under their "
        "own chiefs. Their warbands are better soldiers than the levies of the provinces, and they know it.",
        tfe(GERMANIC, BORDERS_ROME, culture=False)),
    "new_world": ("The Monsoon Trade",
        "Sailors from Egypt and Arabia have learned the rhythm of the monsoon winds and cross the Indian Ocean to "
        "the pepper coasts of India. Each year the ships carry out gold and wine and bring back spices, cloth and "
        "gems.",
        tfe(PORT, regions("arabia_region", "ethiopia_region", "somalia_region", "egypt_region",
                          "western_india_region"))),
    "printing_press": ("The Scriptorium",
        "The codex has replaced the scroll, and monks and clerks copy it by hand in workshops attached to cathedrals "
        "and monasteries. Books grow cheaper and more people learn to read them.",
        tfe(CLERGY, CITY, "OR = { sub_continent = sub_continent:western_europe "
                          "sub_continent = sub_continent:middle_east }")),
    "pike_and_shot": ("Mounted Archery",
        "The riders of the steppe and the Persian plateau shoot from the saddle, wheeling and loosing. Their way "
        "of war spreads to every army that has faced them and survived.",
        tfe(regions("persia_region", "khorasan_region", "steppes_region", "anatolia_region"))),
    "confessionalism": ("Religious Law",
        "A faith that writes down its rules makes a community of its believers, with courts of its own. Councils, "
        "synods and schools of jurists set out what the faithful must do, and judges apply it to the common life.",
        tfe(CITY, CLERGY, regions("arabia_region", "crescent_region", "persia_region"))),
    "global_trade": ("The Silk Road",
        "Caravans carry silk, paper and spice across the oases of Central Asia, and the cities along the road grow "
        "rich on tolls and markets. Goods, faiths and ideas pass from hand to hand between China and the "
        "Mediterranean.",
        tfe(CITY, regions("xinjiang_region", "khorasan_region", "west_china_region", "north_china_region"))),
    "artillery_institution": ("Greek Fire",
        "Engineers of Constantinople learn to throw a burning liquid that water cannot put out. The secret of its "
        "making is closely kept, and the fleets and walls it defends are hard to take.",
        tfe(PORT, CITY, regions("balkan_region", "anatolia_region", "crescent_region"))),
    "manufactories": ("Paper",
        "Paper, a Chinese art, reaches the workshops of Samarkand and Baghdad. It is cheaper than parchment and "
        "papyrus, and the clerks, merchants and scholars who use it write more.",
        tfe(CITY, regions("khorasan_region", "persia_region", "crescent_region"))),
    "scientific_revolution": ("The House of Wisdom",
        "Scholars at the caliph's court gather books from every land and translate them into Arabic. In Baghdad "
        "mathematicians, astronomers and physicians set out to test what the ancients wrote.",
        tfe(CITY, regions("crescent_region", "persia_region"))),
    "military_revolution": ("The Heavy Horse",
        "The stirrup and a stronger breed of horse give the armoured rider a seat from which he can couch a lance. "
        "A charge of such men can break an infantry line, and the ruler who can field them has the upper hand.",
        tfe(NOBLES, regions("france_region", "north_german_region", "persia_region"))),
    "enlightenment": ("The Carolingian Renaissance",
        "Charlemagne gathers scholars from every part of Christendom to his court. Schools open at cathedrals and "
        "monasteries, handwriting is made clear, and the Latin classics are copied again.",
        tfe(CLERGY, regions("france_region", "north_german_region", "south_german_region", "italy_region"))),
    "industrialization": ("The Manor",
        "A lord's estate is farmed in strips by dependent peasants, who owe him labour on his own fields. The "
        "mill, the heavy plough and the three-field rotation make such estates the cell of the northern economy.",
        tfe(PEASANTS, regions("france_region", "north_german_region", "south_german_region",
                              "great_britain_region"))),
    "levee_en_masse": ("Feudalism",
        "Land is held in return for military service, and every lord owes his king a body of mounted men. Counts "
        "and their vassals can call up an army for the season and send it home when the campaign is over.",
        tfe(NOBLES, regions("france_region", "north_german_region", "south_german_region", "italy_region"))),
}


def vanilla_institutions() -> dict[str, Node]:
    out = {}
    for p in sorted((b.GAME / "in_game/common/institution").glob("*.txt")):
        for node in from_entries(parse(p.read_text(encoding="utf-8-sig"))):
            if node.key and node.key in THEMES:
                out[node.key] = node
    return out


def build() -> str:
    van = vanilla_institutions()
    out = []
    for key in THEMES:
        keep = [n for n in _kids(van[key]) if n.key not in ("location", "can_spawn")]
        spawn = Node("can_spawn", "=", from_entries(parse(f"tfe_{key}_plausible_location = yes")))
        out.append(Node("REPLACE:" + key, "=", keep[:1] + [spawn] + keep[1:]))   # age first, then can_spawn
    out[0].lead = ["TFE: vanilla's institutions with a 395-895 theme and a plausible-only spawn "
                   "(written by script/institutions.py)"]
    return render(out)


def triggers() -> str:
    head = ("# Scope: location. One plausible spawn site per institution for 395-895 (written by script/institutions.py).\n"
            "# The game rule is ignored: institutions are born where their people live, not in a fixed city.\n")
    blocks = []
    for key, (_, _, body) in THEMES.items():
        text = "\n".join("\t" + l for l in body.split("\n"))
        blocks.append(f"tfe_{key}_plausible_location = {{\n{text}\n}}\n")
    return head + "\n" + "\n".join(blocks)


def loc() -> str:
    lines = ["l_english:"] + [f' {k}: "{n}"\n {k}_desc: "{d}"' for k, (n, d, _) in THEMES.items()]
    return "\n".join(lines) + "\n"


def outputs():
    return {OUT: build(), TRIGGERS: triggers(), LOC: loc()}
