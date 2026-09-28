# Place Names of 395 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the regions, areas and provinces of the Empire and the lands beyond to 395 names in English classical forms, and fill the missing Latin and Greek town names.

**Architecture:** Name tables in `tools/names/` (one per EU5 region, plus two town tables), a generator `tools/place_names.py` that validates them against the map hierarchy and writes two localization files into `main_menu/localization/english/replace/`, and `tools/test_place_names.py`. The names are researched per region from briefs the generator prints (each province with the towns it holds).

**Tech Stack:** Python 3.12 (pytest; `tools/borders.py` for the map hierarchy), EU5 YAML localization.

**Spec:** `docs/specs/2026-09-28-place-names-design.md`

## Global Constraints

- Scope: every region, area and province with at least one ownable land location in these 25 regions: italy, france, iberia, great_britain, maghreb, egypt, anatolia, crescent, balkan, south_german, north_german, carpathia, caucasus, nubia, ireland, scandinavian, north_atlantic_islands, baltic, ruthenia, steppes, arabia, persia, khorasan, ethiopia, macaronesia (each `<name>_region`).
- Towns: every location WRE owns with no vanilla `.latin_language` name; every location EAR owns with no vanilla `.greek_language` name.
- Table line: `key = Name  # b: note`, where `b` is `a` (attested), `p` (Ptolemy, Tacitus, Strabo) or `d` (descriptive).
- English classical forms for regions, areas, provinces; towns in Latin (West) or Greek (East), like vanilla's.
- No two regions, no two areas, no two provinces share a name.
- Generated files start with a UTF-8 BOM; Python reads and writes with an explicit encoding (CLAUDE.md).
- For testing in game, all four groups land on the `place-names` branch; they go up as the spec's four PRs after the human has tested.

## Review Focus

- A name containing a double quote breaks the YAML line and every key after it: the generator rejects `"` in names.
- A key in the wrong region's table (e.g. an Alpine province listed under italy) would pass coverage but confuse review: the generator rejects keys outside their file's region.
- A province whose land is all wasteland or impassable has no ownable location and so is out of scope; naming it is allowed, never required.
- The same key listed twice (in one table or two) must fail, not silently take the last value.
- A town table key that is a province or area (not a location) must fail.

---

### Task 1: Generator and tests

**Files:**
- Create: `tools/place_names.py`
- Create: `tools/test_place_names.py`
- Create: `tools/names/.gitkeep`

**Interfaces:**
- Consumes: `borders.load_hierarchy() -> {location: (continent, subcontinent, region, area, province)}`, `borders.load_topography()`, `borders.load_unownable()`, `borders.LAND_TOPO`, `borders.GAME`, `borders.MOD`, `borders.TOOLS`, and the WRE/EAR `own_control_core` lists in `main_menu/setup/start/10_countries.txt`.
- Produces:
  - `SCOPE: tuple[str, ...]` (the 25 region keys)
  - `parse_table(path) -> list[tuple[int, str, str, str]]` (line no, key, name, basis)
  - `ownable(anc) -> set[str]` (locations with ownable land)
  - `load_places() -> {key: name}` (all region tables, validated)
  - `load_towns() -> {"latin_language": {loc: name}, "greek_language": {loc: name}}`
  - `wanted_towns() -> {"latin_language": set, "greek_language": set}`
  - `vanilla_per_language() -> {key: set(language)}` for vanilla location/province keys
  - `build_places() -> str`, `build_towns() -> str` (YAML text, without BOM)
  - `brief(region) -> str` (research brief: areas, provinces, their towns with vanilla English and Latin/Greek names)
  - CLI: `python tools/place_names.py` writes both files; `python tools/place_names.py brief <region>` prints a brief.

- [ ] **Step 1: Write the failing tests** (`tools/test_place_names.py`)

```python
"""Place names of 395: regions, areas and provinces in English classical forms, towns in Latin and Greek."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b
import place_names as pn

REPLACE = b.MOD / "main_menu/localization/english/replace"


def test_table_lines_parse_with_a_basis(tmp_path):
    f = tmp_path / "t.txt"
    f.write_text("# header\nitaly_region = Diocese of Italy  # a: Dioecesis Italiae\n\n"
                 "x_province = the Taurini   # p: Ptolemy 3.1\n", encoding="utf-8")
    assert pn.parse_table(f) == [(2, "italy_region", "Diocese of Italy", "a"), (4, "x_province", "the Taurini", "p")]
    for bad in ("k = Name\n", "k = Name  # z: no\n", 'k = Na"me  # a: x\n', "k =   # a: x\n"):
        f.write_text(bad, encoding="utf-8")
        with pytest.raises(ValueError):
            pn.parse_table(f)


def test_tables_name_real_keys_in_their_own_region_once():
    anc = b.load_hierarchy()
    seen = {}
    for f in sorted((b.TOOLS / "names").glob("*_region.txt")):
        assert f.stem in pn.SCOPE, f.name
        for no, key, name, basis in pn.parse_table(f):
            where = {p[2] for p in anc.values() if key in p[2:5]}
            assert where == {f.stem}, f"{f.name}:{no}: {key} is not in {f.stem}"
            assert key not in seen, f"{f.name}:{no}: {key} also in {seen[key]}"
            seen[key] = f.name


def test_no_two_names_alike_in_a_layer():
    anc, names = b.load_hierarchy(), pn.load_places()
    for depth, layer in ((2, "region"), (3, "area"), (4, "province")):
        keys = {p[depth] for p in anc.values()} & set(names)
        by = {}
        for k in keys:
            by.setdefault(names[k].lower(), []).append(k)
        dupes = {n: ks for n, ks in by.items() if len(ks) > 1}
        assert not dupes, (layer, dupes)


def test_every_region_area_and_province_with_a_table_is_named():
    anc, names = b.load_hierarchy(), pn.load_places()
    land = pn.ownable(anc)
    done = {f.stem for f in (b.TOOLS / "names").glob("*_region.txt")}
    need = set()
    for l in land:
        p = anc[l]
        if p[2] in done:
            need |= {p[2], p[3], p[4]}
    assert not need - set(names), sorted(need - set(names))[:20]


def test_every_roman_town_has_its_latin_or_greek_name():
    have = pn.load_towns()
    for lang, want in pn.wanted_towns().items():
        if not (b.TOOLS / f"names/towns_{lang.split('_')[0]}.txt").exists():
            continue
        assert not want - set(have[lang]), (lang, sorted(want - set(have[lang]))[:20])
    locs = {l for l in b.load_hierarchy()}
    for lang, got in have.items():
        assert not set(got) - locs, (lang, sorted(set(got) - locs)[:10])   # towns, not provinces


def test_vanilla_per_language_province_names_are_overridden():
    names, text = pn.load_places(), pn.build_places()
    for key, langs in pn.vanilla_per_language().items():
        if key in names:
            for lang in langs:
                assert f' {key}.{lang}: "{names[key]}"' in text, (key, lang)


@pytest.mark.parametrize("name,build", [("tfe_place_names_l_english.yml", "build_places"),
                                        ("tfe_town_names_l_english.yml", "build_towns")])
def test_generated_files_match_the_tables(name, build):
    f = REPLACE / name
    assert f.read_bytes().startswith(b"\xef\xbb\xbf"), name
    assert f.read_text(encoding="utf-8-sig") == getattr(pn, build)(), "rerun tools/place_names.py"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/test_place_names.py -q`
Expected: collection error `ModuleNotFoundError: No module named 'place_names'`.

- [ ] **Step 3: Write the generator** (`tools/place_names.py`)

```python
"""TFE place names of 395 (docs/specs/2026-09-28-place-names-design.md).

  python tools/place_names.py                 write localization/english/replace/tfe_{place,town}_names_l_english.yml
  python tools/place_names.py brief REGION    print a research brief: areas, provinces and their towns
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

NAMES = b.TOOLS / "names"
REPLACE = b.MOD / "main_menu/localization/english/replace"
LOCNAMES = b.GAME / "main_menu/localization/english/location_names"
SCOPE = tuple(f"{r}_region" for r in (
    "italy", "france", "iberia", "great_britain", "maghreb", "egypt", "anatolia", "crescent", "balkan",
    "south_german", "north_german", "carpathia", "caucasus", "nubia",
    "ireland", "scandinavian", "north_atlantic_islands", "baltic", "ruthenia", "steppes", "arabia", "persia",
    "khorasan", "ethiopia", "macaronesia"))
LINE = re.compile(r"^(\w+)\s*=\s*([^#]*?)\s*#\s*([apd]):")


def parse_table(path):
    out = []
    for no, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not raw.split("#", 1)[0].strip():
            continue
        m = LINE.match(raw.strip())
        if not m or not m.group(2):
            raise ValueError(f"{Path(path).name}:{no}: expected 'key = Name  # a|p|d: note'")
        if '"' in m.group(2):
            raise ValueError(f"{Path(path).name}:{no}: a name cannot hold a double quote")
        out.append((no, m.group(1), m.group(2), m.group(3)))
    return out


def ownable(anc):
    topo, unown = b.load_topography(), b.load_unownable()
    return {l for l, p in anc.items() if len(p) > 4 and topo.get(l) in b.LAND_TOPO and l not in unown}


def load_places():
    names = {}
    for f in sorted(NAMES.glob("*_region.txt")):
        for no, key, name, _ in parse_table(f):
            if key in names:
                raise ValueError(f"{f.name}:{no}: {key} named twice")
            names[key] = name
    return names


def load_towns():
    out = {"latin_language": {}, "greek_language": {}}
    for lang in out:
        f = NAMES / f"towns_{lang.split('_')[0]}.txt"
        if f.exists():
            for no, key, name, _ in parse_table(f):
                if key in out[lang]:
                    raise ValueError(f"{f.name}:{no}: {key} named twice")
                out[lang][key] = name
    return out


def vanilla_per_language():
    out = {}
    for f in LOCNAMES.glob("*.yml"):
        for key, lang in re.findall(r"^ (\w+)\.(\w+):", f.read_text(encoding="utf-8-sig", errors="replace"), re.M):
            out.setdefault(key, set()).add(lang)
    return out


def owners():
    text = (b.MOD / "main_menu/setup/start/10_countries.txt").read_text(encoding="utf-8-sig")
    own = {}
    for m in re.finditer(r"^\t\t(\w{3}) = \{.*?own_control_core = \{(.*?)\}", text, re.M | re.S):
        for l in m.group(2).split():
            own[l] = m.group(1)
    return own


def wanted_towns():
    per, own = vanilla_per_language(), owners()
    return {"latin_language": {l for l, t in own.items() if t == "WRE" and "latin_language" not in per.get(l, ())},
            "greek_language": {l for l, t in own.items() if t == "EAR" and "greek_language" not in per.get(l, ())}}


def build_places():
    names, per = load_places(), vanilla_per_language()
    lines = []
    for key in sorted(names):
        lines.append(f' {key}: "{names[key]}"')
        lines += [f' {key}.{lang}: "{names[key]}"' for lang in sorted(per.get(key, ())) if not key.endswith("_region")]
    return "l_english:\n" + "".join(l + "\n" for l in lines)


def build_towns():
    towns = load_towns()
    lines = [f' {k}.{lang}: "{n}"' for lang in sorted(towns) for k, n in sorted(towns[lang].items())]
    return "l_english:\n" + "".join(l + "\n" for l in lines)


def brief(region):
    anc = b.load_hierarchy()
    land = ownable(anc)
    en = {}
    for f in (b.GAME / "main_menu/localization/english").rglob("*.yml"):
        for k, v in re.findall(r'^ ([\w.]+):\d* "(.*)"', f.read_text(encoding="utf-8-sig", errors="replace"), re.M):
            en.setdefault(k, v)
    own, tree = owners(), {}
    for l in sorted(land):
        p = anc[l]
        if p[2] == region:
            tree.setdefault(p[3], {}).setdefault(p[4], []).append(l)
    out = [f"{region} ({en.get(region, '?')})"]
    for area, provs in sorted(tree.items()):
        out.append(f"  {area} ({en.get(area, '?')})")
        for prov, locs in sorted(provs.items()):
            out.append(f"    {prov} ({en.get(prov, '?')})")
            for l in locs:
                alt = en.get(f"{l}.latin_language") or en.get(f"{l}.greek_language") or ""
                out.append(f"      {l}: {en.get(l, '?')}{' / ' + alt if alt else ''} [{own.get(l, '-')}]")
    return "\n".join(out)


if __name__ == "__main__":
    if sys.argv[1:2] == ["brief"]:
        print(brief(sys.argv[2]))
    else:
        REPLACE.mkdir(parents=True, exist_ok=True)
        (REPLACE / "tfe_place_names_l_english.yml").write_text(build_places(), encoding="utf-8-sig")
        (REPLACE / "tfe_town_names_l_english.yml").write_text(build_towns(), encoding="utf-8-sig")
        print("wrote tfe_place_names_l_english.yml and tfe_town_names_l_english.yml")
```

Also `tools/names/.gitkeep` (empty), then run `python tools/place_names.py` once to write the (still empty) files.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tools/test_place_names.py -q`
Expected: all pass (no tables yet, so coverage checks are vacuous; the parser test is real).

- [ ] **Step 5: Commit**

```bash
git add tools/place_names.py tools/test_place_names.py tools/names/.gitkeep main_menu/localization/english/replace/tfe_*_names_l_english.yml
git commit -m "The map can learn new names: tables, a generator and its tests"
```

### Task 2: The Empire's heart (9 regions)

**Files:**
- Create: `tools/names/{italy,france,iberia,great_britain,maghreb,egypt,anatolia,crescent,balkan}_region.txt`
- Modify: `main_menu/localization/english/replace/tfe_place_names_l_english.yml` (regenerated)

**Interfaces:**
- Consumes: `python tools/place_names.py brief <region>`; the table format and naming rules above.
- Produces: one table per region; every region, area and province with ownable land named.

- [ ] **Step 1: Print the briefs** — `python tools/place_names.py brief italy_region` (and the other 8) into `tools/out/briefs/` (ignored by git).
- [ ] **Step 2: Research each region** (in parallel, one researcher per region) and write its table: the region key first, then each area, then its provinces, each line `key = Name  # a|p|d: note`, following the spec's naming rules (regions = dioceses, areas = Roman provinces, provinces = civitates/peoples/districts; best fit; English classical spelling; no duplicates).
- [ ] **Step 3: Review** every table: spelling consistent across regions, no duplicates, `d` names challenged.
- [ ] **Step 4: Run** `python tools/place_names.py && python -m pytest tools/test_place_names.py -q` — Expected: all pass.
- [ ] **Step 5: Commit** — `git add tools/names main_menu/localization/english/replace/tfe_place_names_l_english.yml && git commit -m "..."`

### Task 3: The frontier (5 regions)

Same steps as Task 2 for `south_german`, `north_german`, `carpathia`, `caucasus`, `nubia` (`tools/names/<region>_region.txt`), with Roman names on the Roman side of each region and the Romans' names for peoples beyond (Free Germania, the Marcomanni, Dacia, Iberia of the Caucasus, the Nobatae).

### Task 4: The lands beyond (11 regions)

Same steps as Task 2 for `ireland`, `scandinavian`, `north_atlantic_islands`, `baltic`, `ruthenia`, `steppes`, `arabia`, `persia`, `khorasan`, `ethiopia`, `macaronesia`, drawing on Ptolemy, Tacitus and Strabo (`p`) where Rome had no provinces. Then add to `tools/test_place_names.py`:

```python
def test_all_regions_in_scope_have_tables():
    assert {f.stem for f in (b.TOOLS / "names").glob("*_region.txt")} == set(pn.SCOPE)
```

Run, expect pass, commit.

### Task 5: The towns

**Files:**
- Create: `tools/names/towns_latin.txt`, `tools/names/towns_greek.txt`
- Modify: `main_menu/localization/english/replace/tfe_town_names_l_english.yml` (regenerated)

- [ ] **Step 1: List the towns** — `python -c "import sys; sys.path.insert(0,'tools'); import place_names as pn; w = pn.wanted_towns(); print(len(w['latin_language']), len(w['greek_language']))"` (expect 533 and 36), with each town's vanilla English name and province from the briefs.
- [ ] **Step 2: Research** the Latin (West) and Greek (East) name of each, attested where one exists (`a`), else a plain Latinised or Hellenised form of the local name (`d`).
- [ ] **Step 3: Run** `python tools/place_names.py && python -m pytest tools/test_place_names.py -q` — Expected: all pass.
- [ ] **Step 4: Commit.**

### Task 6: Whole-suite check and hand-off for the in-game test

- [ ] **Step 1:** `python -m pytest tools -q` — Expected: all pass.
- [ ] **Step 2:** Confirm the mod folder is the repo (junction) and the branch is `place-names`, so the game loads it.
- [ ] **Step 3:** Hand the human the in-game checklist: region, area and province labels at each zoom (Diocese of Gaul, Second Lugdunensis, the Parisii); Carthage reads Carthago; the East's provinces read English; any `tfe_` lines in `logs/error.log`. Note what a town shows once a non-Latin owner holds it.
- [ ] **Step 4:** After the human's test, push the branch and open the spec's PRs.
