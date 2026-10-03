# The Ages, and Peoples on the Road (RoadMap #14 and the migration follow-ups)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move vanilla's six ages onto 395-895 and make every advance, institution, unit and road read like that
world. Then put peoples on the road: Germanic settlers a king can invite, Slavic bands that drift west, and
remnant countries that stay behind when a host leaves.

**Architecture:** Vanilla stays the source of truth. Small Python generators read vanilla and write `REPLACE:`
blocks and loc for only the keys we change, so an EU5 patch is one `python script/run.py` and a test run. Most fixes
are loc renames in `replace/`. Cuts, moves and re-roots are `REPLACE:` copies of single advances, written from a
table. The new mechanics (settlers, Slavic bands, remnants) are typed Python in `script/`, like the rest of TFE.

**Tech Stack:** EU5 1.4 script; Python 3 generators (`script/*.py` with `outputs()`, `tools/pdx/` bindings,
`tools/lint_script.parse` + `pdx.core.from_entries` / `render` for round-tripping vanilla); pytest; pyright;
`tools/eu5ctl.sh` for in-game checks.

**Spec:** this plan carries the decisions made with iSkuffed on 2026-10-03; the per-advance audit is
`docs/advance-audit.md` (same branch), which is the data source for the advance tables in Part 1.

## Global Constraints

- PRs target the `1.4` branch, one PR per Part. Each Part is a whole feature; no "part 1 of N" PRs.
- jj only (see `CLAUDE.md`). Part 1 lives in workspace `/home/skuffed/tfe-ages`; make a new jj workspace per Part.
- Ages: `age_1_traditions` 395 (year 1 in the file), `age_2_renaissance` 400, `age_3_discovery` 500,
  `age_4_reformation` 600, `age_5_absolutism` 700, `age_6_revolutions` 800; `END_DATE = "895.12.31"`.
  Names: Theodosius, Migrations, Justinian, the Prophet, the Caliphs, Charlemagne.
- Keys never change: an age, advance, institution, unit, good or road keeps its vanilla key; only its name, text,
  age, `requires`, `potential` or numbers change. That keeps every vanilla `requires` chain and trigger working.
- Units keep their stats and models. Only names (and goods costs, Part 2) change. Battle balance stays Paradox's.
- Generated files are never edited by hand; edit the generator and rerun `python script/run.py`.
- Script and loc files carry a UTF-8 BOM; `main_menu/setup/395/` files do not. Always pass `encoding=` in Python.
- A file naming Honorius's West by tag carries a `honorius-only:` comment; otherwise use `tfe_is_western_rome`.
- Never change mod files while the game runs.
- Tests: `uv run --no-project --with numpy --with pytest --with pillow --with shapely --with pyright python -m pytest -q tools/`;
  pyright: `uv run --no-project --with pyright python -m pyright`. Both green before every PR. Every Part is seen
  working in game before its PR, or the PR says plainly that it wasn't.

## Review Focus

1. **A live advance requires a cut one.** A cut advance (potential `always = no`) silently locks every advance whose
   `requires` names it. Expect: no advance that is not cut requires a cut advance. Test in Task 1.3.
2. **An institution that can never spawn.** A plausible trigger naming areas nobody owns, or a city that doesn't
   exist yet, locks a whole tree for good. Expect: every institution trigger matches at least one location owned in
   the 395 setup. Test in Task 1.5.
3. **Settlers arriving at land the inviter lost.** The target can change hands during the walk. Expect: they settle
   only if the inviter still owns it, else at the inviter's capital. Test in Task 4.3.
4. **Germania empty.** After decades of drain, no Germanic pop is big enough to send. Expect: the action is
   unavailable, never pops from nowhere. Test in Task 4.3.
5. **A landless host migrates.** A host that is already an army country (no locations) or holds only its capital.
   Expect: no remnant is created when nothing is left behind, and a one-location host leaves one remnant. Test in
   Task 5.1.

---

# Part 1: The Ages (PR `ages`)

Already in `/home/skuffed/tfe-ages` (uncommitted): `in_game/common/age/00_default.txt` (vanilla copy, years
moved), `loading_screen/common/defines/tfe_defines.txt` (`END_DATE`), `main_menu/localization/english/replace/tfe_ages_l_english.yml`,
the `COPIES` entry in `tools/test_vanilla_copies.py`, `docs/advance-audit.md`, and a RoadMap #14 edit.

### Task 1.1: Probe `REPLACE:` on advances

**Files:** none kept (probe only, in a scratch copy of the mod's advances folder, deleted after).

TFE already uses `REPLACE:` for cultures, religions, unit types and buildings, but never for advances.

- [ ] **Step 1:** Write `in_game/common/advances/zz_probe.txt` (BOM):
  ```
  REPLACE:windmills_advance = {
  	age = age_4_reformation
  	icon = windmills_advance
  	unlock_building = windmill
  }
  ```
  Copy the real vanilla block from `in_game/common/advances/0_age_of_traditions.txt` and change only `age`.
- [ ] **Step 2:** `tools/eu5ctl.sh start`, wait, load 395 as any country, open the advances screen at age 4.
  Expected: Windmill is listed in age 4, not age 1; `logs/error.log` has no line naming `windmills_advance`.
- [ ] **Step 3:** `tools/eu5ctl.sh stop`; delete `zz_probe.txt`. If Windmill did not move, stop and report: the
  fallback is whole-file vanilla copies of the advance files, which changes Tasks 1.2-1.3.

### Task 1.2: The advances generator

**Files:**
- Create: `script/advances.py`
- Create (generated): `in_game/common/advances/tfe_vanilla_advances.txt`,
  `main_menu/localization/english/replace/tfe_advances_l_english.yml`
- Test: `tools/test_advances.py`

**Interfaces:**
- Produces: `script/advances.py` with module-level tables `MOVE: dict[str, str]` (key → age key),
  `CUT: set[str]`, `REQUIRES: dict[str, list[str]]` (key → new `requires` list), `POTENTIAL: dict[str, str]`
  (key → raw script body of a new `potential`), `STRIP: dict[str, set[str]]` (key → field keys to drop),
  `RENAME: dict[str, tuple[str, str]]` (key → name, desc), and functions `vanilla() -> dict[str, Node]`,
  `cut_keys() -> set[str]` (CUT plus the tag-collision rule), `build() -> tuple[str, str]` (script text, loc text),
  `outputs()`. Parts 2 and 3 add entries to these tables.

- [ ] **Step 1: Write the failing tests** (`tools/test_advances.py`):

```python
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
import advances as adv  # noqa: E402

VANILLA = adv.vanilla()


def test_every_table_key_is_a_vanilla_advance():
    for table in (adv.MOVE, adv.CUT, adv.REQUIRES, adv.POTENTIAL, adv.STRIP, adv.RENAME):
        assert set(table) <= set(VANILLA), set(table) - set(VANILLA)


def test_moves_name_real_ages():
    ages = {"age_1_traditions", "age_2_renaissance", "age_3_discovery", "age_4_reformation",
            "age_5_absolutism", "age_6_revolutions"}
    assert set(adv.MOVE.values()) <= ages


def test_a_moved_advance_carries_its_new_age():
    text, _ = adv.build()
    assert "REPLACE:windmills_advance = {" in text
    block = text.split("REPLACE:windmills_advance = {", 1)[1].split("\n}", 1)[0]
    assert "age = age_4_reformation" in block


def test_a_cut_advance_is_never_potential():
    text, _ = adv.build()
    for key in adv.cut_keys():
        block = text.split(f"REPLACE:{key} = {{", 1)[1].split("\n}", 1)[0]
        assert "always = no" in block, key


def test_tag_collisions_are_cut():
    cut = adv.cut_keys()
    assert {"meissen_lion", "a_mining_heritage", "rmn_the_descendants_of_trajan"} <= cut


def test_renames_have_name_and_desc():
    _, loc = adv.build()
    for key, (name, desc) in adv.RENAME.items():
        assert name and desc
        assert f' {key}: "' in loc and f' {key}_desc: "' in loc
```

- [ ] **Step 2:** Run `python -m pytest -q tools/test_advances.py`. Expected: FAIL, `No module named 'advances'`.
- [ ] **Step 3: Write the generator** (`script/advances.py`):

```python
"""Vanilla's advances in 395-895: the ones we move, cut, re-root or re-gate, and the names of the ones we rename.

Writes REPLACE: copies of only the advances we change, read from vanilla each run, so a patch is one rerun.
Data source for the tables: docs/advance-audit.md.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import borders as b  # noqa: E402  (b.GAME: vanilla's game folder)
from lint_script import parse  # noqa: E402
from pdx.core import Node, from_entries, render  # noqa: E402

FOLDER = "in_game/common/advances"
OUT = "in_game/common/advances/tfe_vanilla_advances.txt"
LOC = "main_menu/localization/english/replace/tfe_advances_l_english.yml"

MOVE: dict[str, str] = {
    # Rule B (agreed 2026-10-03): to the age where it happened.
    "geo_georgian_script": "age_2_renaissance",
    "irish_monastacism_advance": "age_2_renaissance",
    "pest_house_advance": "age_3_discovery",
    "the_pentarchy": "age_3_discovery",
    "anagignoskomena": "age_3_discovery",
    "salic_law_advance": "age_3_discovery",
    "semi_salic_law_advance": "age_3_discovery",
    "partition_inheritance_advance": "age_3_discovery",
    "windmills_advance": "age_4_reformation",
    "onmyodo": "age_4_reformation",
    "copperworking": "age_4_reformation",
    "porcelain_kiln_advance": "age_4_reformation",
    "hachiman_worship": "age_5_absolutism",
    "filioque_issue": "age_6_revolutions",
    "heian_kyo": "age_6_revolutions",
    "matsuri": "age_6_revolutions",
    "ira_shahnameh": "age_6_revolutions",
    "marcher_lords": "age_6_revolutions",
    "christianization_of_the_slavs": "age_6_revolutions",
    "cyril_and_methodius": "age_6_revolutions",
    # Slavery laws open with Rome (rename in RENAME).
    "slave_trade_act_advance": "age_1_traditions",
}

CUT: set[str] = {
    # Rule D: no period equivalent.
    "pan_amalgamation_advance", "patio_process_advance", "opera_house_advance", "stock_exchange_advance",
    "central_bank_advance", "nation_state_advance", "route_to_the_indies_advance",
    # Rule A: late flavour leaking onto 395 peoples. Transcribe every key marked "cut" in the
    # "Restricted, live" lists of docs/advance-audit.md section B (ages 1-6), e.g.:
    "wallachian_tradition", "netherlandish_protoindustry", "flemish_cloth_making", "scottish_morale",
    "peel_towers_advance", "scandinavian_bergslag_privileges_advance", "scandinavian_tar_privileges_advance",
    "paik_system_advance", "swiss_mercenaries", "the_swiss_confederation", "polders_advance",
    # ... (the rest of section B's restricted cuts)
}

REQUIRES: dict[str, list[str]] = {
    # Re-roots: a child keeps working when its parent moves later or is cut.
    "ranching": ["road_building"],            # was windmills_advance (moved to age 4)
    "alchemy_advance": ["medieval_administration"],  # was windmills_advance
    "hospital_advance": ["medieval_administration"],  # was pest_house_advance (moved to age 3)
    "railroad_advance": ["modern_road_advance"],      # was steel_mill_advance
    "road_advance_2": ["road_building"],              # was the_gold_standard
    "separation_of_powers": ["enlightenment_advance"],  # was slave_trade_act_advance (moved to age 1)
}

ROMAN = "OR = { tag = EAR tfe_is_western_rome = yes }"
POTENTIAL: dict[str, str] = {
    # Rule E: vanilla's Roman and Byzantine advances, gated on ROM/BYZ, open for Rome.
    "aqueduct_system": ROMAN,
    "unlock_legionaries_1_advance": ROMAN,
    "unlock_legionaries_2_advance": ROMAN,
    "rom_restore_the_legions": ROMAN,
    "rom_revival_of_arts_and_culture": ROMAN,
    "rom_provincial_governors": ROMAN,
    "byz_autokratoria_rhomaion": ROMAN,
    "byz_modernized_strategikon": ROMAN,
    "ira_sasanian_heritage": "OR = { tag = SAS has_or_had_tag = IRA culture = { has_culture_group = culture_group:iranian_group } }",
}

STRIP: dict[str, set[str]] = {
    # Part 3 adds the colonial_range grants here.
}

RENAME: dict[str, tuple[str, str]] = {
    # Every advance flagged "rename" in docs/advance-audit.md, with the audit's suggested name where it gives one.
    "slave_trade_act_advance": ("Roman Slave Law",
        "Rome's law knows the slave as a thing that can be bought, sold and set free, and every people that "
        "trades with Rome learns that law."),
    "medieval_administration": ("Dioceses and Prefectures",
        "Diocletian's reforms cut the provinces small and set prefects and vicars over them."),
    "deus_vult": ("Holy War",
        "Those who do not share our faith are our enemies, and God wills that we fight them."),
    "pound_lock_canals_advance": ("Canal Locks", "Gates of timber and stone hold the water, so barges climb."),
    # ... (the rest of the audit's renames)
}

TAG_GATED = re.compile(r"(?:has_or_had_tag|tag)\s*=\s*(SAX|RMN|ASK)\b")


def _blocks(path):
    text = path.read_text(encoding="utf-8-sig")
    for node in from_entries(parse(text)):
        if node.key and isinstance(node.val, list):
            yield node, text


def vanilla() -> dict[str, Node]:
    out = {}
    for p in sorted((b.GAME / FOLDER).glob("*.txt")):
        for node, _ in _blocks(p):
            if node.key != "_advances_template" and any(n.key == "age" for n in node.val):
                out[node.key] = node
    return out


def cut_keys() -> set[str]:
    """CUT, plus every advance whose potential names a tag TFE reuses for another people (SAX, RMN, ASK)."""
    keys = set(CUT)
    for key, node in vanilla().items():
        pot = [n for n in node.val if n.key == "potential"]
        if pot and TAG_GATED.search(render(pot)):
            keys.add(key)
    return keys


def _set(node: Node, key: str, val):
    node.val = [n for n in node.val if n.key != key] + ([Node(key, "=", val)] if val is not None else [])


def build() -> tuple[str, str]:
    van, cut = vanilla(), cut_keys()
    changed = set(MOVE) | cut | set(REQUIRES) | set(POTENTIAL) | set(STRIP)
    out = []
    for key in sorted(changed):
        node = Node("REPLACE:" + key, "=", list(van[key].val))
        if key in MOVE:
            _set(node, "age", MOVE[key])
        if key in REQUIRES:
            node.val = [n for n in node.val if n.key != "requires"] + [Node("requires", "=", r) for r in REQUIRES[key]]
        if key in POTENTIAL:
            _set(node, "potential", [Node(None, None, POTENTIAL[key])])
        if key in STRIP:
            node.val = [n for n in node.val if n.key not in STRIP[key]]
        if key in cut:
            _set(node, "potential", [Node("always", "=", "no")])
        out.append(node)
    loc = ["l_english:"] + [f' {k}: "{n}"\n {k}_desc: "{d}"' for k, (n, d) in sorted(RENAME.items())]
    return render(out), "\n".join(loc) + "\n"


def outputs():
    text, loc = build()
    return {OUT: text, LOC: loc}
```

  Check how `render` writes a raw body node (`Node(None, None, "OR = { ... }")`): if it does not, use the
  existing `raw()` helper the `Scope` classes use (grep `def raw` in `tools/pdx/core.py`) and adapt `_set`.
  A vanilla `requires` may appear more than once; the code above replaces all of them.
- [ ] **Step 4: Fill the tables from `docs/advance-audit.md`.** CUT gets every "cut" in section B's restricted
  lists and Rule D. RENAME gets every "rename" or "reword" in section B plus the generic renames in section A's
  systems that are not units (units are Part 2). Where the audit gives no name, follow its theme. Re-root every child
  of a cut or later-moved parent: run the Task 1.3 test, which lists them.
- [ ] **Step 5:** Run `python -m pytest -q tools/test_advances.py`. Expected: PASS.
- [ ] **Step 6:** `python script/run.py`, then the full test command and pyright. Expected: green, and
  `tools/lint_script.py` reports nothing new for `tfe_vanilla_advances.txt`.
- [ ] **Step 7:** `jj commit -m "<subject>"` (see the commit style in `git log`).

### Task 1.3: No cut parents

**Files:** Test: `tools/test_advances.py` (add).

- [ ] **Step 1: Add the test:**

```python
def test_no_live_advance_requires_a_cut_one():
    cut = adv.cut_keys()
    reqs = {}
    for key, node in VANILLA.items():
        reqs[key] = [n.val for n in node.val if n.key == "requires"]
    reqs.update(adv.REQUIRES)
    broken = {k: [r for r in rs if r in cut] for k, rs in reqs.items() if k not in cut}
    assert not {k: v for k, v in broken.items() if v}, broken


def test_no_advance_requires_one_from_a_later_age():
    order = ["age_1_traditions", "age_2_renaissance", "age_3_discovery", "age_4_reformation",
             "age_5_absolutism", "age_6_revolutions"]
    age = {k: next(n.val for n in node.val if n.key == "age") for k, node in VANILLA.items()}
    age.update(adv.MOVE)
    reqs = {k: [n.val for n in node.val if n.key == "requires"] for k, node in VANILLA.items()}
    reqs.update(adv.REQUIRES)
    late = {k: [r for r in rs if r in age and order.index(age[r]) > order.index(age[k])] for k, rs in reqs.items()}
    assert not {k: v for k, v in late.items() if v}, late
```

- [ ] **Step 2:** Run it. Expected: FAIL listing the children still to re-root. Add them to `REQUIRES`, rerun until
  PASS. (Vanilla itself never requires a later age, so every hit comes from a MOVE or CUT.)
- [ ] **Step 3:** `python script/run.py`; full tests; commit.

### Task 1.4: Institutions for 395-895

**Files:**
- Create: `script/institutions.py`
- Create (generated): `in_game/common/institution/tfe_institutions.txt`,
  `in_game/common/scripted_triggers/tfe_institution_triggers.txt`,
  `main_menu/localization/english/replace/tfe_institutions_l_english.yml`
- Test: `tools/test_institutions.py`

**Interfaces:**
- Produces: `script/institutions.py` with `THEMES: dict[str, tuple[str, str, str]]` (institution key → name,
  desc, raw trigger body of the plausible location) and `outputs()`.

Each institution keeps its key, age and spread values. Its `can_spawn` becomes the call of one scripted trigger,
`tfe_<key>_plausible_location = yes`, whatever the game rule says (iSkuffed wants variety, not fixed cities;
Plausible is vanilla's default rule anyway). The `location =` fallback is dropped.

| Key (age) | Name | Spawns in (plausible trigger) |
|---|---|---|
| `feudalism` (1) | Patrocinium | owned, nobles > 0, `sub_continent = sub_continent:western_europe` or Italy |
| `legalism` (1) | Roman Law | owned, city rank, owner `tag = EAR` or `tfe_is_western_rome = yes` |
| `meritocracy` (1) | The Nine Ranks | owned, city rank, `sub_continent = sub_continent:east_asia` |
| `renaissance` (2) | Monasticism | owned, clergy > 0, region `egypt_region`, `crescent_region`, `anatolia_region` or `france_region` |
| `banking` (2) | The Solidus | owned, city rank, burghers > 0, region `balkan_region`, `anatolia_region`, `crescent_region` or `egypt_region` |
| `professional_armies` (2) | Foederati | owned by a country whose primary culture is Germanic (`tfe_is_germanic_culture`), and borders Rome |
| `new_world` (3) | The Monsoon Trade | owned port, region `arabia_region`, `ethiopia_region`, `somalia_region`, `egypt_region` or `western_india_region` |
| `printing_press` (3) | The Scriptorium | owned, clergy > 0, city rank, sub_continent `western_europe` or `middle_east` |
| `pike_and_shot` (3) | Mounted Archery | owned, region `persia_region`, `khorasan_region`, `steppes_region` or `anatolia_region` |
| `confessionalism` (4) | Religious Law | owned, city rank, clergy > 0, region `arabia_region`, `crescent_region` or `persia_region` |
| `global_trade` (4) | The Silk Road | owned, city rank, region `xinjiang_region`, `khorasan_region`, `west_china_region` or `north_china_region` |
| `artillery_institution` (4) | Greek Fire | owned port, city rank, region `balkan_region`, `anatolia_region` or `crescent_region` |
| `manufactories` (5) | Paper | owned, city rank, region `khorasan_region`, `persia_region` or `crescent_region` |
| `scientific_revolution` (5) | The House of Wisdom | owned, city or megalopolis rank, region `crescent_region` or `persia_region` |
| `military_revolution` (5) | The Heavy Horse | owned, nobles > 0, region `france_region`, `north_german_region` or `persia_region` |
| `enlightenment` (6) | The Carolingian Renaissance | owned, clergy > 0, region `france_region`, `north_german_region`, `south_german_region` or `italy_region` |
| `industrialization` (6) | The Manor | owned, peasants > 0, region `france_region`, `north_german_region`, `south_german_region` or `great_britain_region` |
| `levee_en_masse` (6) | Feudalism | owned, nobles > 0, region `france_region`, `north_german_region`, `south_german_region` or `italy_region` |

Every trigger also has `has_owner = yes` and the vanilla custom tooltip
`custom_tooltip = { text = dominant_culture_is_owners_culture dominant_culture = owner.culture }` (from
`renaissance_plausible_location`), so an institution is born where its people live. `tfe_is_germanic_culture` is
written in Part 4 (Task 4.1); until then `professional_armies` uses
`owner = { culture = { has_culture_group = culture_group:german_group } }`.
The root advances are renamed with their institution (`renaissance_advance` → Monasticism and so on: add them to
`RENAME` in `script/advances.py`).

- [ ] **Step 1: Write the failing tests** (`tools/test_institutions.py`):

```python
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
sys.path.insert(0, str(ROOT / "tools"))
import institutions as inst  # noqa: E402
import borders as b  # noqa: E402

KEYS = {"feudalism", "legalism", "meritocracy", "renaissance", "banking", "professional_armies", "new_world",
        "printing_press", "pike_and_shot", "confessionalism", "global_trade", "artillery_institution",
        "manufactories", "scientific_revolution", "military_revolution", "enlightenment", "industrialization",
        "levee_en_masse"}


def test_all_eighteen_are_rethemed():
    assert set(inst.THEMES) == KEYS


def test_spawn_ignores_the_game_rule():
    text = inst.outputs()["in_game/common/institution/tfe_institutions.txt"]
    assert "institution_spawn" not in text and "location = " not in text
    for key in KEYS:
        assert f"tfe_{key}_plausible_location = yes" in text


def test_every_trigger_names_real_regions():
    anc = b.load_hierarchy()
    regions = {a[2] for a in anc.values()} | {a[1] for a in anc.values()}
    for key, (_, _, body) in inst.THEMES.items():
        for name in re.findall(r"(?:region|sub_continent):(\w+)", body):
            assert name in regions, (key, name)
```

- [ ] **Step 2:** Run. Expected: FAIL, no module `institutions`.
- [ ] **Step 3: Write `script/institutions.py`.** For each key, read vanilla's block from
  `in_game/common/institution/*.txt` (same `parse`/`from_entries` round trip as Task 1.2), drop `location` and
  `can_spawn`, add `can_spawn = { tfe_<key>_plausible_location = yes }`, write it as `REPLACE:<key>`. Write the 18
  scripted triggers from `THEMES` and the loc (`<key>` and `<key>_desc`). Regions in the table above; ranks are
  `location_rank = location_rank:city` / `location_rank:megalopolis`; pop counts `num_pop_type:nobles > 0`;
  a port is `is_port = yes` (check the name in `triggers.log` before use).
- [ ] **Step 4:** Run the tests. Expected: PASS. `python script/run.py`, full tests, pyright, commit.

### Task 1.5: The 395 institution map

**Files:**
- Modify: `tools/borders.py` (write `main_menu/setup/395/08_institutions.txt` in `build()`, next to `06_pops.txt`)
- Modify (generated): `main_menu/setup/395/08_institutions.txt` (today one `include` line)
- Test: `tools/test_institutions.py` (add)

At the start: Roman Law (`legalism`) in every location `EAR` or `WRE` owns; Patrocinium (`feudalism`) in every
location vanilla 1337 gives it that a non-tribal country owns in 395 (tribe, army and pop countries excluded, from
`country_types.txt`); The Nine Ranks (`meritocracy`) where vanilla 1337 has it. Nothing else.

- [ ] **Step 1: Add the failing test:**

```python
def test_395_institutions():
    text = (ROOT / "main_menu/setup/395/08_institutions.txt").read_text(encoding="utf-8")
    assert "include" not in text
    rome = b.owned_by({"EAR", "WRE"})  # honorius-only: Roman Law starts in both halves of the Empire
    blocks = dict(re.findall(r"^\s*(\w+) = \{([^}]*)\}", text, re.M))
    assert all("legalism = yes" in blocks.get(loc, "") for loc in rome)
    assert not any(k in text for k in ("renaissance", "banking", "levee_en_masse"))


def test_every_institution_can_spawn_in_395():
    owned = b.owned_by(None)  # every owned location
    anc = b.load_hierarchy()
    for key, (_, _, body) in inst.THEMES.items():
        names = set(re.findall(r"(?:region|sub_continent):(\w+)", body))
        assert not names or any(anc[l][2] in names or anc[l][1] in names for l in owned if l in anc), key
```

- [ ] **Step 2:** Run. Expected: FAIL (the file is still an `include`).
- [ ] **Step 3:** In `borders.py`, parse `GAME/main_menu/setup/1337/08_institutions.txt` (13,080 `loc = { ... }`
  blocks under `locations={`), filter as above, write the 395 file in the same format (no BOM). Use whatever
  `borders.py` already keeps for "who owns what" to implement `owned_by(tags)`.
- [ ] **Step 4:** Run tests; `python tools/borders.py`; full tests; commit.

### Task 1.6: In game, RoadMap, PR

- [ ] **Step 1:** `tools/eu5ctl.sh start`; load 395 as `EAR`. Check: the age is "Age of Theodosius"; the advances
  screen shows Roman Law, Patrocinium and The Nine Ranks as institutions; Windmill sits in age 4; the Slave law is
  researchable in age 1; Aqueduct System is visible to `EAR`. Probe file:
  `c:EAR = { if = { limit = { current_age = age_1_traditions } debug_log = "age1" } }`, `run` it, read the log.
- [ ] **Step 2:** Console `observe`, run to 401: the age turns to Migrations. `logs/error.log` has no line naming
  `tfe_vanilla_advances`, `tfe_institutions` or `tfe_institution_triggers`. `tools/eu5ctl.sh stop`.
- [ ] **Step 3:** RoadMap #14: replace the "Still to do" sentence with what was done and what is left (the plague).
  Add `advances.py` and `institutions.py` to the "Ported so far" list in `CLAUDE.md`.
- [ ] **Step 4:** Commit, `jj bookmark create ages -r @-`, track, push, `gh pr create --base 1.4 --head ages`.

---

# Part 2: Arms of Antiquity (PR `arms-of-antiquity`, after Part 1)

### Task 2.1: Firearms become weaponry

**Files:**
- Create: `script/arms.py`
- Create (generated): `in_game/common/goods_demand/tfe_arms.txt`,
  `main_menu/localization/english/replace/tfe_arms_l_english.yml`
- Modify: `script/advances.py` (CUT, RENAME)
- Test: `tools/test_arms.py`

Both goods cost 3, so firearms swap for weaponry one for one and every unit costs what it did.

The goods-demand entries holding firearms are listed below. Each is rewritten as `REPLACE:<entry>` with `firearms`
merged into `weaponry` (amounts summed):
- `army_demands.txt`: `infantry_construction`, `heavy_infantry_construction`, `rifle_infantry_construction`,
  `infantry_maintenance`, `heavy_infantry_maintenance`, `rifle_infantry_maintenance`,
  `camel_cavalry_late_construction`, `camel_cavalry_late_maintenance`, `camel_heavy_cavalry_late_construction`,
  `camel_heavy_cavalry_late_maintenance`
- `building_construction_costs.txt`: `korean_gunnery_construction`
- `pop_demands.txt`: `pop_demand` (one big block)

`from_events.txt` is left as it is: those demands belong to 1337 events that never fire.

Cannons stay as a good and are renamed "Siege Equipment". The cannon buildings and the cannon ammunition keep
working, under new names.

- [ ] **Step 1: Write the failing tests:**

```python
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
import arms  # noqa: E402

TEXT = arms.outputs()["in_game/common/goods_demand/tfe_arms.txt"]


def test_no_unit_or_pop_buys_firearms():
    assert "firearms" not in TEXT


def test_every_firearms_entry_is_replaced_and_costs_the_same():
    for entry, before in arms.vanilla_firearms_entries().items():  # {entry: (firearms, weaponry)}
        block = TEXT.split(f"REPLACE:{entry} = {{", 1)[1].split("}", 1)[0]
        weaponry = float(block.split("weaponry =", 1)[1].split()[0])
        assert abs(weaponry - (before[0] + before[1])) < 1e-9, entry


def test_cannons_are_siege_equipment():
    loc = arms.outputs()["main_menu/localization/english/replace/tfe_arms_l_english.yml"]
    assert ' cannons: "Siege Equipment"' in loc
```

- [ ] **Step 2:** Run. Expected: FAIL, no module `arms`.
- [ ] **Step 3:** Write `script/arms.py`: read every `GAME/in_game/common/goods_demand/*.txt` except
  `from_events.txt` with the parse round trip, keep the top-level entries holding `firearms`, merge firearms into
  weaponry, write `REPLACE:` blocks. Add `vanilla_firearms_entries()` for the test. Loc: `cannons` "Siege Equipment",
  `cannons_desc`; the cannon buildings (`cannon_maker` "Siege Workshop", `cannon_workshop` "Siege Engineers",
  `cannon_foundry` "Siege Foundry", `cannons_factory` "Arsenal") and their `_desc`.
- [ ] **Step 4:** Nothing buys firearms now, so the firearms buildings go. Add to `CUT` in `script/advances.py`:
  `gun_smith_advance`, `guns_workshop_advance`, `firearms_manufactory_advance`, `firearms_factory_advance`,
  `hand_cannon_guild_advance`. Check `GAME/in_game/common/building_types/production_cannons.txt` inputs: if no kept
  building takes `saltpeter`, also cut `saltpeter_workshop_advance`, `putrefaction_works_advance` and
  `putrefaction_mill_advance`. Run the Task 1.3 test and re-root what it lists.
- [ ] **Step 5:** Run the tests; `python script/run.py`; full tests; pyright; commit.

### Task 2.2: Every unit renamed

**Files:** Modify: `script/arms.py` (a `UNITS: dict[str, tuple[str, str]]` table → the same loc file). Test:
`tools/test_arms.py` (add).

Rename every unit type in `GAME/in_game/common/unit_types/*.txt` whose name is out of period (gunpowder,
age-of-sail, later named units). Stats stay. Unit-unlock advances use `$<unit>$` in their loc, so they follow
automatically. Names:

| Units | Name |
|---|---|
| handgonners | Plumbatarii |
| early arquebusiers, arquebusiers | Sagittarii |
| musketeers, fusiliers, line infantry | Scutati |
| sharpshooters, hunters | Exculcatores |
| grenadiers | Plumbatarii Veterani |
| pistoleers, cuirassiers, light dragoons | Cataphracti, Clibanarii, Equites Sagittarii |
| houfnice, bombard, falconet, field and flying artillery, royal mortar | Onagri, Ballistae, Carroballistae |
| carrack, caravel, flute, galleon, war galleon | Navis Oneraria, Dromon, Chelandion, Great Dromon, Ousiakos |
| frigate, two-decker, three-decker, ship of the line | Liburna, Bireme, Trireme, Pamphylos |
| everything else with a later name | the nearest late-antique term; "Heavy X" / "Light X" when nothing fits |

The models stay as they are: the files hold no onager or trebuchet (the game folder's `mod/trebuchet_siege_tech`
is an old EU4-style stub with no models).

- [ ] **Step 1: Add the test:**

```python
def test_every_renamed_unit_exists_and_has_text():
    keys = arms.vanilla_unit_keys()
    loc = arms.outputs()["main_menu/localization/english/replace/tfe_arms_l_english.yml"]
    for key, (name, desc) in arms.UNITS.items():
        assert key in keys and name and desc
        assert f' {key}: "{name}"' in loc
```

- [ ] **Step 2:** Run (FAIL), fill `UNITS` and `vanilla_unit_keys()`, run (PASS), regenerate, commit.

### Task 2.3: The Via Publica

**Files:** Modify: `script/arms.py` (one `REPLACE:railroad` in `in_game/common/road_types/tfe_roads.txt`, plus
loc). Test: `tools/test_arms.py` (add).

`railroad` (level 4) keeps its numbers (proximity 15, movement and market access), takes the stone-road look
(`spline_style_id = 2`, `color = map_modern_road`), and is renamed. Its advance was re-rooted off the steel mill in
Part 1.

| Key | Name |
|---|---|
| `gravel_road` | Track |
| `paved_road` | Paved Road |
| `modern_road` | Military Road |
| `railroad` | Via Publica |

- [ ] **Step 1: Add the test:**

```python
def test_the_top_road_keeps_its_numbers_but_not_its_rails():
    text = arms.outputs()["in_game/common/road_types/tfe_roads.txt"]
    block = text.split("REPLACE:railroad = {", 1)[1].split("\n}", 1)[0]
    assert "spline_style_id = 2" in block and "proximity = 15" in block and "level = 4" in block
```

- [ ] **Step 2:** Run (FAIL); write it from vanilla `in_game/common/road_types/00_generic.txt`; run (PASS);
  regenerate; commit.

### Task 2.4: In game and PR

- [ ] **Step 1:** Load 395 as `EAR`; recruit infantry; check the unit and goods tooltips: no Firearms, weaponry
  bought, Siege Equipment named. Build a top-tier road with a console effect and look at it: stone, no rails.
  `logs/error.log` clean for `tfe_arms` and `tfe_roads`.
- [ ] **Step 2:** Commit, bookmark `arms-of-antiquity`, push, `gh pr create --base 1.4`.

---

# Part 3: The Ocean Has No Other Shore (PR `new-world-closed`, after Part 1)

The Americas are not in TFE's world: no countries, no pops, and nobody can own them. Africa, Siberia, Australia and
Oceania stay as they are, settleable as frontier land. Australia is reachable only by island hopping from
Indonesia, because flat colonial range grants from advances are stripped and the base stays 1000 km.

### Task 3.1: Probe empty land

**Files:** none kept.

- [ ] **Step 1:** In a scratch copy of `06_pops.txt`, drop every pop of `mesoamerica_region`. Start the game,
  load 395, observe for a year. Check: it loads, it saves and reloads, the region shows on the map (terrain shows
  through with the user's Death to the Gray Void mod), no crash. Then from `c:SAS`, colonize an empty Arabian
  location with a console effect, and check that a charter can take a location with no pops.
- [ ] **Step 2:** If empty locations break anything, give them 1 pop each instead of none, and say so in the PR.
  Restore the file.

### Task 3.2: The Americas emptied and closed

**Files:**
- Modify: `tools/tags.txt` (drop lines for `MOC NAZ TKL TTH ZPT`), `tools/tag_map.txt` (drop their lines)
- Modify: `tools/borders.py` (drop pops of every location with `anc[l][0] == "america"` when writing `06_pops.txt`;
  write `in_game/map_data/default.map`)
- Create (generated): `in_game/map_data/default.map` (vanilla copy, the 6,174 American locations appended to
  `non_ownable = { }`)
- Modify: `tools/test_vanilla_copies.py` (add the `default.map` entry with its 16-hex hash)
- Modify: `script/advances.py` (`STRIP`: `colonial_range` from every advance that grants a flat one)
- Test: `tools/test_new_world.py`

- [ ] **Step 1: Write the failing tests:**

```python
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))
import borders as b  # noqa: E402
import advances as adv  # noqa: E402

ANC = b.load_hierarchy()
AMERICA = {l for l, a in ANC.items() if a[0] == "america"}


def test_no_one_lives_in_the_americas():
    pops = (ROOT / "main_menu/setup/395/06_pops.txt").read_text(encoding="utf-8")
    blocks = re.findall(r"^\t?(\w+) = \{", pops, re.M)
    assert not AMERICA & set(blocks)


def test_no_american_countries():
    countries = (ROOT / "main_menu/setup/395/10_countries.txt").read_text(encoding="utf-8")
    assert not any(re.search(rf"\b{t}\b", countries) for t in ("MOC", "NAZ", "TKL", "TTH", "ZPT"))


def test_the_americas_are_not_ownable():
    text = (ROOT / "in_game/map_data/default.map").read_text(encoding="utf-8-sig")
    block = text.split("non_ownable = {", 1)[1].split("}", 1)[0].split()
    assert AMERICA <= set(block)


def test_no_advance_grants_flat_colonial_range():
    text, _ = adv.build()
    assert "colonial_range = " not in text
    granting = {k for k, n in adv.vanilla().items() if any(c.key == "colonial_range" for c in n.val)}
    assert granting <= set(adv.STRIP)
```
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. `default.map`: read vanilla's bytes as text, insert the sorted American keys before
  the closing brace of `non_ownable`, write with the original encoding. In `STRIP`, add
  `{k: {"colonial_range"} for k in advances whose block has colonial_range}` computed in `advances.py` from
  `vanilla()`, so a patch that adds one is picked up.
- [ ] **Step 4:** `python tools/borders.py`; `python script/run.py`; the full tests; pyright. Check that no other
  395 setup file names an American location (grep `07_cities_and_buildings.txt`, the market and road files):
  any that does is filtered in `borders.py` too. Commit.

### Task 3.3: Frontier settlement

**Files:** Create: `main_menu/localization/english/replace/tfe_frontier_l_english.yml`.

Colonization keeps working in Africa, Siberia and Australasia, under late-antique names: grep vanilla loc for
"Colonial Charter", "Colonize", "Colonist" and "Colony" and rename the player-facing strings ("Frontier Charter",
"Settle", "Settlers", "Settlement"). Keys only; no script changes.

- [ ] **Step 1:** Write the file (BOM). `reload loc` in game to check.
- [ ] **Step 2:** In game: load 395 as `SAS`; the Americas show no owners and no population; from `c:AXM` (Aksum),
  a frontier charter is offered on unowned land in East Africa; none in the Americas. `error.log` clean.
- [ ] **Step 3:** Commit, bookmark `new-world-closed`, push, `gh pr create --base 1.4`.

---

# Part 4: Peoples on the Road (PR `peoples-on-the-road`, after Part 1 and PR #98)

Unarmed migration. A people moves, not a state: an expedition walks across the map, its people leave where it
starts and arrive where it ends. Two uses: Germanic kings inviting their people into conquered Roman land, and Slavic
bands drifting west into land the Germanic hosts emptied. Armed migration (hosts, `tfe_start_migration_effect`)
stays as it is.

### Task 4.1: One expedition type for a wandering people

**Files:**
- Create: `script/peoples_on_the_road.py`
- Create (generated): `in_game/common/expedition_types/tfe_peoples.txt`,
  `in_game/common/scripted_triggers/tfe_peoples.txt`, `main_menu/localization/english/tfe_peoples_l_english.yml`
- Test: `tools/test_peoples_on_the_road.py`

**Interfaces:**
- Produces: expedition type `tfe_wandering_people` (country `root` holds the variables `tfe_people_from`
  (location), `tfe_people_to` (location), `tfe_people_culture` (culture), `tfe_people_religion` (religion),
  `tfe_people_size` (value)); scripted trigger `tfe_is_germanic_culture` (culture scope); constants `SETTLER_SIZE`,
  `BAND_SIZE`, `TRAVEL_SPEED = 0.25`, `SETTLERS_COST = 150`, `SETTLERS_COOLDOWN = 3`, `BAND_CHANCE = 0.25`;
  `GERMANIC_GROUPS: set[str]` and `GERMANIC_CULTURES: set[str]` (the trigger is written from them) and
  `is_germanic(culture: str) -> bool` (Python mirror, reads group membership from vanilla and `tfe_cultures.txt`);
  `DOC` (the module's `Doc`, so tests can `DOC.find`).

`tools/pdx` has no builder for expedition types: write it with `doc.entry("tfe_wandering_people")` fields and
`e.effects("on_start", ...)` blocks, or `raw(...)` with a `# GAP: no expedition-type builder` comment.

```
tfe_wandering_people = {
	unique = no
	travel_speed = 0.25
	travel_mode = land
	dynamic_first_waypoint = yes
	origin = none
	ai = no
	show_start_message = no
	show_end_message = no
	potential = { has_variable = tfe_people_to }
	leader = { is_expedition_leader = no }
	on_start = {
		scope:expedition = {
			add_new_waypoint = root.var:tfe_people_from
			add_new_waypoint = root.var:tfe_people_to
		}
	}
	on_end = {
		scope:expedition.expedition_current_location = { save_scope_as = tfe_people_arrive }
		if = {
			limit = { NOT = { scope:tfe_people_arrive.owner ?= root } exists = root.capital has_variable = tfe_people_invited }
			root.capital = { save_scope_as = tfe_people_arrive }
		}
		scope:tfe_people_arrive = {
			add_pop = { culture = root.var:tfe_people_culture religion = root.var:tfe_people_religion
				type = pop_type:peasants size = root.var:tfe_people_size }
		}
		root = { remove_variable = tfe_people_to remove_variable = tfe_people_invited }
	}
	on_fail = { root = { remove_variable = tfe_people_to remove_variable = tfe_people_invited } }
}
```

Invited settlers whose target was lost settle at the inviter's capital (Review Focus 3). A Slavic band settles
wherever it arrives, whoever owns it.

`tfe_is_germanic_culture` (culture scope): `OR` over `has_culture_group = culture_group:german_group`,
`netherlandish_group`, `scandinavian_group`, plus each Gothic, Saxon, Lombard or other Germanic culture outside
those groups (`gothic_culture` and the rest; list them from `tfe_cultures.txt` and the primary cultures of the
`MIGRATORS` tags in `script/defs_decline_of_the_west.py`).

- [ ] **Step 1: Write the failing tests:**

```python
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
sys.path.insert(0, str(ROOT / "tools"))
import peoples_on_the_road as pr  # noqa: E402
import defs_decline_of_the_west as dw  # noqa: E402

OUT = pr.outputs()
EXP = OUT["in_game/common/expedition_types/tfe_peoples.txt"]
TRIG = OUT["in_game/common/scripted_triggers/tfe_peoples.txt"]


def test_the_people_walk_slowly_overland():
    assert "travel_mode = land" in EXP and f"travel_speed = {pr.TRAVEL_SPEED}" in EXP
    assert "dynamic_first_waypoint = yes" in EXP and "origin = none" in EXP


def test_settlers_whose_land_was_lost_go_to_the_capital():
    on_end = EXP.split("on_end = {", 1)[1]
    assert "root.capital" in on_end and "tfe_people_invited" in on_end


def test_every_migrator_people_is_germanic():
    countries = (ROOT / "main_menu/setup/395/10_countries.txt").read_text(encoding="utf-8")
    for tag in dw.MIGRATORS:
        culture = re.search(rf"\b{tag} = \{{.*?culture_definition = (\w+)", countries, re.S)
        assert culture and pr.is_germanic(culture.group(1)), tag   # is_germanic: Python mirror of the trigger
```

  (Check the field name for a country's primary culture in `10_countries.txt` before running, and adjust the
  regex.)
- [ ] **Step 2:** Run (FAIL); write the module; run (PASS); `python script/run.py`; tests; pyright; commit.

### Task 4.2: Probe the walk

- [ ] **Step 1:** With the game running the generated files, `run` an effect as `c:FRK`: set the variables
  (`tfe_people_from = location:<a Frankish-held location east of the Rhine>`, `tfe_people_to = location:<a Gallic
  location>`, culture `culture:frankish`, size 1), `create_character = { age = 35 culture = culture:frankish
  religion = root.religion save_scope_as = tfe_people_leader }`,
  `start_expedition = { type = expedition_type:tfe_wandering_people leader = scope:tfe_people_leader }`.
- [ ] **Step 2:** Check: the route on the Expeditions map mode starts at `tfe_people_from`, not the capital; at
  0.25 speed, the walk of about 400 km takes months, not weeks; on arrival a Frankish pop of size 1 exists at the
  target (probe with variables, since `debug_log` is muted in expedition hooks). If the route starts at the capital,
  make the first waypoint hidden (`add_new_waypoint = { location = root.var:tfe_people_from hidden = yes }`) or
  accept the capital as the origin, and record which in the PR. Then `stop`.

### Task 4.3: Invite Germanic Settlers

**Files:** Modify: `script/peoples_on_the_road.py` (a generic action in
`in_game/common/generic_actions/tfe_peoples.txt`, its loc). Test: `tools/test_peoples_on_the_road.py` (add).

A generic action on one of your own locations (any owned location; iSkuffed rejected "non-core only"), modelled on
`tfe_hospitalitas` in `script/decline_rome_actions.py` (cooldown, `ai_tick`, `ai_will_do`).

- **Visible:** the actor's primary culture is Germanic (`tfe_is_germanic_culture`); `current_age = age_1_traditions`
  or `current_age = age_2_renaissance`, so it ends in 500; the target's dominant culture is not the actor's.
- **Allowed:** no `tfe_people_to` variable (one band at a time); gold at least `SETTLERS_COST` (150); and a source
  exists: a location in `north_german_region`, `south_german_region` or `baltic_region` with a pop of the actor's
  culture, or of any Germanic culture, of size at least `SETTLER_SIZE` (Review Focus 4).
- **Cooldown:** `a.data("cooldown", type="tfe_invite_settlers", years=SETTLERS_COOLDOWN)` (3 years).
- **Effect:** pay; choose the source (prefer the actor's own culture, then the largest Germanic pop); take
  `SETTLER_SIZE` from it (`add_pop_size` with a negative value); set the five variables (culture = the actor's
  primary culture, since settlers join the inviting people: this is what lowers the cost of accepting a big Roman
  culture), set `tfe_people_invited`; create the leader; start `tfe_wandering_people`.
- **AI:** `ai_will_do` 0 unless gold is at least 3 × `SETTLERS_COST` and the target's dominant culture is not
  Germanic; then 10, plus 10 if the actor has an accepted Roman culture (`has_accepted_culture`) whose size is over
  half its primary culture's.

- [ ] **Step 1: Add the failing tests:**

```python
from pdx.core import find  # noqa: E402


def test_invite_ends_with_the_migrations():
    doc = pr.DOC
    assert doc.find("current_age", "age_2_renaissance", inside=("tfe_invite_germanic_settlers",))
    assert not doc.find("current_age", "age_3_discovery", inside=("tfe_invite_germanic_settlers",))


def test_no_settlers_from_an_empty_germania():
    doc = pr.DOC
    allow = doc.find("allow", None, inside=("tfe_invite_germanic_settlers",))
    assert allow and "pop_size" in str(allow[0].val) and "north_german_region" in str(allow[0].val)


def test_settlers_drain_germania_and_cost_gold():
    doc = pr.DOC
    assert doc.find("add_pop_size", None, inside=("tfe_invite_germanic_settlers",))
    assert doc.find("cooldown", None, inside=("tfe_invite_germanic_settlers",))
    assert doc.find("start_expedition", None, inside=("tfe_invite_germanic_settlers",))
```

- [ ] **Step 2:** Run (FAIL); implement; run (PASS); regenerate; tests; pyright; commit.
- [ ] **Step 3: In game.** Play as the Visigoths (pick them in the lobby, not by observing). Settle in Aquitaine
  with the existing host flow (or console-give a Gallic location). Use the action on a Gallo-Roman location: gold
  drops, a band appears in Germania and walks; on arrival a Visigothic pop exists there; the action is greyed by its
  cooldown. Console `set_date 500.1.2`: the action is gone. Observe 20 years as the AI: at least one AI Germanic
  kingdom uses it (`logs/game.log` or a probe counting `tfe_people_to` variables).

### Task 4.4: Slavic bands drift west

**Files:** Modify: `script/peoples_on_the_road.py` (an on_action on `yearly_country_pulse` in
`in_game/common/on_action/tfe_peoples.txt`). Test: `tools/test_peoples_on_the_road.py` (add).

Each year, a country whose primary culture is in `slavic_group` (today `venedi`), that owns a location in the
homeland areas (`polesia_area`, `volhynia_area`, `white_ruthenia_area`, `red_ruthenia_area`,
`right_bank_ukraine_area`, `lesser_poland_area`, `mazovia_area`), with no band on the road (`tfe_people_to`), has a
chance `BAND_CHANCE` (from 450 to 700) to send one:

- **From:** its own homeland location with the largest Slavic pop of size at least `BAND_SIZE`.
- **To:** a random location in `brandenburg_area`, `mecklenburg_area`, `pomerania_area`, `upper_saxony_area`,
  `bohemia_area`, `moravia_area` or `silesia_area`, weighted toward low population (the hosts' homelands that
  emptied). After 550, also the Balkan areas south of the Danube in `balkan_region`. Owner does not matter: nobody
  loses land, the band only adds people (iSkuffed's rule for a player holding those lands).
- **Then:** drain `BAND_SIZE` at the source, set the variables (culture and religion of the source pop), start
  `tfe_wandering_people`. No `tfe_people_invited`, so the band settles where it arrives.

Pacing target: the Elbe-Oder lands lean Slavic by about 550. Start with `BAND_CHANCE` 0.25 and `BAND_SIZE` 1, and
tune in game.

- [ ] **Step 1: Add the failing tests:**

```python
def test_slavic_bands_only_in_their_window():
    text = OUT["in_game/common/on_action/tfe_peoples.txt"]
    assert "450.1.1" in text and "700.1.1" in text
    assert "slavic_group" in text and "tfe_people_invited" not in text


def test_bands_never_take_land():
    text = OUT["in_game/common/on_action/tfe_peoples.txt"]
    assert "change_location_owner" not in text and "create_country" not in text
```

- [ ] **Step 2:** Run (FAIL); implement; run (PASS); regenerate; tests; pyright; commit.
- [ ] **Step 3: In game.** Observe from 450 to 560 at speed 5 (or `set_date` steps with probes). Check: bands show
  in the Expeditions map mode; Slavic pops appear in Brandenburg, Pomerania and Bohemia; the dominant culture of
  most Elbe-Oder locations is Slavic by about 550. Tune `BAND_CHANCE` and `BAND_SIZE` until it does, then say the
  final numbers in the PR. `error.log` clean.
- [ ] **Step 4:** Commit, bookmark `peoples-on-the-road`, push, `gh pr create --base 1.4`. Update the memory note
  `expeditions-as-migrations.md` to "built".

---

# Part 5: Those Who Stayed (PR `remnants`, after PR #98)

When a host takes to the road, its homeland stops going to one random neighbour (which made one or two German
hegemons). The homeland becomes a new country of whoever stays: its culture is the majority culture at the host's
old capital, and it holds every location the host left.

### Task 5.1: A remnant in place of the heir

**Files:**
- Modify: `script/defs_migratory.py` (`raise_host`, the `tfe_heir_to_the_land` lookup and handover, lines ~50-77 in
  the migrants lane)
- Modify (generated): `in_game/common/scripted_effects/tfe_migratory.txt`, its loc
- Test: `tools/test_barbarian_kingdoms.py` (add; it already builds `START`)

**Interfaces:**
- Consumes: `tfe_start_migration_effect` (country scope; `scope:tfe_host` is the host).
- Produces: the scope `tfe_remnant` (the new country) inside the effect, the variable `tfe_remnant_of` on it (the
  host), for later events.

New flow, replacing the heir lookup and handover:
```
if = {
	limit = { capital ?= { owner = root } }
	capital = {
		save_scope_as = tfe_old_capital
		create_country_from_location = {
			define_unique_country_tag = REMNANT
			change_government_type = government_type:tribe
			set_primary_culture = scope:tfe_old_capital.dominant_culture
			set_country_religion = root.religion
			set_variable = { name = tfe_remnant_of value = root }
			save_scope_as = tfe_remnant
		}
	}
	every_owned_location = { change_location_owner = scope:tfe_remnant add_core = scope:tfe_remnant }
}
```
Check the effect names `set_primary_culture`, `set_country_religion` and `define_unique_country_tag` in
`effects.log`, and copy the shape of `tfe_usurpers.txt`'s `create_country_from_location` (it sets a name, colour
and flag; a remnant takes its name from its capital if the game does that by default, otherwise from loc
`TFE_REMNANT` = "[culture adjective] Remnant"). Keep the `abandon_location` branch for a host that owns no capital
(Review Focus 5). Remove the `random_neighbor_country` lookup and its `EAR`/western-Rome fallback.

- [ ] **Step 1: Add the failing tests:**

```python
def test_the_homeland_becomes_a_remnant_not_a_neighbours_prize():
    assert START.find("create_country_from_location", None, inside=("tfe_start_migration_effect",))
    assert not START.find("save_scope_as", "tfe_heir_to_the_land", inside=("tfe_start_migration_effect",))
    assert START.find("change_location_owner", "scope:tfe_remnant", inside=("tfe_start_migration_effect",))


def test_the_remnant_is_of_the_people_who_stayed():
    assert START.find("set_primary_culture", "scope:tfe_old_capital.dominant_culture",
                      inside=("tfe_start_migration_effect", "create_country_from_location"))


def test_a_landless_host_leaves_no_remnant():
    ifs = START.find("if", None, inside=("tfe_start_migration_effect",))
    assert any("capital" in str(i.val) and "create_country_from_location" in str(i.val) for i in ifs)
```

- [ ] **Step 2:** Run (FAIL); change `raise_host`; run (PASS); `python script/run.py`; tests; pyright; commit.
- [ ] **Step 3: In game.** Observe from 395; force a migration with the console (`tfe_migrate_west` on `c:VIS`).
  Check: a new country holds every Visigothic location left behind, named sensibly, with the majority culture of
  the old capital; no neighbour gained them. Let ten years pass: no hegemon forms out of remnants alone. Play as a
  host once (lobby pick) and migrate: the remnant appears behind you. `error.log` clean.
- [ ] **Step 4:** Commit, bookmark `remnants`, push, `gh pr create --base 1.4`.

---

## Order

Part 1 first (Parts 2 and 3 add entries to its tables). Parts 2, 3 and 4 can then run in parallel, in separate jj
workspaces, as they touch different files except for the tables in `script/advances.py`. Merge those table edits
on rebase by keeping both sides' entries. Part 5 needs only PR #98.
