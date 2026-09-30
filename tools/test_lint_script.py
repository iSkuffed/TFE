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
