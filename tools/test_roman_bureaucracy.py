"""The Roman state keeps three offices: the Sacrae Largitiones (tax), the Magister Officiorum (court) and the Magister
Peditum (army), written by script/bureaucracies.py through Doc.bureaucracy."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))
import bureaucracies
import lint_script
from pdx.objects import Doc

NAMES = ("tfe_sacrae_largitiones_bureaucracy", "tfe_magister_officiorum_bureaucracy", "tfe_magister_peditum_bureaucracy")
needs_docs = pytest.mark.skipif(not (lint_script.DOCS / "modifiers.log").exists(), reason="no script_docs logs")


def keys(doc, name, block):
    """{key: value} of one modifier block of one office, its scale left out"""
    top = next(n for n in doc.nodes if n.key == name)
    return {c.key: c.val for c in next(c for c in top.val if c.key == block).val if c.key != "scale"}


def test_the_three_stats_each_office_was_asked_for():
    doc = bureaucracies.offices()
    tax, court, army = (keys(doc, n, "positive_modifier") for n in NAMES)
    assert {"global_estate_max_tax", "global_estate_target_satisfaction"} <= set(tax)
    assert {"monthly_political_influence_gain_modifier", "global_distance_from_capital_speed_propagation"} <= set(court)
    assert "discipline" in army and float(army["army_maintenance_efficiency"]) < 0   # drill makes the regiments dearer
    for n in NAMES:
        assert set(keys(doc, n, "positive_modifier")) & set(keys(doc, n, "negative_modifier")), n   # neglect undoes something
    assert not doc.find("has_dlc")   # RoadMap: rebuild Roman content, don't depend on the DLC


def test_every_office_has_its_scales_icon_impact_modifier_and_loc():
    doc = bureaucracies.offices()
    for n in NAMES:
        assert doc.find("value", "scope:maintenance", inside=(n, "positive_modifier", "scale"))
        assert doc.find("subtract", "scope:maintenance", inside=(n, "negative_modifier", "scale"))
        assert (ROOT / f"main_menu/gfx/interface/icons/bureaucracy/{n}.dds").exists(), n
        assert doc.types.find(f"{n}_impact_modifier") and doc.icons.find(f"{n}_impact_modifier"), n
        assert {n, f"{n}_desc", f"MODIFIER_TYPE_NAME_{n}_impact_modifier", f"MODIFIER_TYPE_DESC_{n}_impact_modifier"} <= set(doc.loc.keys)


def test_both_empires_get_three_slots():
    doc = bureaucracies.slots()
    assert doc.find("global_max_bureaucracy_slots", 3)
    assert doc.find("tfe_is_roman_empire", True, inside=("tfe_roman_bureaucracy_slots", "potential_trigger"))


def office(**kw):
    args = dict(title="t", desc="d", potential=lambda t: t.always(True), likes=["crown_estate"], dislikes=[],
                neutral={"monthly_legitimacy": 0.05}, positive={"discipline": 0.05}, negative={"discipline": -0.05})
    d = Doc()
    d.bureaucracy("tfe_x_bureaucracy", **{**args, **kw})
    return d


def test_the_builder_refuses_an_office_whose_neglect_does_not_flip_or_that_no_estate_likes():
    office()
    with pytest.raises(ValueError, match="flip"):
        office(negative={"discipline": 0.05})
    with pytest.raises(ValueError, match="estate"):
        office(likes=[])


@needs_docs
def test_the_builder_refuses_a_misspelt_modifier_key():
    with pytest.raises(ValueError, match="discipln"):
        office(positive={"discipln": 0.05}, negative={})


def test_pyright_rejects_a_misspelt_modifier_key(tmp_path):
    src = ("from pdx.objects import Doc\nd = Doc()\n"
           "d.bureaucracy('x', title='t', desc='d', potential=lambda t: t.always(True), likes=['crown_estate'], dislikes=[],\n"
           "              neutral={}, positive={'discipline': 0.05}, negative={'discipln': -0.05})  # BAD\n"
           "d.modifier('y', global_max_bureaucracy_slots=3)\nd.modifier('z', global_max_bureaucracy_slot=3)  # BAD\n")
    (tmp_path / "pyrightconfig.json").write_text(json.dumps({"extraPaths": [str(ROOT / "tools")]}))
    (tmp_path / "x.py").write_text(src)
    try:
        r = subprocess.run([sys.executable, "-m", "pyright", "--outputjson", "x.py"], cwd=tmp_path, capture_output=True,
                           text=True, timeout=300)
        errs = [d for d in json.loads(r.stdout)["generalDiagnostics"] if d["severity"] == "error"]
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as e:
        pytest.skip(f"pyright cannot run here ({e!r}); use `uv run --with pyright`")
    lines = {d["range"]["start"]["line"] + 1 for d in errs}
    assert lines == {i for i, l in enumerate(src.splitlines(), 1) if "# BAD" in l}, errs


def test_both_empires_start_with_all_three_offices_old_and_half_funded():
    on_action = " ".join((ROOT / "in_game/common/on_action/tfe_roman_bureaucracy.txt").read_text(encoding="utf-8-sig").split())
    assert "on_game_start" in on_action and "tfe_on_start_roman_bureaucracy" in on_action
    assert all(f"add_bureaucracy = bureaucracy_type:{n}" in on_action for n in NAMES)
    assert "set_entrenchment = 60" in on_action and "set_maintenance = 0.5" in on_action
    assert "tfe_is_western_rome = yes" in on_action and "has_or_had_tag = EAR" in on_action
