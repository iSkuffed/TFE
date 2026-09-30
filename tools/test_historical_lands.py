"""Historical lands: each migrating people's AI conquest preference and the tfe_is_historical_land_of trigger
(script/defs_historical_lands.py)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))
import borders as b
import defs_decline_of_the_west as west
import defs_historical_lands as h


def code(rel):
    return re.sub(r"#[^\n]*", "", (ROOT / rel).read_text(encoding="utf-8-sig"))


def test_every_area_is_a_vanilla_area():
    vanilla = set(re.findall(r"\b(\w+_area)\s*=\s*\{", (b.MAP / "definitions.txt").read_text(encoding="utf-8-sig")))
    bad = {f"{t}: {a}" for t, areas in h.HISTORICAL_LANDS.items() for a in areas if f"{a}_area" not in vanilla}
    assert not bad, sorted(bad)


def test_tags_are_tfe_migrators():
    assert set(h.HISTORICAL_LANDS) <= set(b.load_tags())
    assert set(h.HISTORICAL_LANDS) <= set(west.MIGRATORS)


def test_setup_trigger_and_preferences_cover_every_tag():
    setup, trig, prefs = code(h.SETUP_FILE), code(h.TRIG_FILE), code(h.PREF_FILE)
    for tag, areas in h.HISTORICAL_LANDS.items():
        assert re.search(rf"\b{tag}\s*=\s*\{{\s*area_preferences\s*=\s*\{{\s*{h.pref(tag)}\s*\}}", setup), tag
        assert f"tag = {tag}" in trig, tag
        body = re.search(rf"{h.pref(tag)}\s*=\s*\{{([^}}]*)\}}", prefs)
        assert body and set(re.findall(r"area = (\w+)", body[1])) == {f"{a}_area" for a in areas}, tag
        assert all(f"this = area:{a}_area" in trig for a in areas), tag
    for text in (setup, trig, prefs):
        assert text.count("{") == text.count("}")

