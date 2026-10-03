"""The typed Event builder: script/gildo_events.py reproduces in_game/events/tfe_gildo.txt and its yml."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))
import gildo_events  # noqa: E402
import lint_script as ls  # noqa: E402

EVENTS, YML = "in_game/events/tfe_gildo.txt", "main_menu/localization/english/tfe_gildo_l_english.yml"
OUT = gildo_events.outputs()


def tree(entries):
    return [(e.key, e.op, tree(e.val) if isinstance(e.val, list) else e.val) for e in entries]


def yml(text):
    return dict(re.findall(r'^ (\S+): "(.*)"$', text, re.M))


def test_script_parses_equal_to_the_committed_file():
    assert tree(ls.parse(OUT[EVENTS])) == tree(ls.parse((ROOT / EVENTS).read_text(encoding="utf-8-sig")))


def test_localisation_keys_equal_the_committed_yml():
    got, want = yml(OUT[YML]), yml((ROOT / YML).read_text(encoding="utf-8-sig"))
    bad = {k for k in got.keys() | want.keys() if got.get(k) != want.get(k)}
    assert not bad, {k: (got.get(k), want.get(k)) for k in bad}
    assert OUT[YML].startswith("l_english:\n")


def test_generated_events_lint_clean():
    if not (ls.DOCS / "effects.log").exists():
        pytest.skip("no script docs")
    lin = ls.Linter(ls.Knowledge([ls.b.GAME, ls.b.MOD]))
    lin.walk(EVENTS, ls.parse(OUT[EVENTS]), "other")
    assert lin.found == []


def pyright(tmp_path, path):
    """the error diagnostics pyright reports for path (skips the test when pyright cannot run)."""
    (tmp_path / "pyrightconfig.json").write_text(json.dumps({"extraPaths": [str(ROOT / "tools"), str(ROOT / "script")]}))
    try:
        r = subprocess.run([sys.executable, "-m", "pyright", "--outputjson", str(path)], cwd=tmp_path, capture_output=True, text=True, timeout=300)
        return [d for d in json.loads(r.stdout)["generalDiagnostics"] if d["severity"] == "error"]
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as e:
        pytest.skip(f"pyright cannot run here ({e!r}); use `uv run --with pyright`")


def test_pyright_clean_over_gildo_events(tmp_path):
    assert pyright(tmp_path, ROOT / "script/gildo_events.py") == []


def test_bad_outcome_is_a_pyright_error_and_raises_at_build(tmp_path):
    from pdx.objects import Doc
    d = Doc()
    d.namespace("x")
    with pytest.raises(ValueError):
        with d.event(1, type="country_event", title="t", desc="d", outcome="bad"):  # pyright: ignore
            pass
    f = tmp_path / "bad.py"
    f.write_text("from pdx.objects import Doc\nd = Doc()\nwith d.event(1, type='country_event', title='t', desc='d', outcome='bad'):\n    pass\n")
    errs = pyright(tmp_path, f)
    assert len(errs) == 1 and "outcome" in errs[0]["message"], errs


def test_hidden_event_needs_no_text_and_can_fire_once_with_an_after_block():
    from pdx.objects import Doc
    d = Doc()
    d.namespace("x")
    with d.event(1, type="country_event", hidden=True, fire_only_once=True) as e:
        with e.immediate() as i:
            i.add_gold(1)
        with e.after() as a:
            a.add_gold(2)
    assert d.loc.keys == {}
    tree = [(c.key, c.val if isinstance(c.val, str) else "{}") for c in ls.parse(d.text())[1].val]
    assert tree == [("type", "country_event"), ("hidden", "yes"), ("fire_only_once", "yes"), ("immediate", "{}"), ("after", "{}")]


def test_a_visible_event_still_needs_text_and_an_outcome():
    from pdx.objects import Doc
    d = Doc()
    d.namespace("x")
    for kw in ({"desc": "d", "outcome": "neutral"}, {"title": "t", "outcome": "neutral"}, {"title": "t", "desc": "d"}):
        with pytest.raises(ValueError):
            with d.event(1, type="country_event", **kw):  # pyright: ignore
                pass


def _same_entry(doc, committed, name):
    tree = lambda es: [(e.key, e.op, tree(e.val) if isinstance(e.val, list) else e.val) for e in es]
    want = [e for e in ls.parse((ROOT / committed).read_text(encoding="utf-8-sig")) if e.key == name]
    assert tree(ls.parse(doc.text())) == tree(want)


def test_a_static_modifier_builder_matches_the_committed_entry():
    from pdx.objects import Doc
    d = Doc()
    d.modifier("tfe_eutropius_chamber", category="country", tax_income_efficiency=0.05, land_morale_modifier=-0.05)
    _same_entry(d, "main_menu/common/static_modifiers/tfe_opening.txt", "tfe_eutropius_chamber")


def test_an_auto_modifier_builder_matches_the_committed_entry():
    from pdx.objects import Doc
    d = Doc()
    def either_west(t):
        with t.or_() as o:
            o.has_or_had_tag("WRE")
            o.has_variable("tfe_western_rome")
    d.modifier("tfe_comitatenses", potential=either_west, discipline=0.05)
    _same_entry(d, "in_game/common/auto_modifiers/tfe_late_roman_west.txt", "tfe_comitatenses")


@pytest.mark.skipif(not (ls.DOCS / "modifiers.log").exists(), reason="no script_docs logs")
def test_a_bias_builder_and_a_misspelt_modifier_key():
    from pdx.objects import Doc
    d = Doc()
    d.bias("tfe_foederati_subject_opinion", 0)
    _same_entry(d, "in_game/common/biases/tfe_biases.txt", "tfe_foederati_subject_opinion")
    with pytest.raises(ValueError, match="not a modifier key"):
        Doc().modifier("x", land_morale_modifer=0.1)


def test_a_bias_takes_its_extra_keys_in_the_order_given():
    from pdx.objects import Doc
    d = Doc()
    d.bias("a", 50, max=50, yearly_decay=5)
    d.bias("b", -75, yearly_decay=3, min=-75)
    a, b = ls.parse(d.text())
    assert [(c.key, c.val) for c in a.val] == [("value", "50"), ("max", "50"), ("yearly_decay", "5")]
    assert [c.key for c in b.val] == ["value", "yearly_decay", "min"]
    with pytest.raises(ValueError, match="not a bias key"):
        d.bias("c", 1, yearly_dcay=1)  # pyright: ignore


def test_a_select_trigger_builder_matches_the_committed_action():
    from pdx.api import SituationTrig
    from pdx.objects import Doc
    d = Doc()
    with d.generic_action("x") as a:
        with a.select_trigger("situation", SituationTrig, name="choose_situation", source="situation:tfe_hunnic_storm") as t:
            t.compare("situation:tfe_hunnic_storm", "=", "this")
            t.situation_is_active(True)
    tree = lambda es: [(e.key, e.op, tree(e.val) if isinstance(e.val, list) else e.val) for e in es]
    want = next(e for e in ls.parse((ROOT / "in_game/common/generic_actions/tfe_hunnic_storm.txt").read_text(encoding="utf-8-sig"))
                for c in e.val if c.key == "select_trigger")
    have = ls.parse(d.text())[0].val[0]
    assert tree([have]) == tree([next(c for c in want.val if c.key == "select_trigger")])


def test_a_comparison_inside_a_block_keeps_its_operator():
    from pdx.api import LocationTrig
    from pdx.core import Cmp
    nodes = []
    LocationTrig(nodes).religion_percentage(religion="religion:donatism", value=Cmp(">=", 0.25))
    e = ls.parse(__import__("pdx.core", fromlist=["render"]).render(nodes))[0]
    assert [(c.key, c.op, c.val) for c in e.val] == [("religion", "=", "religion:donatism"), ("value", ">=", "0.25")]
    with pytest.raises(ValueError):
        Cmp("=>", 1)


def test_a_decision_writes_vanillas_shape_and_its_loc_keys(tmp_path):
    from pdx.objects import Doc
    d = Doc()
    d.decision_category("cat", title="Cat", sort_order=0)
    with d.decision("x", category="cat", title="T", desc="D", only_once=True) as x:
        with x.potential() as t:
            t.at_war(False)
        with x.ai_will_do() as v, v.if_() as i:
            with i.limit() as t:
                t.gold(10, op=">=")   # a country trigger: the root of a decision's ai_will_do is the country
            i.add(1)
        with x.option("a", text="A") as o, o.effect() as e:
            e.add_gold(1)
    assert d.loc.keys == {"cat": "Cat", "x.title": "T", "x.desc": "D", "x.a": "A"}
    cat, dec = ls.parse(d.text())
    assert [(c.key, c.val) for c in cat.val] == [("name_key", "cat"), ("sort_order", "0")]
    assert [c.key for c in dec.val] == ["decision_category", "only_once", "potential", "ai_will_do", "option"]
    opt = dec.val[-1].val
    assert [c.key for c in opt] == ["name", "ai_chance", "effect"] and opt[0].val == "x.a"
    f = tmp_path / "bad.py"
    f.write_text("from pdx.objects import Doc\nd = Doc()\nwith d.decision('x', category='c', title='t', desc='d') as x:\n"
                 "    with x.option('a', text='a') as o, o.effect() as e:\n        e.is_capital(True)\n")
    errs = pyright(tmp_path, f)
    assert len(errs) == 1 and "is_capital" in errs[0]["message"], errs   # a trigger in an option's effect
