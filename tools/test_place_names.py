"""Place names of 395: regions, areas and provinces in English classical forms, towns in Latin and Greek."""
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
