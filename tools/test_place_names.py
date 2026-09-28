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


def test_a_key_named_twice_fails(tmp_path, monkeypatch):
    (tmp_path / "italy_region.txt").write_text("italy_region = A  # a: x\nitaly_region = B  # a: y\n",
                                               encoding="utf-8")
    monkeypatch.setattr(pn, "NAMES", tmp_path)
    with pytest.raises(ValueError):
        pn.load_places()


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
        keys = {p[depth] for p in anc.values() if len(p) > depth} & set(names)
        by = {}
        for k in keys:
            by.setdefault(names[k].lower(), []).append(k)
        dupes = {n: ks for n, ks in by.items() if len(ks) > 1}
        assert not dupes, (layer, dupes)


def test_every_region_area_and_province_with_a_table_is_named():
    anc, names = b.load_hierarchy(), pn.load_places()
    done = {f.stem for f in (b.TOOLS / "names").glob("*_region.txt")}
    need = set()
    for l in pn.ownable(anc):
        p = anc[l]
        if p[2] in done:
            need |= {p[2], p[3], p[4]}
    need -= set(anc)   # a province sharing its key with its town keeps the town's name (kilkenny)
    assert not need - set(names), sorted(need - set(names))[:20]


def test_every_roman_town_has_its_latin_or_greek_name():
    have = pn.load_towns()
    for lang, want in pn.wanted_towns().items():
        if not (b.TOOLS / f"names/towns_{lang.split('_')[0]}.txt").exists():
            continue
        assert not want - set(have[lang]), (lang, sorted(want - set(have[lang]))[:20])
    locs = set(b.load_hierarchy())
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


def test_all_regions_in_scope_have_tables():
    assert {f.stem for f in (b.TOOLS / "names").glob("*_region.txt")} == set(pn.SCOPE)


def test_no_named_place_is_also_a_town():
    # vanilla gives one key to both the province and its town (kilkenny): naming the province renames the town
    towns = set(b.load_hierarchy())
    assert not set(pn.load_places()) & towns, sorted(set(pn.load_places()) & towns)


def test_town_tables_only_fill_gaps():
    # never override a vanilla Latin or Greek name, never name a town outside the Empire
    have = pn.load_towns()
    for lang, want in pn.wanted_towns().items():
        assert not set(have[lang]) - want, (lang, sorted(set(have[lang]) - want)[:10])


def test_a_constructed_town_name_repeats_no_other_town():
    # attested homonyms are genuine (two Brigantiums, several Constantias); a d name we made up must be unique
    have, per = pn.load_towns(), {}
    for lang in have:
        for f in (b.GAME / "main_menu/localization/english/location_names").glob("*.yml"):
            for k, v in re.findall(rf'^\s*(\w+)\.{lang}:\d*\s*"(.*?)"', f.read_text(encoding="utf-8-sig", errors="replace"),
                                   re.M):
                per.setdefault(lang, {})[k.lower()] = v
    for lang, table in (("latin_language", "towns_latin"), ("greek_language", "towns_greek")):
        names = {**per.get(lang, {}), **have[lang]}
        for no, key, name, basis in pn.parse_table(b.TOOLS / f"names/{table}.txt"):
            if basis == "d":
                others = sorted(k for k, v in names.items() if v == name and k != key)
                assert not others, f"{table}.txt:{no}: {key} = {name} repeats {others}"


def test_names_carry_no_article_or_territory_prefix():
    # on the map a leading "the" crowds the label (the Ruteni); a city territory is the city's Latin name (Carthago)
    bad = {k: n for k, n in pn.load_places().items() if n.startswith("the ") or "Territory of" in n}
    assert not bad, sorted(bad.items())[:10]


def test_names_lead_with_the_name_not_a_direction_or_ordinal():
    # "Northern Senonia" and "First Belgica" read as clutter on the map: a unit gets its own ancient name, and the
    # Roman numbered provinces are written as the Romans did (Belgica Prima, Germania Secunda)
    lead = re.compile(r"^(Northern|Southern|Eastern|Western|Upper|Lower|Inner|Outer|Central|Middle|Coast of|Greater|"
                      r"Lesser|Far|Near|First|Second|Third|Fourth|Senonian)\b")
    bad = {k: n for k, n in pn.load_places().items() if lead.match(n)}
    assert not bad, (len(bad), sorted(bad.items())[:10])
