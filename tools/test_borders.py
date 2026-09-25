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
