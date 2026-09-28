# Place Names of 395 — Design

Approved in chat 2026-09-28: English classical forms; the Empire plus the lands beyond; fill the missing town names
in Latin and Greek; name tables plus a generator; delivered in four PRs.

## Goal

The map reads like 1337: regions, areas and provinces carry medieval and modern names (Lazio, Normandy, Brabant,
Transdanubia). Rename them to the late Roman world's own names, in English classical forms, for the Empire and the
lands beyond it, and fill the gaps in the Latin and Greek town names so no Roman town shows a modern name (Carthage
still reads "Tunis").

## Scope

Every region, area and province with at least one ownable land location in these 25 EU5 regions:

| group | regions | areas | provinces |
|---|---|---|---|
| The Empire's heart | italy, france, iberia, great_britain, maghreb, egypt, anatolia, crescent, balkan | 90 | 504 |
| The frontier | south_german, north_german, carpathia, caucasus, nubia | 46 | 237 |
| The lands beyond | ireland, scandinavian, north_atlantic_islands, baltic, ruthenia, steppes, arabia, persia, khorasan, ethiopia, macaronesia | 77 | 523 |
| **Total** | **25** | **213** | **1,264** |

The limit is the world Roman geographers named (Ptolemy's *Geography*).

Towns: every location WRE owns in 395 with no vanilla `.latin_language` name (533), and every location EAR owns
with no `.greek_language` name (36).

Out of scope: sea zones; the russian, ural and Siberian regions, sub-Saharan Africa, India, East Asia and the
Americas; town names outside the Empire; languages other than Latin and Greek.

## What the game offers (found 2026-09-28)

- Default names: `<key>: "Name"` in vanilla's `area_l_english.yml`, `region_names_l_english.yml`,
  `province_names_l_english.yml` and `location_names/location_names_l_english.yml`.
- Per-language names exist only for locations and provinces: `<key>.<language>: "Name"` in
  `location_names/location_names_<language>_l_english.yml` (8,760 location keys, 179 province keys). A per-language
  name beats the default where that language applies. Areas and regions have one name each.
- TFE's Roman cultures speak `roman_dialect`, a dialect of `latin_language`, whose fallback is `greek_language`.
  Vanilla already names 1,350 of WRE's 1,883 locations in Latin and 646 of EAR's 682 in Greek; no province, area or
  region has a Latin name, and 176 of the Empire's 515 provinces have a Greek one.

## Mechanism

### Name tables

`tools/names/<region>.txt`, one file per EU5 region, in the `key = value  # note` style of `tools/*.txt`:

```
france_region = Diocese of Gaul                    # a: Dioecesis Galliarum
normandy_area = Second Lugdunensis                 # a: Lugdunensis II, capital Rotomagus
caux_province = Caleti                             # a: civitas Caletorum
upper_rhine_valley_province = Upper Rhine Valley   # d: no ancient unit fits
```

The note begins with the basis of the name:

- `a`: attested ancient name of the unit that best fits the EU5 borders.
- `p`: a people or place from Ptolemy (or Tacitus, Strabo), for the lands beyond.
- `d`: descriptive English, only where nothing ancient fits.

Towns: `tools/names/towns_latin.txt` and `tools/names/towns_greek.txt`, `location = Name  # a|p|d: note`, the name
in Latin or Greek like vanilla's own (`tunis = Carthago  # a`).

### Generator

`tools/place_names.py` reads the tables and writes into `main_menu/localization/english/replace/` (which wins over
vanilla):

- `tfe_place_names_l_english.yml`: `<key>: "Name"` for every region, area and province in the tables; plus, for
  every vanilla per-language province name (`<province>.<language>`) in scope, the same English name under that
  key, so a Greek-speaking East reads "Bithynia" too.
- `tfe_town_names_l_english.yml`: `<location>.latin_language` and `<location>.greek_language` names from the town
  tables.

A table key that is not a real region, area, province or location, or a line without a basis, fails the build.

## Naming rules

- Layer to layer: regions are dioceses or the great lands beyond (Diocese of Gaul, Free Germania, Sarmatia,
  Persia); areas are Roman provinces or tribal lands (Second Lugdunensis, Valeria, Caledonia); provinces are
  civitates, peoples, districts or city territories (Parisii, Treveri, Cyrrhestica, Carthago).
- Best fit, not exact fit: each name goes to the EU5 unit covering most of that ground. A Roman province split over
  two EU5 areas uses the Romans' own division where one existed (First and Second Belgica), else a geographic
  qualifier (Northern Tarraconensis).
- No two regions, no two areas and no two provinces share a name.
- No leading article, on the map it crowds the label: Parisii, Ruteni, Caucasus, not the Parisii. A city territory
  is the city's Latin name (Carthago, Roma, Mediolanum), not "the Territory of Carthage". (Changed 2026-09-29
  after the in-game test.)
- English classical spelling: the conventional English form where one exists (Thrace, Cappadocia, Parisii),
  otherwise the Latin form without long-vowel marks (Lugdunensis).
- Towns stay in their language, Latin in the West and Greek in the East, like vanilla's.

## Research

Split by group and researched in parallel: the West's heart, the East's heart, the frontier, the lands beyond, the
towns. Each researcher gets the exact EU5 keys of its regions and the locations each province holds (so the name
fits the ground), and returns a filled table with a basis and short note on every line. Every table is reviewed
before it goes in: spelling and forms consistent across groups, no duplicate names, weak `d` names challenged.

## Tests (`tools/test_place_names.py`)

- Every region, area and province in scope has a name; every WRE location without a vanilla Latin name has a Latin
  one, every EAR location without a vanilla Greek name a Greek one. After an EU5 patch, a new key in scope is named
  by the failure.
- Every table key exists in the game; no empty names; every line has a basis `a`, `p` or `d`.
- No duplicate names within a layer.
- Every vanilla per-language province name in scope is overridden.
- The generated files match the tables and start with a UTF-8 BOM.

In game: the map labels at region, area and province zoom (Diocese of Gaul, Second Lugdunensis, Parisii);
Carthage reads Carthago; the East's provinces read English, not Greek. And a probe: does a town's name follow its
pops' language or its owner's? That decides what a Roman town shows once the Goths hold it.

## Delivery

Four PRs, each merged before the next, each with its tables, generated files and passing tests:

1. The generator and tests, and the Empire's heart (9 regions).
2. The frontier (5 regions).
3. The lands beyond (11 regions).
4. The towns (569 names).

Until all four land, the coverage test checks only the regions that have a table in `tools/names/` (and the towns
only once their tables exist), so each PR passes on its own. PR 3 adds a check that all 25 regions have tables.
