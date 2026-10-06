# The Christianisation of Europe: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Two rival movements (Nicene, Arian) convert the pagans of Europe from 395. Saints and missionaries walk to a
pagan location and preach there. Rulers can sponsor a mission or close the temples, and a pagan king whose people have
turned Christian is asked to follow them.

**Architecture:** Everything is written by one script, `script/missionaries.py`, into the files it names in `outputs()`.
The engine is vanilla's movement system (`in_game/common/movements/`, readme there). A missionary is an expedition
(copied from `tfe_wandering_people`). When it arrives, its leader becomes the movement's spreader, pinned to the
destination. A yearly country pulse sends saints and random missionaries and ends finished missions. Two Native
decisions and one event make the levers.

**Tech Stack:** EU5 1.4 script; Python generators against `tools/pdx` (`Doc`, `Defs`, typed `api.py`); pytest;
pyright; `tools/lint_script.py`; `tools/eu5ctl.sh` in game.

**Spec:** `docs/specs/2026-10-05-christianisation-design.md` (same branch). Task 8 updates it for the changes this
plan makes; they are listed in "Changes from the spec" below.

## Global Constraints

- Workspace `/home/skuffed/tfe-christianity`, jj bookmark `christianisation`, based on `1.4`. Never touch `@` in the
  main folder. The PR targets `1.4`.
- jj only: `jj commit -m "<subject>"` after each task. At the end, `jj bookmark move christianisation --to @-`.
- Commit subjects are one evocative line about the game world, then a short body (see `jj log`), ending with
  `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.
- Generated files are never edited by hand. Edit `script/missionaries.py`, then
  `uv run --no-project --with numpy --with pytest --with pillow --with shapely --with pyright python script/run.py`.
- Tests:
  `EU5_DOCS="$HOME/.local/share/Steam/steamapps/compatdata/3450310/pfx/drive_c/users/steamuser/Documents/Paradox Interactive/Europa Universalis V/docs" uv run --no-project --with numpy --with pytest --with pillow --with shapely --with pyright python -m pytest -q tools/`
  (`EU5_DOCS` is needed because a workspace sits outside Documents). Pyright: `uv run --no-project --with pyright python -m pyright`.
  Lint: `EU5_DOCS=... uv run --no-project --with numpy python tools/lint_script.py`. All three must be green before
  the PR.
- After adding a scripted effect or trigger, or once `modifiers.log` changes: `EU5_DOCS=... python tools/pdx/gen_api.py`
  (with the same `uv run` prefix). After adding a script or loc file: `python tools/gen_index.py`.
- Script and loc files carry a UTF-8 BOM (`run.py` writes it). Python always passes `encoding="utf-8"` or `"utf-8-sig"`.
- **In game, from a workspace:** the game loads the path in the active playset (`TFE (Claude test)` in
  `Documents/.../Europa Universalis V/playsets.json`, now
  `C:/users/steamuser/Documents/Paradox Interactive/Europa Universalis V/mod/TFE/`). While the game is stopped, set
  that entry's `path` to `Z:/home/skuffed/tfe-christianity/`. Put it back once testing is done, also while the game
  is stopped.
- Run time at speed 5 (`tools/eu5ctl.sh key KP_Add KP_Add KP_Add KP_Add`) and confirm it with a screenshot before
  waiting. Never change mod files while the game runs.
- Never `add_country_modifier = { name = ... }`: the binding writes `modifier =`. Event `outcome` is
  positive/neutral/negative.
- Fun over accuracy, and pace the chaos (RoadMap design rules): at most one missionary walking per country.

## Probe results (Task 2)

- **P1:** one movement per `spawn_movement`. Harmless: the day-one sees each get their own, and `add_spreader` picks
  one through `ordered_movement_in_religion`.
- **P2:** a spreader alone starts conversion where the faith was absent. `tfe_preach_effect` spawns nothing.
- **P3:** far too fast at `R0 = 0.012`: majority-Nicene locations went from 992 to 2038 in two years. `R0` is now
  0.002 (Nicene) and 0.0016 (Arian); Task 9 tunes it.
- **P4:** `remove_spreader` on a living or dead character logs nothing. But `kill_character_silently = yes` inside the
  character's own scope fails PostValidate: the yearly pulse kills from the country, `kill_character_silently =
  scope:tfe_missionary`.
- Also: `province = province:laconia_province` is an error; the Mani is `province_definition =
  province_definition:laconia_province`.

## Changes from the spec (made here, written back into the spec in Task 8)

1. **The cult centres resist through `r0`, not a location modifier.** `r0` is ×0.3 at Harran, Baalbek, Gaza, Aswan
   and the Laconian and Attic locations while their dominant faith is pagan. It lapses by itself, and no resistance
   modifier types or day-one seeding are needed. The "smaller version under a pagan owner" is already `r0`'s ×0.5
   for a pagan owner, so it is dropped as a duplicate.
2. **No "reached your country" event.** Vanilla's `movements.20` is written for Hellenism.
3. **Satisfaction losses are one-shot.** EU5 has no modifier for one religion's pop satisfaction. Close the Temples
   takes 10% satisfaction from every pagan pop when it is taken, and a rising takes a further 25%. Both drift back as
   vanilla satisfaction does.
4. **Martin sets out in 395 like any saint,** within the first year, instead of standing as a spreader at Tours on
   day one.
5. **Random missionaries go to a random field in reach, weighted by population,** not the nearest one: EU5 has no
   cheap distance. Sponsor a Mission still picks the most populous.
6. **Caesarea has no location in EU5.** The Palestinian see is `jerusalem`, and Porphyry sets out from there.
7. **Every pop type gets a multiplier,** because a movement skips any pop type not listed (readme). Laborers and
   soldiers are added: Nicene laborers ×1 and soldiers ×0.8; Arian laborers ×0.8 and soldiers ×1.2 (the Gothic army
   was Arian).
8. **A saint whose sender is gone:** the owner of his start location sends him if it has his faith. Otherwise any
   country of his faith holding land in the start location's region sends him. If none, he waits, then is skipped.
9. **Saints take their sender's culture.** No per-saint culture table.

## Review Focus

1. **A missionary whose expedition fails** (no land road: Patrick to Ireland, an island). Expected: he preaches at the
   destination all the same, like the settlers who "cross by boat". The Expedition Lost popup's dry run of `on_fail`
   must not make him preach twice or preach without a destination. Tested in Task 4 (the guard on `tfe_mission_to`)
   and in game (Task 9, step 2).
2. **A missionary dies while preaching.** Expected: the spreader and the `tfe_mission_preaching` modifier go at once,
   not in the next yearly pulse (the pulse only sees living characters). Tested in Task 4 (death hook) and in game.
3. **The target turns before he arrives** (a neighbour's movement, or a conquest). Expected: he preaches anyway. The
   movement simply finds fewer pagans there, which is harmless. No test: accepted behaviour.
4. **A country changes faith while its missionary walks** (the conversion event). Expected: the missionary keeps his
   own faith and spreads his own movement, because the movement is chosen by the leader's religion, not the
   country's. Tested in Task 4 (`add_spreader` sits under a check on `scope:tfe_missionary`'s religion).
5. **Arians converting Nicene Romans under a Nicene owner.** Expected: never (`r0` ×0). Tested in Task 1.

---

### Task 1: The movements, their growth modifiers and the pagan triggers

**Files:**
- Create: `script/missionaries.py`
- Modify: `tools/pdx/objects.py` (add `LocationValue` after `CountryValue`, line ~95)
- Create: `tools/test_missionaries.py`
- Generated: `in_game/common/movements/tfe_christianisation.txt`,
  `main_menu/common/modifier_type_definitions/tfe_christianisation.txt`,
  `main_menu/common/modifier_icons/tfe_christianisation.txt`,
  `in_game/common/scripted_triggers/tfe_christianisation.txt`,
  `main_menu/localization/english/tfe_christianisation_l_english.yml`

**Interfaces:**
- Produces (module constants later tasks use): `NICENE = "orthodox"`, `ARIAN = "arianism"`,
  `MOVEMENT: dict[str, str]` (faith → movement key), `PAGANS: tuple[str, ...]`, `ARIAN_PAGANS`,
  `CONVERTS: dict[str, tuple[str, ...]]`, `FIELD: dict[str, str]` (faith → the location trigger
  `tfe_<faith>_mission_field`), `IN_REACH: dict[str, str]` (faith → the country trigger
  `tfe_<faith>_mission_in_reach`), `SEES`, `CULT_CENTRES`, `outputs()`.
- Produces (script): the scripted triggers `tfe_is_pagan_religion` (religion scope),
  `tfe_nicene_mission_field` / `tfe_arian_mission_field` (location), and `tfe_nicene_mission_in_reach` /
  `tfe_arian_mission_in_reach` (country). Also the modifier types `local_/national_tfe_<x>_movement_growth_modifier`.
- Produces (pdx): `pdx.objects.LocationValue`, a `ValueFx` whose `limit` opens `LocationTrig`.

- [ ] **Step 1: Write the failing tests** in `tools/test_missionaries.py`:

```python
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
sys.path.insert(0, str(ROOT / "tools"))
import missionaries as m  # noqa: E402
import borders as b  # noqa: E402

OUT = m.outputs()
MOV = OUT["in_game/common/movements/tfe_christianisation.txt"]
TRIG = OUT["in_game/common/scripted_triggers/tfe_christianisation.txt"]
LOC = OUT["main_menu/localization/english/tfe_christianisation_l_english.yml"]
TYPES = OUT["main_menu/common/modifier_type_definitions/tfe_christianisation.txt"]


def religions():
    files = [*(b.GAME / "in_game/common/religions").glob("*.txt"), ROOT / "in_game/common/religions/tfe_religions.txt"]
    return {k for p in files for k in re.findall(r"^(?:REPLACE:)?(\w+)\s*=\s*\{", p.read_text(encoding="utf-8-sig"), re.M)}


def locations():
    return set(re.findall(r"^(\w+)\s*=", (ROOT / "in_game/map_data/location_templates.txt").read_text(encoding="utf-8-sig"), re.M))


def test_every_faith_named_exists():
    known = religions()
    for faith, converts in m.CONVERTS.items():
        assert faith in known, faith
        assert not set(converts) - known, set(converts) - known


def test_each_movement_converts_its_list_and_the_rival_only_as_a_minority():
    for faith, key in m.MOVEMENT.items():
        names = [n.key for n in m.MOVEMENTS.find(None, None, inside=(key, "required_religions"))]
        assert names == list(m.CONVERTS[faith]), key
    assert m.ARIAN in m.CONVERTS[m.NICENE] and m.NICENE in m.CONVERTS[m.ARIAN]
    assert "celtic_paganism" not in m.CONVERTS[m.ARIAN]  # Gaul's Celts are left to the Nicenes


def test_every_pop_type_has_a_multiplier():
    """a movement skips pop types it does not list (movements/readme.txt)"""
    for key in m.MOVEMENT.values():
        listed = {n.val for n in m.MOVEMENTS.find("pop_type", None, inside=(key, "specific_pop_type_effect"))}
        assert listed == set(m.POP_TYPES), key


def test_arians_never_convert_nicenes_under_a_nicene_king():
    r0 = MOV.split("tfe_arian_movement", 1)[1].split("calc_interval_days", 1)[0]
    assert "multiply = 0" in r0 and "religion:orthodox" in r0 and "religion:arianism" in r0


def test_the_cult_centres_exist_and_resist():
    known = locations()
    for loc in m.CULT_CENTRES + m.SEES:
        assert loc in known, loc
    assert all(f"location:{c}" in MOV for c in m.CULT_CENTRES)


def test_growth_modifiers_have_a_type_and_a_name():
    for key in m.MOVEMENT.values():
        for scope in ("local", "national"):
            mod = f"{scope}_{key}_growth_modifier"
            assert f"{mod} = {{" in TYPES, mod
            assert f"MODIFIER_TYPE_NAME_{mod}:" in LOC, mod


def test_the_pagan_trigger_lists_every_pagan():
    for faith in m.PAGANS:
        assert f"religion:{faith}" in TRIG, faith
```

- [ ] **Step 2: Run them, expect an import failure.** Run:
  `uv run --no-project --with numpy --with pytest --with pillow --with shapely --with pyright python -m pytest -q tools/test_missionaries.py`.
  Expected: `ModuleNotFoundError: No module named 'missionaries'`.

- [ ] **Step 3: Add `LocationValue`** to `tools/pdx/objects.py`, right after `class CountryValue`, and add
  `LocationTrig` to its `from .api import ...` line:

```python
class LocationValue(ValueFx):
    """a value block whose root is a location (a movement's r0 and map_color): limit opens LocationTrig."""

    def limit(self) -> ContextManager[LocationTrig]:
        return self._open("limit", LocationTrig)

    def if_(self) -> ContextManager["LocationValue"]:
        return self._open("if", LocationValue)

    def else_if(self) -> ContextManager["LocationValue"]:
        return self._open("else_if", LocationValue)

    def else_(self) -> ContextManager["LocationValue"]:
        return self._open("else", LocationValue)
```

- [ ] **Step 4: Write `script/missionaries.py`** (the module docstring, constants, triggers and movements; later
  tasks add to it):

```python
"""The Christianisation of Europe: Nicene and Arian movements (vanilla's movement engine, the Reformation's) carried by
saints and missionaries who walk to a pagan location and preach there. Spec: docs/specs/2026-10-05-christianisation-design.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryTrig, LocationTrig, ReligionTrig
from pdx.core import Q
from pdx.objects import Doc, LocationValue
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
FIELD = {f: f"tfe_{MOVEMENT[f].removeprefix('tfe_').removesuffix('_movement')}_mission_field" for f in MOVEMENT}
IN_REACH = {f: f"tfe_{MOVEMENT[f].removeprefix('tfe_').removesuffix('_movement')}_mission_in_reach" for f in MOVEMENT}
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
# the temples that held out (tools/religions.txt): Carrhae, Heliopolis, the Marneion, Philae, the Mani, Athens
CULT_CENTRES = ("harran", "baalbek", "gaza", "aswan", "athens")
CULT_PROVINCES = ("laconia_province",)
R0 = {NICENE: (0, 0.012), ARIAN: (0, 0.010)}  # vanilla's Lutherans run 0.002 to 0.03; tuned in game (Task 9)
SPREADER_INFECTION = 0.05  # a preaching missionary, as Luther
LOCAL_GROWTH = {"tfe_mission_preaching": 0.5}


def triggers():
    d = Defs()
    d.note("TFE: the Christianisation of Europe. Written from script/missionaries.py.")
    with d.trigger("tfe_is_pagan_religion", ReligionTrig) as t, t.or_() as o:
        for faith in PAGANS:
            o.compare("this", "=", f"religion:{faith}")
    for faith in MOVEMENT:
        d.note(f"a location the {NAME[faith]} missionaries would preach in: its people mostly keep gods the "
               f"{MOVEMENT[faith]} converts")
        with d.trigger(FIELD[faith], LocationTrig) as t, t.go_dominant_religion(op="?=") as r, r.or_() as o:
            for pagan in (PAGANS if faith == NICENE else ARIAN_PAGANS):
                o.compare("this", "=", f"religion:{pagan}")
        d.note("a field the country owns or borders")
        with d.trigger(IN_REACH[faith], CountryTrig) as t, t.any_owned_location() as loc, loc.or_() as o:
            o._call(FIELD[faith], True)
            with o.any_neighbor_location() as n:
                n._call(FIELD[faith], True)
    return d


def r0(v: LocationValue, faith: str):
    lo, hi = R0[faith]
    v.raw(f"value = {{ {lo} {hi} }}")  # GAP: no random-range value binding
    with v.if_() as root:
        root.limit(lambda t: t.exists("root"))
        if faith == ARIAN:
            root.note("Nicene Romans turn Arian only under an Arian king (Huneric's Africa)")
            with root.if_() as i:
                with i.limit() as t:
                    t.compare("dominant_religion", "?=", f"religion:{NICENE}")
                    t.not_(lambda n: n.compare("owner.religion", "?=", f"religion:{ARIAN}"))
                i.multiply(0)
        for cond, factor, why in factors(faith):
            root.note(why)
            with root.if_() as i:
                i.limit(cond)
                i.multiply(factor)


def factors(faith: str):
    """(condition, multiplier, why) for r0, applied one after another"""
    yield (lambda t: t.compare("location_rank", "?=", "location_rank:town"), 1.5 if faith == NICENE else 1.1,
           "a town hears the preacher first")
    yield (lambda t: t.compare("location_rank", "?=", "location_rank:city"), 2 if faith == NICENE else 1.2,
           "and a city more")
    yield (lambda t: t.compare("owner.religion", "?=", f"religion:{faith}"), 1.5, "a king of the faith")
    yield (lambda t: t.any_neighbor_location(lambda n: n.compare("dominant_religion", "?=", f"religion:{faith}")),
           1.25, "a believing neighbour")
    if faith == NICENE:
        yield (lambda t: see(t), 1.5, "a bishop's see")
    yield (lambda t: t.link("owner", CountryTrig, lambda o: o.link("religion", ReligionTrig,
                                                                    lambda r: r.tfe_is_pagan_religion(True)), op="?="),
           0.5, "a pagan king protects the old gods")
    yield (lambda t: cult_centre(t), 0.3, "a great temple holds out while its people keep the gods")


def see(t: LocationTrig):
    with t.or_() as o:
        for loc in SEES:
            o.compare("this", "=", f"location:{loc}")


def cult_centre(t: LocationTrig):
    t.go_dominant_religion(op="?=", body=lambda r: r.tfe_is_pagan_religion(True))
    with t.or_() as o:
        for loc in CULT_CENTRES:
            o.compare("this", "=", f"location:{loc}")
        for prov in CULT_PROVINCES:
            o.compare("province", "=", f"province:{prov}")


def movement(doc: Doc, faith: str):
    key = MOVEMENT[faith]
    with doc.entry(key) as e:
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
        e.raw("calc_interval_days = { 20 40 }")  # GAP: no random-range value
        with e.block("required_religions") as rr:
            for x in CONVERTS[faith]:
                rr._call(x)
        e.field("development", "positive")
        e.field("literacy", "positive")
        e.field("local_control", "neutral")
        e.field("pop_satisfaction", "negative")
        for pop_type, mult in POP_EFFECTS[faith].items():
            e.data("specific_pop_type_effect", pop_type=pop_type, multiplier=mult)
        rival = ARIAN if faith == NICENE else NICENE
        e.data("specific_pop_type_effect", religion=rival, multiplier=RIVAL_EFFECT[faith])
        e.data("location_spread_threshold", value=0.05)
        with e.effects("map_color", LocationValue) as v:
            with v.if_() as i:
                i.limit(lambda t: t.compare(Q(f"religion_percentage(religion:{faith})"), "=", 0))
                i.value("define:NMapColors|MAP_COLOR_NULL")
            with v.else_if() as i:
                i.limit(lambda t: t.compare("dominant_religion", "=", f"religion:{faith}"))
                i.value("define:NMapColors|MAP_COLOR_HIGH")
            with v.else_if() as i:
                i.limit(lambda t: t.compare(Q(f"religion_percentage(religion:{faith})"), ">", 0.05))
                i.value("define:NMapColors|MAP_COLOR_MID")
            with v.else_() as i:
                i.value("define:NMapColors|MAP_COLOR_LOW")


def growth_types(types: Doc, icons: Doc, loc):
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
            loc.add(f"MODIFIER_TYPE_DESC_{mod}", f"How much the [ShowMovementDefinitionName('{key}')] [movement|e] grows {where}.")


def build():
    movements, types, icons = Doc(), Doc(), Doc()
    loc = movements.loc
    movements.note("TFE: the Christianisation of Europe (written by script/missionaries.py). Two rival movements convert\n"
                   "the pagans; a missionary who arrives where he was sent is pinned there as a spreader.")
    for faith in MOVEMENT:
        movement(movements, faith)
    types.note("TFE: the movements' growth modifiers (written by script/missionaries.py)")
    icons.note("TFE: the movements' growth modifiers (written by script/missionaries.py)")
    growth_types(types, icons, loc)
    return movements, types, icons


MOVEMENTS, TYPES, ICONS = build()


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/movements/tfe_christianisation.txt": MOVEMENTS.text(),
            "main_menu/common/modifier_type_definitions/tfe_christianisation.txt": TYPES.text(),
            "main_menu/common/modifier_icons/tfe_christianisation.txt": ICONS.text(),
            "in_game/common/scripted_triggers/tfe_christianisation.txt": triggers().text(),
            "main_menu/localization/english/tfe_christianisation_l_english.yml": MOVEMENTS.loc.text()}
```

  Where a trigger or link above has no typed binding (`go_dominant_religion(body=...)`,
  `any_neighbor_location(lambda ...)`), use the `with` form instead. Pyright says which. `o._call(name, True)` writes
  a scripted trigger the API does not know yet; replace it with the typed method once Step 6 has rerun `gen_api`.
  `LOCAL_GROWTH` is used in Task 4.

- [ ] **Step 5: Generate, then run the tests.** `python script/run.py` (with the `uv run` prefix), then the pytest
  line from Step 2. Expected: all 7 pass. On a mismatch, fix the script, not the test, unless the test contradicts
  the spec.
- [ ] **Step 6: Type the new triggers.** Run `EU5_DOCS=... python tools/pdx/gen_api.py`, replace the `o._call(...)` and
  `n._call(...)` calls with `o.tfe_nicene_mission_field(True)` and the like, then rerun `run.py`. Run pyright, the
  whole test suite and `tools/lint_script.py`. Expected: green. Lint knows nothing of the growth modifiers yet, but
  nothing uses them yet either.
- [ ] **Step 7: Commit.**
  `jj commit -m "Two creeds go out to the pagans: Nicene and Arian movements convert the old gods' faithful, town by town and court by court"`
  (with the body and Co-Authored-By trailer).

### Task 2: In game, probe the movement engine and record the modifiers

**Files:** none kept except the regenerated `tools/pdx/api.py`. Probe files live in `/tmp/tfe-probe/` and are
copied into `Documents/.../run/` by `eu5ctl run`.

This task answers four questions the rest of the plan rests on:

- **P1:** Does each `spawn_movement` make its own movement, or join one?
- **P2:** Does `add_spreader` at a location with no presence start the movement there?
- **P3:** Do pops really change religion?
- **P4:** Does `remove_spreader` on a dead character log an error?

- [ ] **Step 1: Point the playset at the workspace** (game stopped). Edit `playsets.json` so the
  `TFE (Claude test)` entry's path is `Z:/home/skuffed/tfe-christianity/`, keeping a copy of the original line.
- [ ] **Step 2: Start the game and write the docs.** `tools/eu5ctl.sh start`, `wait`, then New Game as `WRE` (click
  Italy on the map, move the mouse off the tooltip, Play as). `tools/eu5ctl.sh cmd "script_docs"`. Check that
  `Documents/.../docs/modifiers.log` lists `local_tfe_nicene_movement_growth_modifier`. Also look for a
  `tfe_christianisation` line in `logs/error.log` (expected: none).
- [ ] **Step 3: Probe P1 to P4.** Write `/tmp/tfe-probe/seed.txt` (BOM not needed for `run`):

```
location:rome = { spawn_movement = { movement_definition = movement_definition:tfe_nicene_movement supporters = { value = population multiply = 0.5 } } }
location:milano = { spawn_movement = { movement_definition = movement_definition:tfe_nicene_movement supporters = { value = population multiply = 0.5 } } }
set_global_variable = { name = tfe_probe_n value = 0 }
every_movement = { limit = { movement_type = movement_definition:tfe_nicene_movement } change_global_variable = { name = tfe_probe_n add = 1 } }
if = { limit = { global_var:tfe_probe_n = 1 } debug_log = "P1: one Nicene movement" }
else_if = { limit = { global_var:tfe_probe_n = 2 } debug_log = "P1: one movement per spawn" }
else = { debug_log = "P1: other count" }
c:WRE = { create_character = { first_name = name_martin religion = religion:orthodox culture = culture:gallo_roman estate = estate_type:clergy_estate age = 60 save_scope_as = probe_m } }
religion:orthodox = { ordered_movement_in_religion = { max = 1 order_by = { value = 1 } add_spreader = { character = scope:probe_m location = location:rennes } } }
c:WRE = { set_variable = { name = tfe_probe_m value = scope:probe_m } }
location:rennes = { if = { limit = { "religion_percentage(religion:orthodox)" > 0.01 } debug_log = "rennes start: over 1% Nicene" } else = { debug_log = "rennes start: under 1% Nicene" } }
```

  `tools/eu5ctl.sh run /tmp/tfe-probe/seed.txt`, then `tools/eu5ctl.sh log 20`. Unpause, set speed 5 (screenshot to
  confirm) and run two years. Then write `/tmp/tfe-probe/after.txt`:

```
location:rennes = { if = { limit = { "religion_percentage(religion:orthodox)" > 0.05 } debug_log = "P2: rennes over 5% Nicene" } else_if = { limit = { "religion_percentage(religion:orthodox)" > 0.01 } debug_log = "P2: rennes over 1%" } else = { debug_log = "P2: rennes unchanged" } }
location:rome = { every_neighbor_location = { if = { limit = { "religion_percentage(religion:orthodox)" > 0.5 } debug_log = "P3: a neighbour of Rome over half Nicene" } } }
c:WRE.var:tfe_probe_m = { save_scope_as = probe_m }
scope:probe_m = { kill_character_silently = yes }
religion:orthodox = { every_movement_in_religion = { remove_spreader = scope:probe_m } }
debug_log = "P4: removed a dead spreader"
```

  Run it and read the log, then `tools/eu5ctl.sh log 30 error.log` and look for a `remove_spreader` line. Open the
  Movements map mode and take a screenshot.
- [ ] **Step 4: Record the answers** at the top of this plan, under a heading "Probe results (Task 2)". Then pick the
  branch below:
  - **P1 one per spawn:** nothing changes. `add_spreader` goes through `ordered_movement_in_religion` with `max = 1`,
    which picks one of them. That is harmless, because the spreader's location is what counts.
  - **P2 unchanged** (a spreader cannot start the movement where it is absent): in Task 4's `tfe_preach_effect`,
    first `spawn_movement` at the destination with `supporters = { value = population multiply = 0.01 }`, then
    `add_spreader`. Write it into Task 4's code before starting Task 4.
  - **P3 no neighbour moved:** raise `R0` tenfold for the observer run, then tune it down in Task 9.
  - **P4 error:** in Task 4's death hook, call `remove_spreader` before the character is gone. That means the
    `on_character_death` hook, not the yearly pulse. Note the error text.
- [ ] **Step 5: Stop the game and type the modifiers.** `tools/eu5ctl.sh stop`. Then
  `EU5_DOCS=... python tools/pdx/gen_api.py`, then the full test suite and pyright. Expected: green. `api.py`'s
  `ModifierKeys` now has the four growth keys.
- [ ] **Step 6: Commit** `tools/pdx/api.py` and the probe results:
  `jj commit -m "The engine is sounded before the missionaries set out: probe results for spreaders, and the growth modifiers typed"`.

### Task 3: Seed the movements on day one

**Files:**
- Modify: `script/missionaries.py`
- Generated: `in_game/common/on_action/tfe_christianisation.txt`
- Test: `tools/test_missionaries.py`

**Interfaces:**
- Consumes: `SEES`, `MOVEMENT`, `NICENE`, `ARIAN` (Task 1).
- Produces: `ARIAN_SEEDS = ("VIS", "GEP", "RUG", "SCR", "HAS")`, and `pulses() -> Defs`, which Tasks 4, 5 and 7
  extend. It hooks `on_game_start` to `tfe_on_start_christianisation` and `yearly_country_pulse` to
  `tfe_on_christianisation_pulse`.

- [ ] **Step 1: Write the failing tests:**

```python
PULSE = OUT["in_game/common/on_action/tfe_christianisation.txt"]


def test_every_see_is_seeded_with_its_own_believers():
    start = m.PULSES.find(None, None, inside=("tfe_on_start_christianisation", "effect"))
    text = PULSE.split("tfe_on_start_christianisation", 1)[1]
    for loc in m.SEES:
        assert f"location:{loc}" in text, loc
    assert "religion_percentage(religion:orthodox)" in text and start


def test_the_arian_peoples_are_seeded_in_their_capitals():
    text = PULSE.split("tfe_on_start_christianisation", 1)[1]
    for tag in m.ARIAN_SEEDS:
        assert f"c:{tag}" in text, tag
```

- [ ] **Step 2: Run them, expect a KeyError** on the missing on_action file.
- [ ] **Step 3: Implement** in `script/missionaries.py`:

```python
ARIAN_SEEDS = ("VIS", "GEP", "RUG", "SCR", "HAS")  # the Arian peoples of 395 (tools/religions.txt)


def seed(loc: LocationFx, faith: str):
    """the movement starts with the believers already there, so nothing converts on day one"""
    loc.spawn_movement(movement_definition=f"movement_definition:{MOVEMENT[faith]}",
                       supporters={"value": "population", "multiply": Q(f"religion_percentage(religion:{faith})")})


def pulses():
    d = Defs()
    d.note("TFE: the Christianisation of Europe (written by script/missionaries.py). Day one seeds the movements; a yearly\n"
           "pulse sends saints and missionaries and ends their missions.")
    d.hook("on_game_start", "tfe_on_start_christianisation")
    with d.on_action("tfe_on_start_christianisation") as a, a.effect() as e:
        e.note("the Nicene sees")
        for loc in SEES:
            with e.link(f"location:{loc}", LocationFx) as l:
                seed(l, NICENE)
        e.note("the Arian peoples, at their capitals")
        for tag in ARIAN_SEEDS:
            with e.link(f"c:{tag}", CountryFx, op="?=") as c, c.go_capital(op="?=") as cap:
                seed(cap, ARIAN)
    return d
```

  Add `LocationFx, CountryFx` to the imports. Set `PULSES = pulses()` beside `MOVEMENTS`, and add
  `"in_game/common/on_action/tfe_christianisation.txt": PULSES.text()` to `outputs()`. `multiply = "religion_..."`
  must render without quotes inside a value block. If `Q` quotes it, pass the plain string (as in Step 1's test).
- [ ] **Step 4: Run run.py, pytest, pyright and lint.** Expected: green.
- [ ] **Step 5: Commit:**
  `jj commit -m "On the first day the sees and the Gothic courts hold their own: the movements start from the believers already there"`.

### Task 4: The missionary's walk, his preaching and its end

**Files:**
- Modify: `script/missionaries.py`
- Generated: `in_game/common/expedition_types/tfe_missionaries.txt`,
  `in_game/common/scripted_effects/tfe_christianisation.txt`,
  `main_menu/common/static_modifiers/tfe_christianisation.txt`, plus additions to the on_action file and the loc
- Test: `tools/test_missionaries.py`

**Interfaces:**
- Consumes: `MOVEMENT`, `FIELD`, `PULSES` (Tasks 1 and 3).
- Produces the scripted effects every sender uses. Each runs in country scope.
  - `tfe_send_missionary_effect` reads `scope:tfe_missionary` (a character), `scope:tfe_mission_from` and
    `scope:tfe_mission_to` (locations). It sets the country variables `tfe_mission_from`/`tfe_mission_to` and starts
    the expedition.
  - `tfe_preach_effect` reads `scope:tfe_missionary` and `scope:tfe_mission_at`.
  - `tfe_end_mission_effect` reads `scope:tfe_missionary`.
- Produces in Python: `EXPEDITION_TYPE = "tfe_missionary"`, the static modifier `tfe_mission_preaching`, and the
  helper `collect_near(fx, frm, faith, list_name)`.
- The character variables are `tfe_mission_at` (location), `tfe_preaching` (timed), `tfe_missions` (count) and
  `tfe_missionary` (flag).

- [ ] **Step 1: Write the failing tests:**

```python
EXP = OUT["in_game/common/expedition_types/tfe_missionaries.txt"]
FX = OUT["in_game/common/scripted_effects/tfe_christianisation.txt"]


def test_the_missionary_walks_overland_one_at_a_time():
    for field in ("travel_mode = land", "dynamic_first_waypoint = yes", "origin = none", "unique = yes", "ai = no"):
        assert field in EXP, field


def test_he_preaches_on_arrival_and_even_when_the_road_fails():
    for block in ("on_end", "on_fail"):
        assert m.EXPEDITION.find("tfe_preach_effect", None, inside=(m.EXPEDITION_TYPE, block)), block
    on_fail = EXP.split("on_fail", 1)[1]
    assert "has_variable = tfe_mission_to" in on_fail  # the popup's dry run finds no destination


def test_the_spreader_follows_the_missionarys_own_faith():
    preach = FX.split("tfe_preach_effect", 1)[1].split("tfe_end_mission_effect", 1)[0]
    for faith in m.MOVEMENT:
        assert f"religion:{faith}" in preach
    assert "add_spreader" in preach and "scope:tfe_missionary" in preach


def test_a_dead_missionary_stops_preaching_at_once():
    assert "on_character_death" in PULSE and "tfe_on_missionary_dies" in PULSE
    dies = PULSE.split("tfe_on_missionary_dies = {", 1)[1]
    assert "tfe_end_mission_effect" in dies


def test_a_mission_ends_by_removing_the_spreader_and_the_modifier():
    end = FX.split("tfe_end_mission_effect", 1)[1]
    assert "remove_spreader = scope:tfe_missionary" in end and "remove_location_modifier = tfe_mission_preaching" in end


def test_at_most_three_missions():
    assert f"var:tfe_missions < {m.MAX_MISSIONS}" in PULSE
```

- [ ] **Step 2: Run them, expect a KeyError** on the expedition file.
- [ ] **Step 3: Implement.** Add to `script/missionaries.py` (imports: `CharacterFx, CharacterTrig, ExpeditionFx,
  LocationFx, ReligionFx`):

```python
EXPEDITION_TYPE = "tfe_missionary"
TRAVEL_SPEED = 0.5  # a man on foot, faster than a people with wagons (0.25)
PREACH_YEARS = (5, 7, 10)
MAX_MISSIONS = 3
MOVE_ON_CHANCE = 50
NEAR_RINGS = 3  # "the next pagan location within 3 locations"


def spreader(fx: CountryFx, add: bool):
    """the missionary's own faith picks the movement: a country that changed faith while he walked does not change his"""
    for faith in MOVEMENT:
        with fx.if_() as i:
            i.limit(lambda t, f=faith: t.link("scope:tfe_missionary", CharacterTrig,
                                              lambda c: c.compare("religion", "=", f"religion:{f}")))
            with i.link(f"religion:{faith}", ReligionFx) as r:
                if add:
                    with r.ordered_movement_in_religion(max=1, order_by={"value": 1}) as mv:
                        mv.add_spreader(character="scope:tfe_missionary", location="scope:tfe_mission_at")
                else:
                    with r.every_movement_in_religion() as mv:
                        mv.remove_spreader("scope:tfe_missionary")


def effects():
    d = Defs()
    d.note("TFE: missionaries (written by script/missionaries.py). Country scope. The caller saves scope:tfe_missionary\n"
           "and the locations each effect names.")
    with d.effect("tfe_send_missionary_effect", CountryFx) as fx:
        fx.set_variable(name="tfe_mission_from", value="scope:tfe_mission_from")
        fx.set_variable(name="tfe_mission_to", value="scope:tfe_mission_to")
        with fx.link("scope:tfe_missionary", CharacterFx) as c:
            c.set_variable("tfe_missionary")
        fx.start_expedition(type=f"expedition_type:{EXPEDITION_TYPE}", leader="scope:tfe_missionary")
    d.note("he arrives: pinned to the place as the movement's spreader, for 5 to 10 years or until he dies")
    with d.effect("tfe_preach_effect", CountryFx) as fx:
        with fx.link("scope:tfe_missionary", CharacterFx) as c:
            c.set_variable(name="tfe_mission_at", value="scope:tfe_mission_at")
            with c.if_() as i:
                i.limit(lambda t: t.has_variable("tfe_missions"))
                i.change_variable(name="tfe_missions", add=1)
            with c.else_() as i:
                i.set_variable(name="tfe_missions", value=1)
            with c.random_list() as r:
                for years in PREACH_YEARS:
                    with r.weight(1) as w:
                        w.set_variable(name="tfe_preaching", years=years)
        with fx.link("scope:tfe_mission_at", LocationFx) as loc:
            loc.add_location_modifier(modifier="tfe_mission_preaching", years=max(PREACH_YEARS))
        spreader(fx, add=True)
    with d.effect("tfe_end_mission_effect", CountryFx) as fx:
        with fx.link("scope:tfe_missionary.var:tfe_mission_at", LocationFx, op="?=") as loc:
            loc.remove_location_modifier("tfe_mission_preaching")
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
    doc.loc.add(f"{EXPEDITION_TYPE}_desc", "A man of God on the road with a staff and a gospel book, bound for people "
                "who still sacrifice to the old gods.")
    doc.note("GAP: no expedition-type builder (doc.entry); a copy of tfe_wandering_people (expedition_types/tfe_peoples.txt)")
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
                i.limit(lambda t: t._call(FIELD[faith], True))  # typed after gen_api: t.tfe_nicene_mission_field(True)
                i.add_to_temporary_list(name)
            if depth > 1:
                ring(n, depth - 1)
    with fx.link(frm, LocationFx) as loc:
        ring(loc, NEAR_RINGS)


def end_missions(d: Defs):
    """the yearly pulse: a mission whose time is up ends; the missionary may walk on, else he dies in his see"""
    with d.on_action("tfe_on_missions_end") as a, a.effect(CountryFx) as e:
        with e.every_character() as c:
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
                            with t.link("scope:tfe_missionary", CharacterTrig) as m:
                                m.compare("religion", "=", f"religion:{faith}")
                                m.var("tfe_missions", "<", MAX_MISSIONS)
                        with i.random(MOVE_ON_CHANCE) as go:
                            collect_near(go, "scope:tfe_mission_from", faith, "tfe_near_fields")
                            with go.ordered_in_list(LocationFx, list="tfe_near_fields", order_by="population") as to:
                                to.save_scope_as("tfe_mission_to")
                            with go.if_() as s:
                                s.limit(lambda t: t.exists("scope:tfe_mission_to"))
                                s.tfe_send_missionary_effect(True)
                with r.if_() as i:
                    i.note("he did not walk on: he dies in his see (a made-for-the-road character must not crowd the court)")
                    i.limit(lambda t: t.not_(lambda n: n.exists("scope:tfe_mission_to")))
                    i.kill_character_silently("scope:tfe_missionary")
    d.hook("on_character_death", "tfe_on_missionary_dies")
    with d.on_action("tfe_on_missionary_dies") as a:
        with a.trigger(CountryTrig) as t, t.link("scope:target", CharacterTrig) as c:
            c.has_variable("tfe_mission_at")
        with a.effect(CountryFx) as e:
            with e.link("scope:target", CharacterFx) as c:
                c.save_scope_as("tfe_missionary")
            e.tfe_end_mission_effect(True)
```

  Tidy as you go:
  - The test wants the literal `var:tfe_missions < 3`, so make sure `m.var("tfe_missions", "<", MAX_MISSIONS)`
    renders it.
  - Add `ExpeditionTrig` to the imports, or use `t.exists("scope:expedition.expedition_leader")` if pyright rejects
    the link.

  Then wire it up:
  - Hook the yearly pulse inside `pulses()`: `d.hook("yearly_country_pulse", "tfe_on_missions_end")`, then call
    `end_missions(d)`.
  - Add the static modifier in `build()` (a fourth Doc, `mods`, with `mods.loc = loc`):
    `mods.modifier("tfe_mission_preaching", category="location", local_tfe_nicene_movement_growth_modifier=0.5, local_tfe_arian_movement_growth_modifier=0.5)`.
    Add its loc, `STATIC_MODIFIER_NAME_tfe_mission_preaching` ("A Missionary Preaches") and
    `STATIC_MODIFIER_DESC_tfe_mission_preaching` ("A man of God has come to live among these people, and they come
    to hear him."). Remove the `LOCAL_GROWTH` constant, since the call above replaces it.
  - Make `EXPEDITION = Doc()` with `EXPEDITION.loc = loc` and call `expedition(EXPEDITION)`.
  - Add the three new files to `outputs()`:
    - `in_game/common/expedition_types/tfe_missionaries.txt`
    - `in_game/common/scripted_effects/tfe_christianisation.txt` (from `effects().text()`)
    - `main_menu/common/static_modifiers/tfe_christianisation.txt`
- [ ] **Step 4: Generate, gen_api, generate.** `run.py`, then `gen_api.py` (types the three new scripted effects),
  then replace each `x._call(...)`/`.tfe_*_effect(True)` that pyright flags with the typed call, then `run.py` again.
- [ ] **Step 5: Run pytest, pyright and lint.** Expected: green. Lint should report no unknown effect.
- [ ] **Step 6: Commit:**
  `jj commit -m "A man of God takes the road: missionaries walk to a pagan place, preach there for years, and walk on or die in their see"`.

### Task 5: Saints on their dates, and missionaries at random

**Files:**
- Modify: `script/missionaries.py`
- Test: `tools/test_missionaries.py`

**Interfaces:**
- Consumes: `tfe_send_missionary_effect`, `FIELD`, `IN_REACH`, `collect_near`, `pulses()` (Tasks 1, 3 and 4).
- Produces: `SAINTS: tuple[Saint, ...]`, where `Saint` is a `NamedTuple` with fields `key: str`, `name: str`,
  `faith: str`, `year: int`, `start: str`, `targets: tuple[str, ...]`, `age: int`, and `wait: int = 10`. A target is
  a location key, an `*_area` key or an `*_region` key. Also produces `region_of(location) -> str`, read from
  vanilla's `in_game/map_data/definitions.txt`.

- [ ] **Step 1: Write the failing tests:**

```python
def areas_and_regions():
    t = (b.GAME / "in_game/map_data/definitions.txt").read_text(encoding="utf-8-sig")
    return set(re.findall(r"(\w+_(?:area|region))\s*=\s*\{", t))


def test_every_saint_starts_and_ends_somewhere_real():
    locs, ar = locations(), areas_and_regions()
    for s in m.SAINTS:
        assert s.start in locs, s.key
        for target in s.targets:
            assert target in (ar if target.endswith(("_area", "_region")) else locs), (s.key, target)
        assert s.faith in m.MOVEMENT


def test_every_saint_has_a_name():
    for s in m.SAINTS:
        assert f"name_{s.key}" in LOC or s.key in m.VANILLA_NAMES, s.key


def test_each_saint_goes_once_within_his_window():
    for s in m.SAINTS:
        assert f"tfe_saint_{s.key}" in PULSE
        assert f"{s.year + s.wait}.1.1" in PULSE


def test_martin_goes_in_the_first_year():
    assert m.SAINTS[0].key == "martin" and m.SAINTS[0].year == 395


def test_random_missionaries_are_rarer_without_the_edict():
    rnd = PULSE.split("tfe_on_random_missionary", 1)[1]
    assert f"chance = {m.RANDOM_CHANCE}" in rnd and f"chance = {m.RANDOM_CHANCE + m.TEMPLES_BONUS}" in rnd
```

- [ ] **Step 2: Run them, expect `AttributeError: SAINTS`.**
- [ ] **Step 3: Implement:**

```python
from typing import NamedTuple


class Saint(NamedTuple):
    key: str
    name: str
    faith: str
    year: int
    start: str
    targets: tuple[str, ...]
    age: int
    wait: int = 10


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
TEMPLES = "tfe_temples_closed"  # Close the Temples' country modifier (Task 6)


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
    flag = f"tfe_saint_{s.key}"
    with fx.if_() as i:
        with i.limit() as t:
            t.current_date(f"{s.year}.1.1", op=">=")
            t.current_date(f"{s.year + s.wait}.1.1", op="<")
            t.not_(lambda n: n.has_global_variable(flag))
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


def random_missionary(d: Defs):
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
                                with f.random_in_list(LocationFx, list="tfe_reach_fields", weight={"base": 1, "modifier": {"add": "population"}}) as to:
                                    to.save_scope_as("tfe_mission_to")
                                new_missionary(f)


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
```

  Wire it up in `pulses()`:
  - `d.hook("yearly_country_pulse", "tfe_on_saints", "tfe_on_random_missionary")` (the same `hook` call adds to the
    existing one).
  - A `tfe_on_saints` on_action whose trigger is `not has_variable tfe_mission_to` and whose effect calls
    `send_saint` for each of `SAINTS`.
  - `random_missionary(d)`.
  - In `build()`, add the loc for each saint not in `VANILLA_NAMES`: `loc.add(f"name_{s.key}", s.name)`.

  Add `functools`, `re`, `AreaFx` and `RegionFx` to the imports. Replace `_call(FIELD...)` with the typed trigger as
  in Task 1.
- [ ] **Step 4: Run run.py, pytest, pyright and lint.** Expected: green.
- [ ] **Step 5: Commit:**
  `jj commit -m "Martin leaves Tours for the Gaulish villages: saints set out on their dates, and every Christian court may send a priest of its own"`.

### Task 6: Sponsor a Mission and Close the Temples

**Files:**
- Modify: `script/missionaries.py`
- Generated: `in_game/common/decisions/tfe_christianisation.txt`,
  `in_game/common/decision_categories/tfe_christianisation.txt`,
  `in_game/common/script_values/tfe_christianisation.txt`, plus static modifiers and loc
- Test: `tools/test_missionaries.py`

**Interfaces:**
- Consumes: `fields_in_reach`, `new_missionary`, `IN_REACH`, `TEMPLES`, `PAGANS` (Tasks 1 and 5).
- Produces: the decisions `tfe_sponsor_mission` and `tfe_close_the_temples`; the category `tfe_the_faith`; the script
  values `tfe_mission_price` and `tfe_mission_price_twice`; and the country modifier `tfe_temples_closed`, which the
  random-missionary pulse already reads.

- [ ] **Step 1: Write the failing tests:**

```python
DEC = OUT["in_game/common/decisions/tfe_christianisation.txt"]


def test_a_mission_costs_months_of_income_with_a_floor():
    vals = OUT["in_game/common/script_values/tfe_christianisation.txt"]
    assert f"multiply = {m.MISSION_INCOME_MONTHS}" in vals and f"min = {m.MISSION_MIN_GOLD}" in vals


def test_sponsor_a_mission_has_a_cooldown_and_waits_for_the_last_missionary():
    allow = DEC.split("tfe_sponsor_mission", 1)[1].split("ai_will_do", 1)[0]
    assert "tfe_mission_sponsored" in allow and "tfe_mission_to" in allow
    assert f"years = {m.MISSION_COOLDOWN}" in DEC


def test_close_the_temples_is_for_a_nicene_rome():
    pot = DEC.split("tfe_close_the_temples", 1)[1].split("allow", 1)[0]
    assert "tfe_is_roman_empire = yes" in pot and "religion:orthodox" in pot


def test_close_the_temples_angers_the_pagans_and_can_raise_them():
    eff = DEC.split("tfe_close_the_temples", 1)[1]
    assert "add_pop_satisfaction" in eff and f"chance = {m.RISING_CHANCE}" in eff
```

- [ ] **Step 2: Run them, expect a KeyError.**
- [ ] **Step 3: Implement:**

```python
CATEGORY = "tfe_the_faith"
EXT = "gfx/interface/illustrations/event/backgrounds/exterior/"
INT = "gfx/interface/illustrations/event/backgrounds/interior/"
MISSION_INCOME_MONTHS = 6
MISSION_MIN_GOLD = 50
MISSION_COOLDOWN = 5
TEMPLES_YEARS = 10
RISING_CHANCE = 25


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
                i.limit(lambda t: t.gold("tfe_mission_price_twice", op=">="))
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
```

  Wire it up:
  - In `build()`, add a `decisions` Doc and a `cats` Doc, both sharing `loc`.
  - `cats.decision_category(CATEGORY, title="The Faith", sort_order=1)`.
  - Call `sponsor(decisions)` and `close_the_temples(decisions)`.
  - `mods.modifier(TEMPLES, category="country", national_tfe_nicene_movement_growth_modifier=0.5)`.
  - Add the loc:

| Key | Text |
|---|---|
| `STATIC_MODIFIER_NAME_tfe_temples_closed` | "The Temples Closed" |
| `STATIC_MODIFIER_DESC_tfe_temples_closed` | "The edicts against the sacrifices are enforced in our lands." |
| `tfe_mission_price_tt` | "We have the gold for a mission ([tfe_mission_price])" |
| `tfe_mission_on_the_road_tt` | "None of our missionaries is still on the road" |
| `tfe_mission_sponsored_tt` | "We have not sponsored a mission in the last 5 years" |
| `tfe_temples_already_closed_tt` | "The temples are not already closed" |
| `tfe_sponsor_mission_tt` | "A missionary of our faith sets out for the most populous pagan place in or beside our lands, and preaches there for 5 to 10 years." |
| `tfe_close_the_temples_tt` | "For 10 years our faith spreads half again as fast and more of our priests go out to the pagans. Every pagan in our lands loses 10% satisfaction, and in a quarter of the pagan places they lose 25% more." |

  - Add the three new files to `outputs()`.
  - Add `PopTrig` to the imports, and replace `_call` with the typed trigger as before.
- [ ] **Step 4: Run run.py, pytest, pyright and lint.** Expected: green.
- [ ] **Step 5: Commit:**
  `jj commit -m "The emperor's edicts reach the villages: rulers can sponsor a mission, and a Nicene Rome can close the temples at the risk of a pagan rising"`.

### Task 7: A pagan king follows his people

**Files:**
- Modify: `script/missionaries.py`
- Generated: `in_game/events/tfe_conversion.txt`, plus on_action, script value, static modifier and loc additions
- Test: `tools/test_missionaries.py`

**Interfaces:**
- Consumes: `pulses()`, `tfe_is_pagan_religion`, `values()`, `MOVEMENT` (Tasks 1, 3 and 6).
- Produces: the event `tfe_conversion.1`, the script value `tfe_christian_share`, and the static modifiers
  `tfe_new_faith_resented` and `tfe_old_gods_kept`.

- [ ] **Step 1: Write the failing tests:**

```python
EVT = OUT["in_game/events/tfe_conversion.txt"]


def test_a_pagan_king_is_asked_once_a_decade_when_his_people_have_turned():
    pulse = PULSE.split("tfe_on_pagan_king", 1)[1]
    assert "tfe_christian_share > 0.5" in pulse and "tfe_conversion_asked" in pulse
    assert f"years = {m.CONVERSION_EVERY}" in pulse


def test_taking_the_faith_changes_the_king_too():
    a = EVT.split("option", 1)[1].split("option", 1)[0]
    assert "change_religion = scope:tfe_new_faith" in a and "change_religion_for_ruler_and_family" in a


def test_holding_out_speeds_the_drift():
    assert "tfe_old_gods_kept" in EVT
    mods = OUT["main_menu/common/static_modifiers/tfe_christianisation.txt"]
    kept = mods.split("tfe_old_gods_kept", 1)[1]
    assert "national_tfe_nicene_movement_growth_modifier" in kept and "national_tfe_arian_movement_growth_modifier" in kept
```

- [ ] **Step 2: Run them, expect a KeyError.**
- [ ] **Step 3: Implement:**

```python
CONVERSION_EVERY = 10


def conversion_event():
    doc = Doc()
    doc.namespace("tfe_conversion")
    doc.note("A pagan king whose people have mostly turned Christian (on_action/tfe_christianisation.txt asks once a decade)")
    with doc.event(1, type="country_event", title="The King and the Cross", outcome="neutral",
                   desc="Most of our people now pray to the Christ, in our villages as in our towns, and their priests "
                        "ask why the king still sacrifices to gods his people have left. Clovis's bishops would say a "
                        "king who kneels at the font wins a kingdom. Our own priests say a king who betrays the gods "
                        "loses his luck.",
                   image=INT + "byz_clergy_interior.dds") as e:
        with e.immediate() as i:
            i.note("the larger of the two churches; the scope is made here, not passed in (a saved scope can go missing)")
            with i.if_() as f:
                f.limit(lambda t: t.compare(Q("religion_percentage_in_country(religion:orthodox)"), ">=",
                                            Q("religion_percentage_in_country(religion:arianism)")))
                f.link("religion:orthodox", ReligionFx, lambda r: r.save_scope_as("tfe_new_faith"))
            with i.else_() as f:
                f.link("religion:arianism", ReligionFx, lambda r: r.save_scope_as("tfe_new_faith"))
        with e.option("a", text="Kneel at the font.") as o:
            o.change_religion("scope:tfe_new_faith")
            o.change_religion_for_ruler_and_family(country="root", religion="scope:tfe_new_faith")
            o.add_stability(10)
            o.add_country_modifier(modifier="tfe_new_faith_resented", years=CONVERSION_EVERY)
            with o.ai_chance_block(1) as ai, ai.modifier(3) as t:
                t.compare("tfe_christian_share", ">", 0.7)
        with e.option("b", text="We keep faith with the gods of our fathers.") as o:
            o.add_country_modifier(modifier="tfe_old_gods_kept", years=CONVERSION_EVERY)
            o.ai_chance(1)
    return doc


def pagan_king(d: Defs):
    d.hook("yearly_country_pulse", "tfe_on_pagan_king")
    with d.on_action("tfe_on_pagan_king") as a:
        with a.trigger(CountryTrig) as t:
            t.link("religion", ReligionTrig, lambda r: r.tfe_is_pagan_religion(True))
            t.compare("tfe_christian_share", ">", 0.5)
            t.not_(lambda n: n.has_variable("tfe_conversion_asked"))
        with a.effect(CountryFx) as e:
            e.set_variable(name="tfe_conversion_asked", years=CONVERSION_EVERY)
            e.trigger_event_non_silently("tfe_conversion.1")
```

  Wire it up:
  - Call `pagan_king(d)` in `pulses()`.
  - In `values()`, add `tfe_christian_share`: `value = "religion_percentage_in_country(religion:orthodox)"` and
    `add = "religion_percentage_in_country(religion:arianism)"`. Quote these with `Q` only if the linter or game wants
    it; vanilla writes `"culture_percentage_in_country(...)"` quoted, so quote them.
  - Add the static modifiers in `build()`:
    - `mods.modifier("tfe_new_faith_resented", category="country", nobles_estate_target_satisfaction=-0.1)`
    - `mods.modifier("tfe_old_gods_kept", category="country", clergy_estate_target_satisfaction=0.1, national_tfe_nicene_movement_growth_modifier=0.25, national_tfe_arian_movement_growth_modifier=0.25)`
    - their `STATIC_MODIFIER_NAME_`/`DESC_` loc: "The Old Gods Abandoned" (the nobles who kept the sacrifices resent
      it) and "The Old Gods Kept" (the priests rejoice, but the people drift to the Christ all the same).
  - Give the event doc `loc` (`EVENT.loc = loc`) and add `in_game/events/tfe_conversion.txt` to `outputs()`.
- [ ] **Step 4: Run run.py, pytest, pyright and lint.** `lint_refs` checks that the event's title, desc and option loc
  exist. Expected: green.
- [ ] **Step 5: Commit:**
  `jj commit -m "A king whose people have taken the cross must choose: kneel at the font like Clovis, or keep faith with the old gods"`.

### Task 8: Docs, index and the spec's corrections

**Files:**
- Modify: `RoadMap.html` (a new item `#30` under Tier 2, after `#9`), `docs/specs/2026-10-05-christianisation-design.md`,
  `CLAUDE.md` (the list of ported scripts in "Script written in Python"), `docs/INDEX.md` (regenerated)

- [ ] **Step 1: RoadMap.** After the `<li value="9">` item, add:
  `<li value="30"><strong>The Christianisation of Europe.</strong> <span class="built">✅ v1</span>
  (<code>script/missionaries.py</code>): Nicene and Arian movements convert the pagans; saints (Martin, Nicetas,
  Victricius, Porphyry, Germanus, Patrick, Severinus, Sigesar, Ajax) and random missionaries walk to a pagan place and
  preach there; Sponsor a Mission, Close the Temples; a pagan king whose people turned asks whether to follow.
  Later: pick a mission's target by hand; the councils (#8) fold the heresies in; #7's minority law steers the Arian
  movement.</li>`
- [ ] **Step 2: Spec.** Apply the nine "Changes from the spec" above to the spec's sections 1–4. Edit the lines the
  changes touch and leave the rest as written.
- [ ] **Step 3: CLAUDE.md.** In "Ported so far", add `missionaries.py` (the Christianisation: movements, missionaries,
  decisions and the conversion event).
- [ ] **Step 4: Index.** `python tools/gen_index.py` (with the `uv run` prefix).
- [ ] **Step 5: Full checks.** Run pytest (whole suite), pyright and `tools/lint_script.py`. Also run
  `tools/lint_script.py --vanilla` and confirm the hit count has not jumped because of `LocationValue` or the movement
  files. Expected: green.
- [ ] **Step 6: Commit:**
  `jj commit -m "The road map learns of the missions: RoadMap #30, the spec brought up to date, and the index"`.

### Task 9: In game, watch the Church win the countryside, then open the PR

**Files:** `script/missionaries.py` (tuning `R0` only), regenerated files. Screenshots and saves go to
`/home/skuffed/tfe-christianity-run/` (outside the repo).

- [ ] **Step 1: Day one.** The playset still points at the workspace (Task 2). Start a new game as `WRE` and open the
  Movements map mode. Expected: Nicene colour at the eleven sees and Arian colour at the five capitals. Take a
  screenshot.
- [ ] **Step 2: The missionary probe.** Write `/tmp/tfe-probe/mission.txt`:

```
c:WRE = {
	location:rennes = { save_scope_as = tfe_mission_to }
	capital = { save_scope_as = tfe_mission_from }
	create_character = { religion = religion:orthodox culture = culture:gallo_roman estate = estate_type:clergy_estate age = 35 save_scope_as = tfe_missionary }
	tfe_send_missionary_effect = yes
	set_variable = { name = tfe_probe_m value = scope:tfe_missionary }
}
```

  Run it and confirm the expedition shows in the Expeditions panel. Unpause at speed 5 (screenshot to confirm) until
  it arrives, then run
  `c:WRE.var:tfe_probe_m = { if = { limit = { has_variable = tfe_mission_at } debug_log = "preaching" } else = { debug_log = "not preaching" } }`.
  Expected: "preaching", Rennes carrying "A Missionary Preaches", and over the next years Rennes turning in the map
  mode.

  Then kill him through the console probe and check that the modifier is gone at once (the death hook). Do the same
  for an island target (`location:armagh` from `london`): he should preach on arrival though the land road fails.
- [ ] **Step 3: Saints.** Run one year. `tools/eu5ctl.sh log 50` and the Expeditions panel should show Martin on the
  road from Tours. Check with a probe: `if = { limit = { has_global_variable = tfe_saint_martin } debug_log = "martin went" }`.
- [ ] **Step 4: A pagan king.** Stop and start a new game as the Franks (`FRK`) through the lobby (not Observe: the
  observer trap). Use the console to convert most of their pops: run an effect that does `every_owned_location`,
  then `every_pop`, then `change_pop_religion` or `split_pop` with `fraction = 0.8` and `religion = religion:orthodox`
  (look up the effect name in `effects.log`). Wait one year at speed 5. Expected: `tfe_conversion.1` fires, and
  "Kneel at the font" makes the Franks Nicene.
- [ ] **Step 5: The observer run.** Start a new game, Observe, speed 5, and run to 500. At 400, 450 and 500, take a
  screenshot of the Movements map mode and save the game (`save tfe_christianisation_<year>` in the console).
  Compare the saves (plain text; see [[eu5-save-forensics]]) with the pacing table in the spec:
  - 450: Roman towns and Italy mostly Nicene, Gaul and Illyricum about half, the Goths' Germanic neighbours mostly
    Arian.
  - 500, on the way to 550: the countryside going Nicene.

  Use a short Python reader over the saves' pop blocks, written in `/tmp`, not committed. If the spread is too slow or
  too fast, change `R0` in `script/missionaries.py` (stop the game first), rerun `run.py` and repeat the run. Note
  any interesting emergent story (a Frankish king who kneeled, a rising) for the PR. Keep those saves.
- [ ] **Step 6: Errors.** `grep -n "tfe_" logs/error.log` filtered to `christianisation|missionar|conversion|mission_`.
  Expected: no lines. Fix any, and rerun the step they came from.
- [ ] **Step 7: Put the playset back** (game stopped): the `TFE (Claude test)` path back to
  `C:/users/steamuser/Documents/Paradox Interactive/Europa Universalis V/mod/TFE/`.
- [ ] **Step 8: Final checks and commit.** Run pytest, pyright and lint. If `R0` changed:
  `jj commit -m "The countryside turns at the pace of history: the movements' growth tuned against an observer run to 500"`.
- [ ] **Step 9: Push and open the PR.**
  - `jj git fetch`, then `jj rebase -b @ -d 1.4`. On a conflict in a generated file, take either side and rerun the
    generator. Rerun the tests.
  - `jj bookmark move christianisation --to @-`, `jj bookmark track christianisation --remote origin`, `jj git push`.
  - `gh pr create --repo iSkuffed/TFE --base 1.4 --head christianisation`. The body covers:
    - what it adds
    - the probe results (Task 2)
    - the in-game evidence (screenshots at 400/450/500, the conversion event, the island mission)
    - what was not tested
    - and ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

    Link the PR with the t3-code `link_pull_request` tool.
