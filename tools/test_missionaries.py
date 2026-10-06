"""The Christianisation of Europe (RoadMap #30): Nicene and Arian movements, missionaries who walk to a pagan place and
preach there, two decisions and a conversion event. Static checks on what script/missionaries.py writes."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
sys.path.insert(0, str(ROOT / "tools"))
import missionaries as m  # noqa: E402
import borders as b  # noqa: E402

OUT = m.outputs()
MOV = OUT["in_game/common/movements/tfe_christianisation.txt"]
TRIG = OUT["in_game/common/scripted_triggers/tfe_christianisation.txt"]
LOC = OUT["main_menu/localization/english/tfe_christianisation_l_english.yml"]
TYPES = OUT["main_menu/common/modifier_type_definitions/tfe_christianisation.txt"]


def religions():
    files = [*(b.GAME / "in_game/common/religions").glob("*.txt"), ROOT / "in_game/common/religions/tfe_religions.txt"]
    return {k for p in files for k in re.findall(r"^(?:REPLACE:)?(\w+)\s*=\s*\{", p.read_text(encoding="utf-8-sig"), re.M)}


def locations():
    text = (ROOT / "in_game/map_data/location_templates.txt").read_text(encoding="utf-8-sig")
    return set(re.findall(r"^(\w+)\s*=", text, re.M))


def test_every_faith_named_exists():
    known = religions()
    for faith, converts in m.CONVERTS.items():
        assert faith in known, faith
        assert not set(converts) - known, set(converts) - known


def test_each_movement_converts_its_list_and_the_rival_only_as_a_minority():
    for faith, key in m.MOVEMENT.items():
        names = [n.key for n in m.MOVEMENTS.find(None, None, inside=(key, "required_religions"))]
        assert names == list(m.CONVERTS[faith]), key
    assert m.ARIAN in m.CONVERTS[m.NICENE] and m.NICENE in m.CONVERTS[m.ARIAN]
    assert "celtic_paganism" not in m.CONVERTS[m.ARIAN]  # Gaul's Celts are left to the Nicenes


def test_every_pop_type_has_a_multiplier():
    """a movement skips pop types it does not list (movements/readme.txt)"""
    for key in m.MOVEMENT.values():
        listed = {n.val for n in m.MOVEMENTS.find("pop_type", None, inside=(key, "specific_pop_type_effect"))}
        assert listed == set(m.POP_TYPES), key


def test_arians_never_convert_nicenes_under_a_nicene_king():
    r0 = MOV.split("tfe_arian_movement", 1)[1].split("calc_interval_days", 1)[0]
    assert "multiply = 0" in r0 and "religion:orthodox" in r0 and "religion:arianism" in r0


def test_the_cult_centres_exist_and_resist():
    known = locations()
    for loc in m.CULT_CENTRES + m.SEES:
        assert loc in known, loc
    assert all(f"location:{c}" in MOV for c in m.CULT_CENTRES)


def test_growth_modifiers_have_a_type_and_a_name():
    for key in m.MOVEMENT.values():
        for scope in ("local", "national"):
            mod = f"{scope}_{key}_growth_modifier"
            assert f"{mod} = {{" in TYPES, mod
            assert f"MODIFIER_TYPE_NAME_{mod}:" in LOC, mod


def test_the_pagan_trigger_lists_every_pagan():
    for faith in m.PAGANS:
        assert f"religion:{faith}" in TRIG, faith
