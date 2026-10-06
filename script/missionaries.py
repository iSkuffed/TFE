"""The Christianisation of Europe (RoadMap #30): Nicene and Arian movements (vanilla's movement engine, the Reformation's)
carried by saints and missionaries who walk to a pagan location and preach there.
Spec: docs/specs/2026-10-05-christianisation-design.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryTrig, LocationTrig, ReligionTrig
from pdx.core import Q
from pdx.objects import Doc, LocationValue, Loc
from pdx.objects_defs import Defs

NICENE, ARIAN = "orthodox", "arianism"
MOVEMENT = {NICENE: "tfe_nicene_movement", ARIAN: "tfe_arian_movement"}
NAME = {NICENE: "Nicene Christianity", ARIAN: "Arian Christianity"}
# the old gods of the Roman world and its rim (tools/religions.txt); the heresies are the councils' (RoadMap #8)
PAGANS = ("religio_romana", "hellenism_religion", "celtic_paganism", "illyrian_paganism", "zalmoxism", "basque_paganism",
          "nuragic_religion", "armazi_religion", "kushite_religion", "arabian_paganism", "godala_religion", "norse",
          "slavic_paganism", "alan_paganism")
# the Goths' neighbours beyond the Danube and the Rhine; Gaul's Celts are left to the Nicenes
ARIAN_PAGANS = ("norse", "slavic_paganism", "zalmoxism", "alan_paganism")
CONVERTS = {NICENE: (*PAGANS, ARIAN), ARIAN: (*ARIAN_PAGANS, NICENE)}
# the religion-scope trigger naming the gods each movement's missionaries preach against
PAGAN_TRIGGER = {NICENE: "tfe_is_pagan_religion", ARIAN: "tfe_is_arian_pagan_religion"}
FIELD = {NICENE: "tfe_nicene_mission_field", ARIAN: "tfe_arian_mission_field"}
IN_REACH = {NICENE: "tfe_nicene_mission_in_reach", ARIAN: "tfe_arian_mission_in_reach"}
POP_TYPES = ("nobles", "clergy", "burghers", "laborers", "soldiers", "peasants", "tribesmen", "slaves")
# who listens: the towns for the Nicenes, the court and the warband for the Arians
POP_EFFECTS = {
    NICENE: {"burghers": 1.5, "clergy": 0.5, "nobles": 0.7, "laborers": 1, "soldiers": 0.8, "peasants": 1,
             "tribesmen": 0.8, "slaves": 0.5},
    ARIAN: {"nobles": 1.5, "tribesmen": 1.2, "soldiers": 1.2, "peasants": 1, "laborers": 0.8, "burghers": 0.5,
            "clergy": 0.5, "slaves": 0.5},
}
# a Goth does not give up Ulfilas' Bible easily; a Roman gives up Nicaea more slowly still
RIVAL_EFFECT = {NICENE: 0.3, ARIAN: 0.2}
# the patriarchal and metropolitan sees (Caesarea has no location: Jerusalem stands in)
SEES = ("rome", "constantinople", "alexandria", "antioch", "tunis", "milano", "trier", "arles", "thessaloniki",
        "ayasuluk", "jerusalem")
# the temples that held out (tools/religions.txt): Carrhae, Heliopolis, the Marneion, Philae, Athens and the Mani
CULT_CENTRES = ("harran", "baalbek", "gaza", "aswan", "athens")
CULT_PROVINCES = ("laconia_province",)
R0 = {NICENE: (0, 0.012), ARIAN: (0, 0.010)}  # vanilla's Lutherans run 0.002 to 0.03; tuned in game
SPREADER_INFECTION = 0.05  # a preaching missionary, as Luther
SPREAD_THRESHOLD = 0.05


def triggers():
    d = Defs()
    d.note("TFE: the Christianisation of Europe. Written from script/missionaries.py.")
    for faith, name in PAGAN_TRIGGER.items():
        d.note(f"religion scope: gods the {MOVEMENT[faith]} converts from")
        with d.trigger(name, ReligionTrig) as t, t.or_() as o:
            for pagan in (PAGANS if faith == NICENE else ARIAN_PAGANS):
                o.compare("this", "=", f"religion:{pagan}")
    for faith in MOVEMENT:
        d.note(f"location: a place the {NAME[faith]} missionaries would preach in, its people mostly keeping those gods")
        with d.trigger(FIELD[faith], LocationTrig) as t, t.link("dominant_religion", ReligionTrig, op="?=") as r:
            r._call(PAGAN_TRIGGER[faith], True)
        d.note("country: a field it owns or borders")
        with d.trigger(IN_REACH[faith], CountryTrig) as t, t.link("any_owned_location", LocationTrig) as loc, \
                loc.or_() as o:
            o._call(FIELD[faith], True)
            with o.any_neighbor_location() as n:
                n._call(FIELD[faith], True)
    return d


def factors(faith: str):
    """(condition, multiplier, why) for r0, applied one after another"""
    def rank(r):
        return lambda t: t.compare("location_rank", "?=", f"location_rank:{r}")

    def neighbour(t: LocationTrig):
        with t.any_neighbor_location() as n:
            n.compare("dominant_religion", "?=", f"religion:{faith}")

    def pagan_king(t: LocationTrig):
        with t.link("owner", CountryTrig, op="?=") as o, o.link("religion", ReligionTrig) as r:
            r._call(PAGAN_TRIGGER[NICENE], True)

    yield rank("town"), 1.5 if faith == NICENE else 1.1, "a town hears the preacher first"
    yield rank("city"), 2 if faith == NICENE else 1.2, "and a city more"
    yield (lambda t: king_of(t, faith)), 1.5, "a king of the faith"
    yield neighbour, 1.25, "a believing neighbour"
    if faith == NICENE:
        yield see, 1.5, "a bishop's see"
    yield pagan_king, 0.5, "a pagan king protects the old gods"
    yield cult_centre, 0.3, "a great temple holds out while its people keep the gods"


def king_of(t: LocationTrig, faith: str):
    t.link("owner", CountryTrig, lambda o: o.compare("religion", "=", f"religion:{faith}"), op="?=")


def see(t: LocationTrig):
    with t.or_() as o:
        for loc in SEES:
            o.compare("this", "=", f"location:{loc}")


def cult_centre(t: LocationTrig):
    with t.link("dominant_religion", ReligionTrig, op="?=") as r:
        r._call(PAGAN_TRIGGER[NICENE], True)
    with t.or_() as o:
        for loc in CULT_CENTRES:
            o.compare("this", "=", f"location:{loc}")
        for prov in CULT_PROVINCES:
            o.compare("province", "=", f"province:{prov}")


def r0(v: LocationValue, faith: str):
    lo, hi = R0[faith]
    v.raw(f"value = {{ {lo} {hi} }}")  # GAP: no binding for a random-range value
    with v.if_() as root:
        with root.limit() as t:
            t.exists("root")
        if faith == ARIAN:
            root.note("Nicene Romans turn Arian only under an Arian king (Huneric's Africa)")
            with root.if_() as i:
                with i.limit() as t:
                    t.compare("dominant_religion", "?=", f"religion:{NICENE}")
                    t.not_(lambda n: king_of(n, ARIAN))
                i.multiply(0)
        for cond, factor, why in factors(faith):
            root.note(why)
            with root.if_() as i:
                with i.limit() as t:
                    cond(t)
                i.multiply(factor)


def map_color(v: LocationValue, faith: str):
    share = Q(f"religion_percentage(religion:{faith})")
    for kind, cond, colour in (
            (v.if_, lambda t: t.compare(share, "=", 0), "NULL"),
            (v.else_if, lambda t: t.compare("dominant_religion", "=", f"religion:{faith}"), "HIGH"),
            (v.else_if, lambda t: t.compare(share, ">", SPREAD_THRESHOLD), "MID"),
            (v.else_, None, "LOW")):
        with kind() as i:
            if cond:
                with i.limit() as t:
                    cond(t)
            i.value(f"define:NMapColors|MAP_COLOR_{colour}")


def movement(doc: Doc, faith: str):
    rival = ARIAN if faith == NICENE else NICENE
    with doc.entry(MOVEMENT[faith]) as e:
        e.field("religion", faith)
        e.note("seeded on day one (on_action/tfe_christianisation.txt), never by the monthly scheduler")
        with e.triggers("potential") as t:
            t.always(True)
        e.data("monthly_spawn_chance", value=0)
        with e.block("spawn"):
            pass
        e.data("environmental_infection", value=SPREADER_INFECTION)
        with e.effects("r0", LocationValue) as v:
            r0(v, faith)
        e.raw("calc_interval_days = { 20 40 }")  # GAP: no binding for a random-range value
        with e.block("required_religions") as rr:
            for x in CONVERTS[faith]:
                rr._call(x)
        e.field("development", "positive")
        e.field("literacy", "positive")
        e.field("local_control", "neutral")
        e.field("pop_satisfaction", "negative")
        for pop_type, mult in POP_EFFECTS[faith].items():
            e.data("specific_pop_type_effect", pop_type=pop_type, multiplier=mult)
        e.data("specific_pop_type_effect", religion=rival, multiplier=RIVAL_EFFECT[faith])
        e.data("location_spread_threshold", value=SPREAD_THRESHOLD)
        with e.effects("map_color", LocationValue) as v:
            map_color(v, faith)


def growth_types(types: Doc, icons: Doc, loc: Loc):
    """the engine's growth modifiers are ours to define (movements/readme.txt); they wear vanilla's Lutheran icons"""
    for faith, key in MOVEMENT.items():
        loc.add(key, NAME[faith])
        for scope, category, where in (("local", "location", "in a [location|e]"),
                                       ("national", "country", "in [locations|e] owned by the [country|e]")):
            mod = f"{scope}_{key}_growth_modifier"
            with types.entry(mod) as t:
                t.field("percent", True)
                t.data("game_data", category=category)
            with icons.entry(mod) as i:
                i.field("positive", Q(f"gfx/interface/icons/modifier_types/{scope}_lutheranism_movement_growth_modifier.dds"))
            loc.add(f"MODIFIER_TYPE_NAME_{mod}", f"[ShowMovementDefinitionNameWithNoTooltip('{key}')] Growth Modifier")
            loc.add(f"MODIFIER_TYPE_DESC_{mod}",
                    f"How much the [ShowMovementDefinitionName('{key}')] [movement|e] grows {where}.")


def build():
    movements, types, icons = Doc(), Doc(), Doc()
    movements.note("TFE: the Christianisation of Europe (written by script/missionaries.py). Two rival movements convert\n"
                   "the pagans; a missionary who arrives where he was sent is pinned there as a spreader.")
    for faith in MOVEMENT:
        movement(movements, faith)
    types.note("TFE: the movements' growth modifiers (written by script/missionaries.py)")
    icons.note("TFE: the movements' growth modifiers (written by script/missionaries.py)")
    growth_types(types, icons, movements.loc)
    return movements, types, icons


MOVEMENTS, TYPES, ICONS = build()
TRIGGERS = triggers()


def outputs():
    """{repo-relative path: text}; run.py writes each with its BOM."""
    return {"in_game/common/movements/tfe_christianisation.txt": MOVEMENTS.text(),
            "main_menu/common/modifier_type_definitions/tfe_christianisation.txt": TYPES.text(),
            "main_menu/common/modifier_icons/tfe_christianisation.txt": ICONS.text(),
            "in_game/common/scripted_triggers/tfe_christianisation.txt": TRIGGERS.text(),
            "main_menu/localization/english/tfe_christianisation_l_english.yml": MOVEMENTS.loc.text()}
