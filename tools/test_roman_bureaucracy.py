"""The Roman state keeps three offices: the Sacrae Largitiones (tax), the Magister Officiorum (court) and the Magister Peditum (army)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b
import lint_script

FILE = b.MOD / "in_game/common/bureaucracies/tfe_roman.txt"
SLOTS = b.MOD / "in_game/common/auto_modifiers/tfe_roman_bureaucracy.txt"
TYPES = b.MOD / "main_menu/common/modifier_type_definitions/tfe_bureaucracies.txt"
ICONS = b.MOD / "main_menu/common/modifier_icons/tfe_modifier_icons.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_bureaucracies_l_english.yml"
ICON_DIR = b.MOD / "main_menu/gfx/interface/icons/bureaucracy"
NAMES = ("tfe_sacrae_largitiones_bureaucracy", "tfe_magister_officiorum_bureaucracy", "tfe_magister_peditum_bureaucracy")


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def block(text, head):
    """the `{ ... }` body that follows `head` (brace-matched)"""
    i = text.index("{", text.index(head))
    depth = 0
    for j in range(i, len(text)):
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        if depth == 0:
            return text[i + 1:j]
    raise ValueError(head)


def entries():
    text = code(FILE)
    return {n: block(text, f"{n} = ") for n in NAMES}


def values(body):
    """{key: float} of the `key = number` lines of a modifier block"""
    body = re.sub(r"scale = \{[^}]*\}", "", body)   # its `value = 1` is the scale, not a modifier
    return {k: float(v) for k, v in re.findall(r"^\s*(\w+) = (-?[\d.]+)\s*$", body, re.M)}


def test_three_offices_with_every_block_the_game_reads():
    for name, body in entries().items():
        for part in ("implementation_price", "maintenance_price", "removal_price", "potential", "estates_that_like",
                     "estates_that_dislike", "neutral_modifier", "positive_modifier", "negative_modifier"):
            assert part in body, (name, part)
        assert "scale = { value = scope:maintenance }" in " ".join(block(body, "positive_modifier").split()), name
        assert "subtract = scope:maintenance" in block(body, "negative_modifier"), name
        assert "has_dlc" not in body, name   # RoadMap: rebuild Roman content, don't depend on the DLC


def test_modifier_keys_exist_and_negative_sides_flip_the_positive_ones():
    known = set(re.findall(r"^Tag: (\w+),", (lint_script.DOCS / "modifiers.log").read_text(encoding="utf-8-sig"), re.M))
    for name, body in entries().items():
        pos, neg = values(block(body, "positive_modifier")), values(block(body, "negative_modifier"))
        for k in {**values(block(body, "neutral_modifier")), **pos, **neg}:
            assert k in known, (name, k)
        shared = set(pos) & set(neg)
        assert shared, name
        for k in shared:
            assert pos[k] * neg[k] < 0, (name, k)


def test_the_three_stats_each_office_was_asked_for():
    e = entries()
    tax, court, army = (values(block(e[n], "positive_modifier")) for n in NAMES)
    assert {"global_estate_max_tax", "global_estate_target_satisfaction"} <= set(tax)
    assert {"monthly_political_influence_gain_modifier", "global_distance_from_capital_speed_propagation"} <= set(court)
    assert "discipline" in army and army["army_maintenance_efficiency"] < 0   # drill makes the regiments dearer


def test_every_office_is_named_drawn_and_has_its_impact_modifier():
    loc = LOC.read_text(encoding="utf-8-sig")
    assert LOC.read_bytes().startswith(b"\xef\xbb\xbf") and FILE.read_bytes().startswith(b"\xef\xbb\xbf")
    for n in NAMES:
        assert re.search(rf"^ {n}: \"", loc, re.M) and re.search(rf"^ {n}_desc: \"", loc, re.M), n
        assert f"MODIFIER_TYPE_NAME_{n}_impact_modifier" in loc and f"MODIFIER_TYPE_DESC_{n}_impact_modifier" in loc, n
        assert (ICON_DIR / f"{n}.dds").exists(), n
        assert f"{n}_impact_modifier = {{" in code(TYPES) and f"{n}_impact_modifier = {{" in code(ICONS), n


def test_both_empires_get_three_slots():
    t = " ".join(code(SLOTS).split())
    assert "global_max_bureaucracy_slots = 3" in t
    assert all(x in t for x in ("has_or_had_tag = WRE", "has_variable = tfe_western_rome", "has_or_had_tag = EAR"))
