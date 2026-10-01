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


def test_a_saved_scope_and_a_target_flag_count_as_saved(tmp_path):
    files = {"in_game/events/t.txt": EVENT % "save_scope_as = w scope:w = { kill = yes } scope:t = { kill = yes }",
             "in_game/common/generic_actions/t.txt": "a = { target_flag = t }\n", LOC_FILE: LOC}
    assert refs(tmp_path, files) == []


def test_an_override_of_a_vanilla_building_uses_the_vanilla_icon(tmp_path):
    # REPLACE:x names vanilla's x, whose icon is x.dds (MAZZO313's Theodosian Walls)
    files = {"in_game/common/building_types/t.txt": "REPLACE:theodosian_walls = { }\n", LOC_FILE: LOC}
    assert not [p for p in refs(tmp_path, files) if "icon" in p]
