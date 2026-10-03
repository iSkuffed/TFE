"""The script linter: our own files are clean, and each trap it claims to catch is caught."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b
import lint_script as ls

pytestmark = pytest.mark.skipif(not (ls.DOCS / "effects.log").exists(), reason="no script_docs logs")


def problems(text, ctx="other"):
    lin = ls.Linter(ls.Knowledge([b.GAME, b.MOD]))
    lin.walk("t.txt", ls.parse(text), ctx)
    return lin.found


def test_mod_script_is_clean():
    assert ls.lint() == []


@pytest.mark.parametrize("text, expect", [
    ("e = { immediate = { add_country_modifier = { name = x years = 5 } } }", "takes `modifier =`"),
    ("e = { outcome = good }", "outcome = good"),
    ("e = { trigger = { exists = c:ROM } }", "country_exists"),
    ("e = { immediate = { add_gold_typo = 5 } }", "unknown effect `add_gold_typo`"),
    ("e = { trigger = { is_a_made_up_thing = yes } }", "unknown trigger `is_a_made_up_thing`"),
    ("e = { immediate = { add_country_modifier = { modifier = no_such_modifier years = 5 } } }", "not defined"),
    ("e = { immediate = { every_neighbor_country = { limit = { nope = yes } } } }", "unknown trigger `nope`"),
])
def test_traps_are_caught(text, expect):
    assert any(expect in p for p in problems(text)), problems(text)


OFFICE = """x_bureaucracy = {
    potential = { always = yes }
    on_activate = { add_gold_typo = 5 }
    neutral_modifier = { monthly_legitimacy = 0.05 }
    positive_modifier = { scale = { value = scope:maintenance } discipline = 0.05 global_estate_max_tax = 0.05 }
    negative_modifier = { scale = { value = 1 subtract = scope:maintenance } discipline = 0.05 global_estate_max_tx = -0.05 }
}"""


def test_a_bureaucracy_has_real_keys_flips_its_neglect_and_checks_its_effects():
    lin = ls.Linter(ls.Knowledge([b.GAME, b.MOD]))
    tree = ls.parse(OFFICE)
    lin.walk("t.txt", tree, "other")
    ls.bureaucracy_problems(lin, "t.txt", tree)
    found = " | ".join(lin.found)
    assert "unknown effect `add_gold_typo`" in found and "global_estate_max_tx is not a modifier key" in found, found
    assert "discipline is 0.05 funded and 0.05 neglected" in found and len(lin.found) == 3, found


def test_valid_script_passes():
    ok = "e = { outcome = neutral trigger = { NOT = { has_variable = x } } immediate = { if = { limit = { var:x > 1 } set_variable = y } } }"
    assert problems(ok) == []


def test_unbalanced_braces_are_an_error():
    with pytest.raises(ValueError):
        ls.parse("a = { b = c")
    with pytest.raises(ValueError):
        ls.parse("a = b }")


# --- cross-references (tools/lint_refs.py) -----------------------------------------------------------------------

import lint_refs


def refs(tmp_path, files):
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8-sig")
    return lint_refs.refs(tmp_path, [b.GAME, tmp_path])


EVENT = 'namespace = t\nt.1 = { title = t.1.title desc = t.1.desc option = { name = t.1.a %s } }\n'
LOC = 'l_english:\n t.1.title: "T"\n t.1.desc: "D"\n t.1.a: "A"\n'
LOC_FILE = "main_menu/localization/english/t_l_english.yml"


def test_a_complete_event_is_clean(tmp_path):
    assert refs(tmp_path, {"in_game/events/t.txt": EVENT % "", LOC_FILE: LOC}) == []


@pytest.mark.parametrize("files, expect", [
    ({"in_game/events/t.txt": EVENT % "trigger_event_silently = t.9", LOC_FILE: LOC}, "event t.9 is not defined"),
    ({"in_game/events/t.txt": EVENT % "", LOC_FILE: LOC.replace(" t.1.a", " t.1.b")}, "localisation key t.1.a is missing"),
    ({"in_game/events/t.txt": EVENT % "scope:ghost = { kill = yes }", LOC_FILE: LOC}, "scope:ghost is never saved"),
    ({"in_game/common/building_types/t.txt": "tfe_no_icon = { }\n"}, "tfe_no_icon has no icon"),
    ({"in_game/common/on_action/t.txt": "a = { effect = { trigger_event = { id = t.4 } } }\n"}, "event t.4 is not defined"),
])
def test_dangling_references_are_caught(tmp_path, files, expect):
    assert any(expect in p for p in refs(tmp_path, files)), refs(tmp_path, files)


def test_a_bureaucracy_needs_its_icon(tmp_path):
    found = refs(tmp_path, {"in_game/common/bureaucracies/t.txt": "tfe_iconless_bureaucracy = { }"})
    assert any("bureaucracies tfe_iconless_bureaucracy has no icon" in p for p in found), found


def test_a_saved_scope_and_a_target_flag_count_as_saved(tmp_path):
    files = {"in_game/events/t.txt": EVENT % "save_scope_as = w scope:w = { kill = yes } scope:t = { kill = yes }",
             "in_game/common/generic_actions/t.txt": "a = { target_flag = t }\n", LOC_FILE: LOC}
    assert refs(tmp_path, files) == []


def test_an_override_of_a_vanilla_building_uses_the_vanilla_icon(tmp_path):
    # REPLACE:x names vanilla's x, whose icon is x.dds (MAZZO313's Theodosian Walls)
    files = {"in_game/common/building_types/t.txt": "REPLACE:theodosian_walls = { }\n", LOC_FILE: LOC}
    assert not [p for p in refs(tmp_path, files) if "icon" in p]


def e(body):
    return {"in_game/events/t.txt": EVENT % body, LOC_FILE: LOC}


@pytest.mark.parametrize("body, expect", [
    ("has_advance = no_such_advance", "no_such_advance is not defined in advances"),
    ("research_advance = advance_type:no_such_advance", "no_such_advance is not defined in advances"),
    ("research_advance = taxation_advance", "vanilla writes this as `advance_type:taxation_advance`"),
    ("make_subject_of = { target = scope:x type = subject_type:tfe_foedrati }", "tfe_foedrati is not defined in subject_types"),
    ("add_pop = { type = pop_type:nobles_typo culture = x religion = y size = 1 }", "nobles_typo is not defined in pop_types"),
])
def test_a_value_vanilla_takes_from_a_registry_must_name_a_key_in_the_right_form(tmp_path, body, expect):
    assert any(expect in p for p in refs(tmp_path, e(body))), refs(tmp_path, e(body))


def test_the_mods_own_keys_count_and_real_values_pass(tmp_path):
    files = e("has_advance = taxation_advance research_advance = advance_type:taxation_advance has_advance = tfe_own_advance")
    files["in_game/common/advances/t.txt"] = "tfe_own_advance = { }\n"
    assert refs(tmp_path, files) == []
