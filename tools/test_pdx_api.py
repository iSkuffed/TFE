"""tools/pdx/api.py is generated and current, and its scope types catch a wrong-scope call."""
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "pdx"))
import gen_api
from lint_script import DOCS, parse
from pdx import api
from pdx.core import render

needs_docs = pytest.mark.skipif(not (DOCS / "effects.log").exists(), reason=f"no docs at {DOCS} (run `script_docs` in the game)")


@pytest.fixture(scope="module")
def generated():
    return gen_api.generate()[0]


@needs_docs
def test_api_is_up_to_date(generated):
    assert gen_api.OUT.read_text(encoding="utf-8") == generated, "run `python tools/pdx/gen_api.py`"


@needs_docs
def test_generation_is_deterministic(generated):
    assert gen_api.generate()[0] == generated


def test_add_country_modifier_takes_modifier_not_name():
    params = inspect.signature(api.CountryFx.add_country_modifier).parameters
    assert "modifier" in params and "name" not in params
    out = []
    api.CountryFx(out).add_country_modifier(modifier="x", years=5)
    assert render(out) == "add_country_modifier = {\n\tmodifier = x\n\tyears = 5\n}\n"


def test_comparison_trigger_takes_value_and_optional_op():
    params = inspect.signature(api.CountryTrig.gold).parameters
    assert params["op"].default == "="
    out = []
    api.CountryTrig(out).gold(100, op=">=")
    api.CountryTrig(out).gold(5)
    api.AnyTrig(out).current_date("395.2.18", op=">=")
    api.CountryTrig(out).at_war(False)
    assert render(out) == "gold >= 100\ngold = 5\ncurrent_date >= 395.2.18\nat_war = no\n"


def test_custom_tooltip_in_both_lists():
    assert hasattr(api.AnyFx, "custom_tooltip") and hasattr(api.AnyTrig, "custom_tooltip")
    assert issubclass(api.CountryFx, api.AnyFx) and issubclass(api.LocationTrig, api.AnyTrig)


def test_structure_keeps_the_scope_class():
    out = []
    with api.CountryFx(out).if_() as i:
        with i.limit() as t:
            assert isinstance(t, api.CountryTrig)
        assert isinstance(i, api.CountryFx)
    with api.CountryFx(out).go_capital() as loc:
        assert isinstance(loc, api.LocationFx)


def dump(entries):
    return [(e.key, e.op, dump(e.val) if isinstance(e.val, list) else e.val) for e in entries]


def same(out, text):
    """the nodes in `out` parse to the same tree as `text` (layout is render()'s business, not the API's)"""
    return dump(parse(render(out))) == dump(parse(text))


def test_scripted_effects_and_triggers_are_any_scope_methods():
    t, e = [], []
    api.CountryTrig(t).tfe_is_migrator()
    api.LocationTrig(t).tfe_frontier_unmanned(False)
    api.AnyFx(e).tfe_start_migration_effect()
    assert render(t) == "tfe_is_migrator = yes\ntfe_frontier_unmanned = no\n" and render(e) == "tfe_start_migration_effect = yes\n"
    assert hasattr(api.AnyTrig, "tfe_is_under_the_yoke") and hasattr(api.AnyFx, "tfe_start_migration_effect")


def test_scripted_call_with_a_parameter_block():
    out = []
    api._scripted(api.AnyFx(out), "x", None, {"a": 1, "b": None})
    api._scripted(api.AnyFx(out), "y", None, {})
    api._scripted(api.AnyFx(out), "z", "no", {})
    assert same(out, "x = { a = 1 } y = yes z = no")
    assert any("_scripted(self" in l for l in inspect.getsource(api).splitlines()), "no scripted effect with parameters generated"


def test_value_blocks():
    out = []
    v = api.ValueFx(out)
    v.value(0)
    with v.if_() as i:
        with i.limit() as t:
            assert type(t) is api.AnyTrig
            t.var("tfe_unity", "<", 50)
        i.add(5)
        with i.modifier() as m:
            m.factor(0.5)
            m.tfe_is_migrator()
    with v.add_block() as a:
        a.value("gold")
        a.multiply(2)
    assert same(out, "value = 0 if = { limit = { var:tfe_unity < 50 } add = 5 modifier = { factor = 0.5 tfe_is_migrator = yes } }"
                     " add = { value = gold multiply = 2 }")


def test_limit_opens_the_matching_trigger_class():
    scopes = {n[:-2] for n in dir(api) if n.endswith("Fx") and n not in ("AnyFx", "ValueFx")}
    bad = [s for s in scopes if not hasattr(api, s + "Trig")
           or inspect.signature(getattr(api, s + "Fx").limit).return_annotation != f"ContextManager[{s}Trig]"]
    assert not bad, bad
    assert inspect.signature(api.AnyFx.limit).return_annotation == "ContextManager[AnyTrig]"


def test_migratory_equals_the_committed_file():
    sys.path.insert(0, str(TOOLS.parent / "script"))
    import migratory

    committed = (TOOLS.parent / "in_game/common/generic_actions/tfe_migratory.txt").read_text(encoding="utf-8-sig")
    assert dump(parse(migratory.build().text())) == dump(parse(committed))


def test_unverified_names_are_loose():
    assert api.UNVERIFIED and all(n.startswith(("Fx.", "Trig.")) for n in api.UNVERIFIED)


GOOD = '''
from pdx.api import CountryFx, LocationFx

def ok(c: CountryFx, l: LocationFx):
    c.add_country_modifier(modifier="x", years=5)
    c.save_scope_as("a")      # any-scope effect, in a country
    l.save_scope_as("b")      # and in a location
    with c.every_neighbor_country() as n:
        n.add_country_modifier(modifier="y")
        with n.limit() as t:
            t.gold(100, op=">=")
    with c.go_capital() as loc:
        loc.save_scope_as("c")
'''
BAD = '''
from pdx.api import CountryFx

def bad(c: CountryFx):
    with c.go_capital() as loc:
        loc.add_country_modifier(modifier="x")   # BAD: a location takes no country modifier
    c.gold(">=", 1)                               # BAD: gold is a trigger
'''


def pyright(tmp_path, source, name):
    """errors pyright reports (with the repo's pyrightconfig.json) for `source` written to tmp_path, or, with source None,
    for the repo file `name`."""
    root = TOOLS.parent
    f = root / name if source is None else tmp_path / name
    if source is not None:
        f.write_text(source)
    try:
        r = subprocess.run([sys.executable, "-m", "pyright", "-p", str(root / "pyrightconfig.json"), "--outputjson", str(f)],
                           cwd=root, capture_output=True, text=True, timeout=300)
        return [d for d in json.loads(r.stdout)["generalDiagnostics"] if d["severity"] == "error"]
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as e:
        pytest.skip(f"pyright cannot run here ({e!r}); use `uv run --with pyright`")


def test_pyright_accepts_right_scopes_and_flags_wrong_ones(tmp_path):
    assert pyright(tmp_path, GOOD, "good.py") == []
    lines = {d["range"]["start"]["line"] + 1 for d in pyright(tmp_path, BAD, "bad.py")}
    bad = [i for i, l in enumerate(BAD.splitlines(), 1) if "# BAD" in l]
    assert lines == set(bad), (lines, bad)


WRONG_IN_LINK = '''
from pdx.api import AnyFx, CountryFx

def bad(e: AnyFx):
    with e.link("scope:actor", CountryFx) as c:
        with c.go_capital() as loc:
            c.add_country_modifier(modifier="x")      # fine: c is the country
            loc.add_country_modifier(modifier="y")    # BAD: loc is a location
    with e.hidden_effect() as h:
        with h.link("scope:actor", CountryFx) as c:
            c.add_country_modifier(modifier="x")
            c.declare_war_with_cb(target="c:EAR", type="t", bogus=1)   # BAD: no such parameter
'''


def test_pyright_passes_migratory_and_flags_wrong_scope_in_a_link(tmp_path):
    assert pyright(tmp_path, None, "script/migratory.py") == []
    lines = {d["range"]["start"]["line"] + 1 for d in pyright(tmp_path, WRONG_IN_LINK, "wrong.py")}
    assert lines == {i for i, l in enumerate(WRONG_IN_LINK.splitlines(), 1) if "# BAD" in l}, lines
