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
    (tmp_path / "pyrightconfig.json").write_text(json.dumps({"extraPaths": [str(ROOT / "tools")]}))
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
