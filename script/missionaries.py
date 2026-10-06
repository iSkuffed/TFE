"""The Christianisation of Europe (RoadMap #30): Nicene and Arian movements (vanilla's movement engine, the Reformation's)
carried by saints and missionaries who walk to a pagan location and preach there.
Spec: docs/specs/2026-10-05-christianisation-design.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import (CharacterFx, CharacterTrig, CountryFx, CountryTrig, ExpeditionFx, ExpeditionTrig, LocationFx, LocationTrig,
                     ReligionFx, ReligionTrig)
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
# vanilla's Lutherans run 0.002 to 0.03, but 0.012 doubled the Nicene world in two years from two spawns (probe, Task 2)
R0 = {NICENE: (0, 0.002), ARIAN: (0, 0.0016)}
SPREADER_INFECTION = 0.05  # a preaching missionary, as Luther
SPREAD_THRESHOLD = 0.05
ARIAN_SEEDS = ("VIS", "GEP", "RUG", "SCR", "HAS")  # the Arian peoples of 395 (tools/religions.txt)
EXPEDITION_TYPE = "tfe_missionary"
TRAVEL_SPEED = 0.5  # a man on foot, faster than a people with wagons (0.25)
PREACH_YEARS = (5, 7, 10)
PREACHING = "tfe_mission_preaching"  # the location modifier where he preaches
PREACHING_GROWTH = 0.5
MAX_MISSIONS = 3
MOVE_ON_CHANCE = 50
NEAR_RINGS = 3  # he walks on to a field within this many steps of where he preached


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
            o.compare("province_definition", "=", f"province_definition:{prov}")


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


def seed(loc: LocationFx, faith: str):
    """a movement of the believers already there: each spawn is its own movement (probed), so nothing converts on day one"""
    loc.spawn_movement(movement_definition=f"movement_definition:{MOVEMENT[faith]}",
                       supporters={"value": "population", "multiply": Q(f"religion_percentage(religion:{faith})")})


def pulses():
    d = Defs()
    d.note("TFE: the Christianisation of Europe (written by script/missionaries.py). Day one seeds the movements; a yearly\n"
           "pulse sends saints and missionaries and ends their missions.")
    d.hook("on_game_start", "tfe_on_start_christianisation")
    with d.on_action("tfe_on_start_christianisation") as a, a.effect(CountryFx) as e:
        e.note("the Nicene sees")
        for loc in SEES:
            with e.link(f"location:{loc}", LocationFx) as here:
                seed(here, NICENE)
        e.note("the Arian peoples, at their capitals")
        for tag in ARIAN_SEEDS:
            with e.link(f"c:{tag}", CountryFx, op="?=") as c, c.go_capital(op="?=") as cap:
                seed(cap, ARIAN)
    end_missions(d)
    return d


def spreader(fx: CountryFx, add: bool):
    """the missionary's own faith picks the movement: a country that changed faith while he walked does not change his"""
    for faith in MOVEMENT:
        with fx.if_() as i:
            with i.limit() as t, t.link("scope:tfe_missionary", CharacterTrig) as c:
                c.compare("religion", "=", f"religion:{faith}")
            with i.link(f"religion:{faith}", ReligionFx) as r:
                if add:
                    with r.ordered_movement_in_religion(max=1, order_by={"value": 1}) as mv:
                        mv.add_spreader(character="scope:tfe_missionary", location="scope:tfe_mission_at")
                else:
                    with r.every_movement_in_religion() as mv:
                        mv.remove_spreader("scope:tfe_missionary")


def effects():
    d = Defs()
    d.note("TFE: missionaries (written by script/missionaries.py). Country scope; the caller saves scope:tfe_missionary\n"
           "and the locations each effect names.")
    d.note("sends scope:tfe_missionary from scope:tfe_mission_from to scope:tfe_mission_to (one on the road per country)")
    with d.effect("tfe_send_missionary_effect", CountryFx) as fx:
        fx.set_variable(name="tfe_mission_from", value="scope:tfe_mission_from")
        fx.set_variable(name="tfe_mission_to", value="scope:tfe_mission_to")
        with fx.link("scope:tfe_missionary", CharacterFx) as c:
            c.set_variable("tfe_on_road")
        fx.start_expedition(type=f"expedition_type:{EXPEDITION_TYPE}", leader="scope:tfe_missionary")
    d.note("he arrives at scope:tfe_mission_at: pinned there as the movement's spreader for 5 to 10 years, or until he dies")
    with d.effect("tfe_preach_effect", CountryFx) as fx:
        with fx.link("scope:tfe_missionary", CharacterFx) as c:
            c.remove_variable("tfe_on_road")
            c.set_variable(name="tfe_mission_at", value="scope:tfe_mission_at")
            with c.if_() as i:
                with i.limit() as t:
                    t.has_variable("tfe_missions")
                i.change_variable(name="tfe_missions", add=1)
            with c.else_() as i:
                i.set_variable(name="tfe_missions", value=1)
            with c.random_list() as r:
                for years in PREACH_YEARS:
                    with r.weight(1) as w:
                        w.set_variable(name="tfe_preaching", years=years)
        with fx.link("scope:tfe_mission_at", LocationFx) as loc:
            loc.add_location_modifier(modifier=PREACHING, years=max(PREACH_YEARS))
        spreader(fx, add=True)
    d.note("his stay is over, or he died: the spreader and the modifier go")
    with d.effect("tfe_end_mission_effect", CountryFx) as fx:
        with fx.link("scope:tfe_missionary.var:tfe_mission_at", LocationFx, op="?=") as loc:
            loc.remove_location_modifier(PREACHING)
        spreader(fx, add=False)
        with fx.link("scope:tfe_missionary", CharacterFx) as c:
            c.remove_variable("tfe_mission_at")
            c.remove_variable("tfe_preaching")
    return d


def arrive(fx: CountryFx):
    """on_end and on_fail: preach at the destination if there is one; the popup's dry run of on_fail finds none"""
    with fx.if_() as i:
        with i.limit() as t:
            t.has_variable("tfe_mission_to")
            with t.link("scope:expedition", ExpeditionTrig) as x:
                x.exists("expedition_leader")
        with i.link("scope:expedition", ExpeditionFx) as x, x.go_expedition_leader() as leader:
            leader.save_scope_as("tfe_missionary")
        with i.link("var:tfe_mission_to", LocationFx) as to:
            to.save_scope_as("tfe_mission_at")
        i._call("tfe_preach_effect", True)
    fx.remove_variable("tfe_mission_from")
    fx.remove_variable("tfe_mission_to")


def expedition(doc: Doc):
    doc.loc.add(EXPEDITION_TYPE, "A Mission")
    doc.loc.add(f"{EXPEDITION_TYPE}_desc", "A man of God on the road with a staff and a gospel book, bound for people who "
                "still sacrifice to the old gods.")
    doc.note("A mission (written by script/missionaries.py), a copy of tfe_wandering_people (tfe_peoples.txt): the country\n"
             "sets tfe_mission_from and tfe_mission_to, then tfe_send_missionary_effect starts it.")
    with doc.entry(EXPEDITION_TYPE) as e:
        e.note("one missionary on the road per country: pace the chaos")
        e.field("unique", True)
        e.field("travel_speed", TRAVEL_SPEED)
        e.field("travel_mode", "land")
        e.field("dynamic_first_waypoint", True)
        e.field("origin", "none")
        e.field("ai", False)
        e.field("show_start_message", False)
        e.field("show_end_message", False)
        with e.triggers("potential", CountryTrig) as t:
            t.has_variable("tfe_mission_to")
        with e.triggers("leader", CharacterTrig) as t:
            t.is_expedition_leader(False)
        with e.effects("on_start", CountryFx) as fx, fx.link("scope:expedition", ExpeditionFx) as x:
            x.add_new_waypoint("root.var:tfe_mission_from")
            x.add_new_waypoint("root.var:tfe_mission_to")
        with e.effects("on_end", CountryFx) as fx:
            arrive(fx)
        with e.effects("on_fail", CountryFx) as fx:
            fx.note("no road there (Ireland, an island): he crosses by boat and preaches all the same")
            arrive(fx)


def collect_near(fx: CountryFx, frm: str, faith: str, name: str):
    """every field within NEAR_RINGS steps of `frm`, into the temporary list `name`"""
    def ring(loc: LocationFx, depth: int):
        with loc.every_neighbor_location() as n:
            with n.if_() as i:
                with i.limit() as t:
                    t._call(FIELD[faith], True)
                i.add_to_temporary_list(name)
            if depth > 1:
                ring(n, depth - 1)
    with fx.link(frm, LocationFx) as loc:
        ring(loc, NEAR_RINGS)


def end_missions(d: Defs):
    """the yearly pulse: a stay whose time is up ends; the missionary may walk on to a field nearby, else he retires
    (a character made for the road must not crowd the court)"""
    d.hook("yearly_country_pulse", "tfe_on_missions_end")
    with d.on_action("tfe_on_missions_end") as a, a.effect(CountryFx) as e, e.every_character() as c:
        with c.limit() as t:
            t.has_variable("tfe_mission_at")
            t.not_(lambda n: n.has_variable("tfe_preaching"))
        c.save_scope_as("tfe_missionary")
        with c.link("var:tfe_mission_at", LocationFx) as at:
            at.save_scope_as("tfe_mission_from")
        with c.link("root", CountryFx) as r:
            r._call("tfe_end_mission_effect", True)
            for faith in MOVEMENT:
                with r.if_() as i:
                    with i.limit() as t:
                        t.not_(lambda n: n.has_variable("tfe_mission_to"))
                        with t.link("scope:tfe_missionary", CharacterTrig) as who:
                            who.compare("religion", "=", f"religion:{faith}")
                            who.var("tfe_missions", "<", MAX_MISSIONS)
                    with i.random(MOVE_ON_CHANCE) as go:
                        collect_near(go, "scope:tfe_mission_from", faith, "tfe_near_fields")
                        with go.ordered_in_list(LocationFx, list="tfe_near_fields", order_by="population") as to:
                            to.save_scope_as("tfe_mission_to")
                        with go.if_() as s:
                            with s.limit() as t:
                                t.exists("scope:tfe_mission_to")
                            s._call("tfe_send_missionary_effect", True)
            r.note("a kill in the character's own scope fails PostValidate (probe): kill from the country")
            with r.if_() as i:
                with i.limit() as t, t.link("scope:tfe_missionary", CharacterTrig) as who:
                    who.not_(lambda n: n.has_variable("tfe_on_road"))
                i.kill_character_silently("scope:tfe_missionary")
    d.hook("on_character_death", "tfe_on_missionary_dies")
    with d.on_action("tfe_on_missionary_dies") as a:
        with a.trigger(CountryTrig) as t, t.link("scope:target", CharacterTrig) as dead:
            dead.has_variable("tfe_mission_at")
        with a.effect(CountryFx) as e:
            with e.link("scope:target", CharacterFx) as dead:
                dead.save_scope_as("tfe_missionary")
            e._call("tfe_end_mission_effect", True)


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


def static_modifiers(loc: Loc):
    mods = Doc()
    mods.loc = loc
    mods.note("TFE: the Christianisation of Europe (written by script/missionaries.py)")
    mods.modifier(PREACHING, category="location", local_tfe_nicene_movement_growth_modifier=PREACHING_GROWTH,
                  local_tfe_arian_movement_growth_modifier=PREACHING_GROWTH)
    loc.add(f"STATIC_MODIFIER_NAME_{PREACHING}", "A Missionary Preaches")
    loc.add(f"STATIC_MODIFIER_DESC_{PREACHING}", "A man of God has come to live among these people, and they come to hear him.")
    return mods


MOVEMENTS, TYPES, ICONS = build()
MODIFIERS = static_modifiers(MOVEMENTS.loc)
EXPEDITION = Doc()
EXPEDITION.loc = MOVEMENTS.loc
expedition(EXPEDITION)
EFFECTS = effects()
TRIGGERS = triggers()
PULSES = pulses()


def outputs():
    """{repo-relative path: text}; run.py writes each with its BOM."""
    return {"in_game/common/movements/tfe_christianisation.txt": MOVEMENTS.text(),
            "main_menu/common/modifier_type_definitions/tfe_christianisation.txt": TYPES.text(),
            "main_menu/common/modifier_icons/tfe_christianisation.txt": ICONS.text(),
            "in_game/common/scripted_triggers/tfe_christianisation.txt": TRIGGERS.text(),
            "in_game/common/on_action/tfe_christianisation.txt": PULSES.text(),
            "in_game/common/scripted_effects/tfe_christianisation.txt": EFFECTS.text(),
            "in_game/common/expedition_types/tfe_missionaries.txt": EXPEDITION.text(),
            "main_menu/common/static_modifiers/tfe_christianisation.txt": MODIFIERS.text(),
            "main_menu/localization/english/tfe_christianisation_l_english.yml": MOVEMENTS.loc.text()}
