import re
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent
START = MOD / "main_menu/setup/start"
STUBS = ["05_characters", "07_cities_and_buildings", "11_art", "12_diplomacy", "13_religion",
         "15_international_organizations", "16_wars", "18_opinions", "20_rivals", "23_colonies",
         "25_area_preferences", "26_ai_personalities", "27_armies"]


def test_stubs_have_no_tag_references():
    for name in STUBS:
        text = (START / f"{name}.txt").read_text(encoding="utf-8-sig")
        code = re.sub(r"#[^\n]*", "", text)
        assert code.count("{") == code.count("}"), name
        assert not re.search(r"\b(tag|country|first|second)\s*=\s*[A-Z][A-Z0-9]{2}\b", code), name


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
