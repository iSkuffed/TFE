"""The Christianisation of Europe (RoadMap #30): Nicene and Arian movements (vanilla's movement engine, the Reformation's)
carried by saints and missionaries who walk to a pagan location and preach there.
Spec: docs/specs/2026-10-05-christianisation-design.md."""
import functools
import re
import sys
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import (AreaFx, CharacterFx, CharacterTrig, CountryFx, CountryTrig, ExpeditionFx, ExpeditionTrig, LocationFx,
                     LocationTrig, PopTrig, RegionFx, ReligionFx, ReligionTrig)
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


class Saint(NamedTuple):
    key: str
    name: str
    faith: str
    year: int
    start: str
    targets: tuple[str, ...]  # a location, an *_area or an *_region
    age: int
    wait: int = 10  # years he waits for a country of his faith to send him, then never goes


SAINTS = (
    Saint("martin", "Martin", NICENE, 395, "tours", ("brittany_area", "orleanais_area"), 79),
    Saint("nicetas", "Nicetas", NICENE, 396, "nis", ("thrace_area",), 60),
    Saint("victricius", "Victricius", NICENE, 396, "rouen", ("picardy_area", "flanders_area"), 66),
    Saint("porphyry", "Porphyry", NICENE, 402, "jerusalem", ("gaza",), 55),
    Saint("germanus", "Germanus", NICENE, 429, "auxerre", ("great_britain_region",), 50),
    Saint("patrick", "Patrick", NICENE, 432, "london", ("ireland_region",), 45),
    Saint("severinus", "Severinus", NICENE, 454, "aquileia", ("austria_area", "upper_austria_area", "salzburg_area"), 44),
    Saint("sigesar", "Sigesar", ARIAN, 400, "tarnovo", ("silesia_area", "bavaria_area"), 50, wait=20),
    Saint("ajax", "Ajax", ARIAN, 466, "toulouse", ("galicia_area", "north_portugal_area"), 50),
)
VANILLA_NAMES = {"martin", "nicetas", "germanus", "patrick", "severinus"}  # name_<key> is already in vanilla's loc
RANDOM_CHANCE = 5
TEMPLES_BONUS = 5
TEMPLES = "tfe_temples_closed"  # Close the Temples' country modifier
TEMPLES_GROWTH = 0.5
CATEGORY = "tfe_the_faith"
EXT = "gfx/interface/illustrations/event/backgrounds/exterior/"
MISSION_INCOME_MONTHS = 6
MISSION_MIN_GOLD = 50
MISSION_COOLDOWN = 5
TEMPLES_YEARS = 10
RISING_CHANCE = 25


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
    d.hook("yearly_country_pulse", "tfe_on_saints", "tfe_on_random_missionary")
    saints(d)
    random_missionary(d)
    end_missions(d)
    return d


@functools.cache
def region_of(location: str) -> str:
    import borders as b  # numpy, so only when asked
    path: list[str] = []
    for tok in re.finditer(r"(\w+)\s*=\s*\{|\}|(\w+)", (b.GAME / "in_game/map_data/definitions.txt").read_text(encoding="utf-8-sig")):
        if tok.group(1):
            path.append(tok.group(1))
        elif tok.group(0) == "}":
            path.pop()
        elif tok.group(2) == location:
            return next(p for p in reversed(path) if p.endswith("_region"))
    raise KeyError(location)


def each_target(fx: CountryFx, s: Saint, body):
    """run body(location scope) on every location among the saint's targets"""
    for target in s.targets:
        if target.endswith("_area"):
            with fx.link(f"area:{target}", AreaFx) as ar, ar.every_location_in_area() as loc:
                body(loc)
        elif target.endswith("_region"):
            with fx.link(f"region:{target}", RegionFx) as rg, rg.every_location_in_region() as loc:
                body(loc)
        else:
            with fx.link(f"location:{target}", LocationFx) as loc:
                body(loc)


def send_saint(fx: CountryFx, s: Saint):
    """the saint sets out from his own town, sent by the country of his faith that holds it or that rules its region"""
    flag = f"tfe_saint_{s.key}"
    with fx.if_() as i:
        with i.limit() as t:
            t.current_date(f"{s.year}.1.1", op=">=")
            t.current_date(f"{s.year + s.wait}.1.1", op="<")
            t.not_(lambda n: n.has_global_variable(flag))
            t.not_(lambda n: n.has_variable("tfe_mission_to"))  # an earlier saint set out this pulse
            t.compare("religion", "=", f"religion:{s.faith}")
            with t.or_() as o:
                o.link(f"location:{s.start}", LocationTrig, lambda l: l.compare("owner", "?=", "root"))
                with o.and_() as a:
                    a.not_(lambda n: n.compare(f"location:{s.start}.owner.religion", "?=", f"religion:{s.faith}"))
                    with a.any_owned_location() as loc:
                        loc.compare("region", "=", f"region:{region_of(s.start)}")

        def add(loc: LocationFx):
            with loc.if_() as f:
                f.limit(lambda t: t._call(FIELD[s.faith], True))
                f.add_to_temporary_list("tfe_saint_fields")
        each_target(i, s, add)
        with i.ordered_in_list(LocationFx, list="tfe_saint_fields", order_by="population") as to:
            to.save_scope_as("tfe_mission_to")
        i.note(f"{s.name}: no pagans left there yet, so he waits (until {s.year + s.wait}, then never goes)")
        with i.if_() as g:
            g.limit(lambda t: t.exists("scope:tfe_mission_to"))
            g.set_global_variable(flag)
            with g.link(f"location:{s.start}", LocationFx) as frm:
                frm.save_scope_as("tfe_mission_from")
            g.create_character(first_name=f"name_{s.key}", religion=f"religion:{s.faith}", culture="root.culture",
                               estate="estate_type:clergy_estate", age=s.age, save_scope_as="tfe_missionary")
            with g.if_() as h:
                h.limit(lambda t: t.exists("scope:tfe_missionary"))
                h.tfe_send_missionary_effect(True)


def saints(d: Defs):
    with d.on_action("tfe_on_saints") as a:
        with a.trigger(CountryTrig) as t:
            t.not_(lambda n: n.has_variable("tfe_mission_to"))
        with a.effect(CountryFx) as e:
            for s in SAINTS:
                send_saint(e, s)


def fields_in_reach(fx: CountryFx, faith: str, name: str):
    """every field the country owns or borders, into the temporary list `name`"""
    with fx.every_owned_location() as loc:
        with loc.if_() as i:
            i.limit(lambda t: t._call(FIELD[faith], True))
            i.add_to_temporary_list(name)
        with loc.every_neighbor_location() as n, n.if_() as i:
            i.limit(lambda t: t._call(FIELD[faith], True))
            i.add_to_temporary_list(name)


def new_missionary(fx: CountryFx):
    """a generated priest of the country's faith and people sets out from its capital for scope:tfe_mission_to"""
    with fx.if_() as i:
        i.limit(lambda t: t.exists("scope:tfe_mission_to"))
        with i.go_capital() as cap:
            cap.save_scope_as("tfe_mission_from")
        i.create_character(religion="root.religion", culture="root.culture", estate="estate_type:clergy_estate", age=35,
                           save_scope_as="tfe_missionary")
        with i.if_() as g:
            g.limit(lambda t: t.exists("scope:tfe_missionary"))
            g.tfe_send_missionary_effect(True)


def random_missionary(d: Defs):
    """now and then a Christian court with pagans in reach sends a priest of its own; more often with the temples closed"""
    with d.on_action("tfe_on_random_missionary") as a:
        with a.trigger(CountryTrig) as t:
            t.not_(lambda n: n.has_variable("tfe_mission_to"))
            t.num_locations(3, op=">=")
            with t.or_() as o:
                for faith in MOVEMENT:
                    with o.and_() as x:
                        x.compare("religion", "=", f"religion:{faith}")
                        x._call(IN_REACH[faith], True)
        with a.effect(CountryFx) as e:
            for closed, chance in ((True, RANDOM_CHANCE + TEMPLES_BONUS), (False, RANDOM_CHANCE)):
                with (e.if_() if closed else e.else_()) as i:
                    if closed:
                        i.limit(lambda t: t.has_country_modifier(TEMPLES))
                    with i.random(chance) as r:
                        for faith in MOVEMENT:
                            with r.if_() as f:
                                f.limit(lambda t, faith=faith: t.compare("religion", "=", f"religion:{faith}"))
                                fields_in_reach(f, faith, "tfe_reach_fields")
                                with f.random_in_list(LocationFx, list="tfe_reach_fields",
                                                      weight={"base": 1, "modifier": {"add": "population"}}) as to:
                                    to.save_scope_as("tfe_mission_to")
                                new_missionary(f)


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
        i.tfe_preach_effect(True)
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
            r.tfe_end_mission_effect(True)
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
                            s.tfe_send_missionary_effect(True)
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
            e.tfe_end_mission_effect(True)


def values():
    d = Doc()
    d.note("TFE: the price of a mission, half a year of trade and tax (written by script/missionaries.py)")
    with d.entry("tfe_mission_price") as e:
        e.field("value", "monthly_income_trade_and_tax")
        e.field("multiply", MISSION_INCOME_MONTHS)
        e.field("min", MISSION_MIN_GOLD)
    with d.entry("tfe_mission_price_twice") as e:
        e.field("value", "tfe_mission_price")
        e.field("multiply", 2)
    return d


def pagan_pop(t: PopTrig):
    with t.link("religion", ReligionTrig) as r:
        r.tfe_is_pagan_religion(True)


def sponsor(doc: Doc):
    with doc.decision("tfe_sponsor_mission", category=CATEGORY, title="Sponsor a Mission",
                      desc="A priest of our faith asks for a mule, a gospel book and a letter of protection, and he "
                           "will go to the people beyond our towns who still sacrifice to the old gods.",
                      image=EXT + "byz_clergy_exterior.dds") as d:
        with d.potential() as t, t.or_() as o:
            for faith in MOVEMENT:
                with o.and_() as a:
                    a.compare("religion", "=", f"religion:{faith}")
                    a._call(IN_REACH[faith], True)
        with d.allow() as t:
            with t.custom_tooltip_block("tfe_mission_price_tt") as ct:
                ct.gold("tfe_mission_price", op=">=")
            with t.custom_tooltip_block("tfe_mission_on_the_road_tt") as ct:
                ct.not_(lambda n: n.has_variable("tfe_mission_to"))
            with t.custom_tooltip_block("tfe_mission_sponsored_tt") as ct:
                ct.not_(lambda n: n.has_variable("tfe_mission_sponsored"))
        with d.ai_will_do() as v:
            v.value(0)
            with v.if_() as i:
                with i.limit() as t:
                    t.gold("tfe_mission_price_twice", op=">=")
                i.add(10)
        with d.option("a", text="Go with God.") as o, o.effect() as e:
            e.add_gold(value="tfe_mission_price", multiply=-1)
            e.set_variable(name="tfe_mission_sponsored", years=MISSION_COOLDOWN)
            e.custom_tooltip("tfe_sponsor_mission_tt")
            with e.hidden_effect() as h:
                for faith in MOVEMENT:
                    with h.if_() as f:
                        f.limit(lambda t, faith=faith: t.compare("religion", "=", f"religion:{faith}"))
                        fields_in_reach(f, faith, "tfe_reach_fields")
                        with f.ordered_in_list(LocationFx, list="tfe_reach_fields", order_by="population") as to:
                            to.save_scope_as("tfe_mission_to")
                        new_missionary(f)


def close_the_temples(doc: Doc):
    with doc.decision("tfe_close_the_temples", category=CATEGORY, title="Close the Temples",
                      desc="Theodosius forbade the sacrifices and shut the temples, but in the villages the altars still "
                           "smoke. Enforce the edicts: send the soldiers with the bishops, and let the old gods starve.",
                      image=EXT + "byz_clergy_hellenist_exterior.dds") as d:
        with d.potential() as t:
            t.compare("religion", "=", f"religion:{NICENE}")
            t.tfe_is_roman_empire(True)
        with d.allow() as t:
            with t.custom_tooltip_block("tfe_temples_already_closed_tt") as ct:
                ct.not_(lambda n: n.has_country_modifier(TEMPLES))
        with d.ai_will_do() as v:
            v.value(0)
            with v.if_() as i:
                with i.limit() as t:
                    t.stability(50, op=">=")
                    t.at_war(False)
                i.add(10)
        with d.option("a", text="The edicts will be obeyed.") as o, o.effect() as e:
            e.add_country_modifier(modifier=TEMPLES, years=TEMPLES_YEARS)
            e.custom_tooltip("tfe_close_the_temples_tt")
            with e.hidden_effect() as h, h.every_owned_location() as loc:
                with loc.every_pop() as p:
                    p.limit(pagan_pop)
                    p.add_pop_satisfaction("pop_satisfaction_mild_penalty")
                with loc.if_() as i:
                    i.limit(lambda t: t._call(FIELD[NICENE], True))
                    with i.random(RISING_CHANCE) as r, r.every_pop() as p:
                        p.limit(pagan_pop)
                        p.add_pop_satisfaction("pop_satisfaction_extreme_penalty")


def faith_decisions(loc: Loc):
    """(the category file, the decisions file), sharing the movements' localisation"""
    cats, doc = Doc(), Doc()
    cats.loc = doc.loc = loc
    cats.note("TFE: The Faith's decisions (decisions/tfe_christianisation.txt), after the Fall of the West's.")
    cats.decision_category(CATEGORY, title="The Faith", sort_order=1)
    doc.note("TFE: missions and the edicts against the sacrifices (written by script/missionaries.py)")
    sponsor(doc)
    close_the_temples(doc)
    for key, text in (
            ("tfe_mission_price_tt", "We have the gold for a mission ([tfe_mission_price])"),
            ("tfe_mission_on_the_road_tt", "None of our missionaries is still on the road"),
            ("tfe_mission_sponsored_tt", f"We have not sponsored a mission in the last {MISSION_COOLDOWN} years"),
            ("tfe_temples_already_closed_tt", "The temples are not already closed"),
            ("tfe_sponsor_mission_tt", "A missionary of our faith sets out for the most populous pagan place in or "
                                       "beside our lands, and preaches there for 5 to 10 years."),
            ("tfe_close_the_temples_tt", f"For {TEMPLES_YEARS} years our faith spreads half again as fast and more of "
                                         "our priests go out to the pagans. Every pagan in our lands loses 10% "
                                         "satisfaction, and in a quarter of the pagan places they lose 25% more.")):
        loc.add(key, text)
    return cats, doc


def build():
    movements, types, icons = Doc(), Doc(), Doc()
    movements.note("TFE: the Christianisation of Europe (written by script/missionaries.py). Two rival movements convert\n"
                   "the pagans; a missionary who arrives where he was sent is pinned there as a spreader.")
    for faith in MOVEMENT:
        movement(movements, faith)
    types.note("TFE: the movements' growth modifiers (written by script/missionaries.py)")
    icons.note("TFE: the movements' growth modifiers (written by script/missionaries.py)")
    growth_types(types, icons, movements.loc)
    for s in SAINTS:
        if s.key not in VANILLA_NAMES:
            movements.loc.add(f"name_{s.key}", s.name)
    return movements, types, icons


def static_modifiers(loc: Loc):
    mods = Doc()
    mods.loc = loc
    mods.note("TFE: the Christianisation of Europe (written by script/missionaries.py)")
    mods.modifier(PREACHING, category="location", local_tfe_nicene_movement_growth_modifier=PREACHING_GROWTH,
                  local_tfe_arian_movement_growth_modifier=PREACHING_GROWTH)
    loc.add(f"STATIC_MODIFIER_NAME_{PREACHING}", "A Missionary Preaches")
    loc.add(f"STATIC_MODIFIER_DESC_{PREACHING}", "A man of God has come to live among these people, and they come to hear him.")
    mods.modifier(TEMPLES, category="country", national_tfe_nicene_movement_growth_modifier=TEMPLES_GROWTH)
    loc.add(f"STATIC_MODIFIER_NAME_{TEMPLES}", "The Temples Closed")
    loc.add(f"STATIC_MODIFIER_DESC_{TEMPLES}", "The edicts against the sacrifices are enforced in our lands.")
    return mods


MOVEMENTS, TYPES, ICONS = build()
MODIFIERS = static_modifiers(MOVEMENTS.loc)
CATEGORIES, DECISIONS = faith_decisions(MOVEMENTS.loc)
VALUES = values()
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
            "in_game/common/decision_categories/tfe_christianisation.txt": CATEGORIES.text(),
            "in_game/common/decisions/tfe_christianisation.txt": DECISIONS.text(),
            "in_game/common/script_values/tfe_christianisation.txt": VALUES.text(),
            "main_menu/localization/english/tfe_christianisation_l_english.yml": MOVEMENTS.loc.text()}
