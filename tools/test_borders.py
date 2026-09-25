import re
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent
START = MOD / "main_menu/setup/start"
STUBS = ["05_characters", "07_cities_and_buildings", "11_art", "12_diplomacy", "13_religion",
         "15_international_organizations", "16_wars", "18_opinions", "20_rivals", "23_colonies", "24_town_rights", "03_markets", "09_roads",
         "25_area_preferences", "26_ai_personalities", "27_armies"]


def test_stubs_only_reference_tfe_tags():
    tfe = set(b.load_tags())
    for name in STUBS:
        text = (START / f"{name}.txt").read_text(encoding="utf-8-sig")
        code = re.sub(r"#[^\n]*", "", text)
        assert code.count("{") == code.count("}"), name
        refs = set(re.findall(r"\b(?:tag|country|first|second)\s*=\s*([A-Z][A-Z0-9]{2})\b", code))
        assert refs <= tfe, (name, refs - tfe)


import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b


def test_hierarchy_places_rome_in_italy():
    anc = b.load_hierarchy()
    assert "italy_region" in anc["rome"]
    assert anc["rome"][0] == "europe"


def test_land_topographies_cover_vanilla_owned():
    topo = b.load_topography()
    text = (b.GAME / "main_menu/setup/start/10_countries.txt").read_text(encoding="utf-8-sig")
    owned = set()
    for block in re.findall(r"own_control_\w+\s*=\s*\{([^}]*)\}", re.sub(r"#[^\n]*", "", text)):
        owned.update(b.tokens(block))
    bad = {l: topo.get(l) for l in owned if topo.get(l) not in b.LAND_TOPO}
    assert not bad, sorted(bad.items())[:20]
    assert topo["argolic_gulf"] not in b.LAND_TOPO


def test_centroids_cover_the_map():
    cent = b.load_centroids()
    assert len(cent) > 25000
    assert cent["constantinople"][0] > cent["rome"][0]   # east of Rome
    assert cent["cairo"][1] > cent["rome"][1]             # image y grows southward


import numpy as np


def test_projection_fit_is_accurate():
    cent = b.load_centroids()
    proj = b.fit_projection(cent)
    st = b.error_stats(b.fit_errors(proj, cent, b.ANCHORS))
    assert st["p95"] <= b.FIT_P95_MAX_PX, st
    assert b.fit_errors(proj, cent, b.HOLDOUT)["tunis"] <= b.FIT_P95_MAX_PX


def test_projection_roundtrip_and_monotonic():
    proj = b.fit_projection(b.load_centroids())
    x, y = b.to_pixel(proj, 41.9, 12.5)
    lon, lat = b.to_lonlat(proj, x, y)
    assert abs(lon - 12.5) < 0.01 and abs(lat - 41.9) < 0.01
    d = np.diff(np.polyval(proj[1], b._LAT))
    assert (d > 0).all() or (d < 0).all()


def _anc(region, area, prov):
    return ("cont", "sub", region, area, prov)


def test_overrides_later_line_wins_and_unknown_key_errors(tmp_path):
    f = tmp_path / "10_x.txt"
    f.write_text("!scope reg\narea1 = AAA  # note\nloc2 = none\nbogus = AAA\n")
    entries, scopes = b.load_overrides([f])
    anc = {"loc1": _anc("reg", "area1", "prov1"), "loc2": _anc("reg", "area1", "prov1"),
           "loc3": _anc("reg", "area2", "prov2")}
    ds = {"loc3": ("BBB", "dataset:X (within) -> BBB")}
    owner, trail, errors = b.assign(set(anc), anc, ds, entries)
    assert owner == {"loc1": "AAA", "loc2": "none", "loc3": "BBB"}
    assert scopes == {"reg"}
    assert errors == ["10_x.txt:4: unknown location/province/area/region 'bogus'"]
    assert trail["loc2"] == ["10_x.txt:2 area1 = AAA", "10_x.txt:3 loc2 = none"]


def test_coverage_flags_unsourced_only_in_scope():
    anc = {"a": _anc("reg", "ar", "p"), "c": _anc("other", "ar2", "p2")}
    errors, warnings = b.check_coverage({"a", "c"}, {}, anc, {"reg"})
    assert len(errors) == 1 and " a" in errors[0]
    assert len(warnings) == 1


def _tag(**kw):
    d = dict(name="N", adj="A", capital="-", template="t1", culture="c1", religion="r1", rgb=(1, 2, 3), line=1)
    d.update(kw)
    return d


def test_check_tags():
    tags = {"AAA": _tag(), "BYZ": _tag(), "bad": _tag(), "CCC": _tag(template="x", culture="x", religion="x", capital="nowhere")}
    errs = b.check_tags(tags, {"BYZ"}, {"t1"}, {"c1"}, {"r1"}, {"rome"})
    joined = "\n".join(errs)
    assert "AAA" not in joined
    assert "BYZ" in joined and "collides" in joined
    assert "bad" in joined
    for what in ("template", "culture", "religion", "capital"):
        assert f"CCC: unknown {what}" in joined


def test_check_tag_map_and_values():
    errs = b.check_tag_map({"Rome": "AAA", "Ghost": "none", "Persia": "ZZZ"}, {"Rome", "Persia", "Huns"}, {"AAA": _tag()})
    joined = "\n".join(errs)
    assert "'Huns' has no tag_map entry" in joined
    assert "'Ghost' is not in the dataset" in joined
    assert "ZZZ" in joined
    assert b.check_values([("f:1", "k", "QQQ"), ("f:2", "k", "none")], {"AAA": _tag()}) == ["f:1: undefined tag 'QQQ'"]


def test_resolve_capitals():
    tags = {"AAA": _tag(capital="rome"), "BBB": _tag(capital="-"), "CCC": _tag(capital="milano")}
    caps, warns, errs = b.resolve_capitals(tags, {"AAA": ["rome"], "BBB": ["x", "y"], "CCC": ["z"]})
    assert caps == {"AAA": "rome", "BBB": "x"}
    assert len(warns) == 1 and errs == ["CCC: capital 'milano' is not owned by CCC"]


def test_dataset_owner_within_and_nearest():
    from shapely.geometry import box
    geoms, names = [box(0, 0, 10, 10)], ["Rome"]
    got = b.dataset_owner({"in": (5, 5), "near": (10.5, 5), "far": (50, 50)}, geoms, names, {"Rome": "AAA"})
    assert got["in"][0] == "AAA" and "(within)" in got["in"][1]
    assert got["near"][0] == "AAA" and "(nearest)" in got["near"][1]
    assert "far" not in got


def test_emit_countries_lists_each_location_once():
    tags = {"AAA": _tag(template="catholic_monarchy"), "BBB": _tag(template="eurasian_tribe")}
    owned = {"AAA": ["l1", "l2"], "BBB": ["l3"]}
    text = b.emit_countries(tags, owned, {"AAA": "l1", "BBB": "l3"})
    body = re.findall(r"own_control_core = \{([^}]*)\}", text)
    locs = [l for blk in body for l in blk.split()]
    assert sorted(locs) == ["l1", "l2", "l3"]
    assert text.count("{") == text.count("}")
    assert 'include = "eurasian_tribe"' in text and "capital = l3" in text


def test_emit_definitions_and_localization():
    tags = {"AAA": _tag(name="Western Roman Empire", adj="Western Roman", culture="roman_culture", religion="catholic")}
    d = b.emit_definitions(tags)
    assert "AAA = {" in d and "culture_definition = roman_culture # PLACEHOLDER" in d
    loc = b.emit_localization(tags)
    assert loc.startswith("﻿l_english:\n")
    assert ' AAA: "Western Roman Empire"' in loc and ' AAA_ADJ: "Western Roman"' in loc


def test_resolve_capitals_skips_undefined_tags():
    # an override naming an undefined tag is reported by check_values; capitals must not crash on it
    caps, warns, errs = b.resolve_capitals({"AAA": _tag(capital="rome")}, {"AAA": ["rome"], "QQQ": ["x"]})
    assert caps == {"AAA": "rome"} and errs == [] and warns == []


def test_start_files_have_no_bom_but_country_definitions_do():
    # the start loader chokes on a BOM ("Unexpected token"); in_game/setup wants utf8-bom
    for f in START.glob("*.txt"):
        assert not f.read_bytes().startswith(b"\xef\xbb\xbf"), f.name
    assert b.DEFS_OUT.read_bytes().startswith(b"\xef\xbb\xbf")


def test_short_hex_colours_are_loaded():
    names = set(b.load_colors().values())
    assert {"kalmar", "lincoln"} <= names          # kalmar = 291f
    assert {"kalmar", "lincoln"} <= set(b.load_centroids())


def test_unownable_lists_loaded():
    un = b.load_unownable()
    assert {"pantelleria", "syrian_desert_corridor8", "lastovo_island_wasteland"} <= un
    assert "rome" not in un


def test_override_covering_no_land_and_scope_typo_error(tmp_path):
    anc = {"a1": ("r", "areaA"), "w1": ("r", "wasteA")}
    _, _, errs = b.assign({"a1"}, anc, {}, [("f:1", "wasteA", "AAA")])
    assert errs and "no ownable land" in errs[0]
    errs, _ = b.check_coverage({"a1"}, {"a1": "AAA"}, anc, {"bogus_region"})
    assert errs and "bogus_region" in errs[0]


def test_load_ranks_reports_unknown_rank_and_tag(tmp_path):
    f = tmp_path / "ranks.txt"
    f.write_text("rank_empire = AAA\nrank_emperor = BBB\nrank_duchy = ZZZ AAA\n")
    ranks, errs = b.load_ranks(f, {"AAA": _tag(), "BBB": _tag()}, {"rank_empire", "rank_duchy", "rank_county"})
    assert ranks["BBB"] == "rank_county"          # unlisted/invalid -> default
    assert any("rank_emperor" in e for e in errs)
    assert any("ZZZ" in e for e in errs)
    assert any("AAA" in e and "twice" in e for e in errs)


def test_discovered_regions_by_distance():
    anc = {"a": ("c", "s", "home_region", "x", "p"), "b": ("c", "s", "near_region", "x", "p"),
           "c": ("c", "s", "far_region", "x", "p"), "c2": ("c", "s", "far_region", "x", "p"),
           "wrap": ("c", "s", "far_region", "x", "p")}   # map-wrapping sea zone: centroid lands mid-map
    lonlat = {"a": (0.0, 0.0), "b": (5.0, 0.0), "c": (40.0, 0.0), "c2": (41.0, 0.0), "wrap": (1.0, 0.0)}
    disc = b.discovered_regions(anc, lonlat, {"AAA": ["a"]}, radius_deg=8)
    assert disc["AAA"] == ["home_region", "near_region"]


def test_emit_countries_writes_rank_and_discovery():
    text = b.emit_countries({"AAA": _tag()}, {"AAA": ["l1"]}, {"AAA": "l1"},
                            ranks={"AAA": "rank_empire"}, discovered={"AAA": ["r1", "r2"]})
    assert text.index("include =") < text.index("country_rank = rank_empire")   # after template: overrides it
    assert re.search(r"discovered_regions = \{\s*r1 r2\s*\}", text)
    assert text.count("{") == text.count("}")


def test_emit_countries_uses_government_lines():
    govs = {"AAA": ["ruler = c_a", "heir = c_b"]}
    text = b.emit_countries({"AAA": _tag(), "BBB": _tag()}, {"AAA": ["l1"], "BBB": ["l2"]}, {"AAA": "l1", "BBB": "l2"},
                            governments=govs)
    a, bb = text.split("BBB = {")
    assert "ruler = c_a" in a and "heir = c_b" in a and "ruler = random" not in a
    assert "ruler = random" in bb


def test_load_governments_groups_lines_and_flags_unlanded(tmp_path):
    f = tmp_path / "g.txt"
    f.write_text("AAA = ruler = c_a  # note\nAAA = heir = c_b\nZZZ = ruler = c_z\n", encoding="utf-8")
    govs, errs = b.load_governments(f, {"AAA": ["l1"]})
    assert govs == {"AAA": ["ruler = c_a", "heir = c_b"]}
    assert errs == ["g.txt:3: ZZZ owns no land"]


def test_splice_dynasties_keeps_vanilla_and_adds_ours():
    out = b.splice_dynasties("dynasty_manager = {\n\ta_dynasty = { }\n}\n", "\tb_dynasty = { }\n")
    assert out.index("a_dynasty") < out.index("b_dynasty") < out.rindex("}")
    assert out.count("{") == out.count("}")
