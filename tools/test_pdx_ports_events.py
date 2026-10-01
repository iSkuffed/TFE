"""The ported events files: script/{decline_rome,foederati,hunnic_storm,opening}_events.py reproduce the committed .txt files.

Their localisation ymls also hold keys for generic actions, situations and GUI that these scripts cannot know, so the
ymls stay hand-written: the test checks every key the script adds is in the yml with the same text.
"""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))
import decline_rome_events, foederati_events, hunnic_storm_events, opening_events  # noqa: E402
import lint_script as ls  # noqa: E402
from test_pdx_events import pyright, tree, yml  # noqa: E402

LOC = "main_menu/localization/english/%s_l_english.yml"
PORTS = {n: m for n, m in (("tfe_decline_rome", decline_rome_events), ("tfe_foederati", foederati_events),
                           ("tfe_hunnic_storm", hunnic_storm_events), ("tfe_opening", opening_events))}
param = pytest.mark.parametrize("name", PORTS)


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8-sig")


@param
def test_script_parses_equal_to_the_committed_file(name):
    rel = f"in_game/events/{name}.txt"
    assert tree(ls.parse(PORTS[name].outputs()[rel])) == tree(ls.parse(read(rel)))


@param
def test_event_localisation_is_in_the_committed_yml(name):
    want = yml(read(LOC % name))
    got = PORTS[name].build().loc.keys
    assert got and all(k.startswith(name + ".") for k in got)
    assert {k: v for k, v in got.items() if want.get(k) != v.replace("\n", "\\n")} == {}


@param
def test_generated_events_lint_clean(name):
    if not (ls.DOCS / "effects.log").exists():
        pytest.skip("no script docs")
    rel = f"in_game/events/{name}.txt"
    lin = ls.Linter(ls.Knowledge([ls.b.GAME, ls.b.MOD]))
    lin.walk(rel, ls.parse(PORTS[name].outputs()[rel]), "other")
    assert lin.found == []


@pytest.mark.parametrize("script", ["decline_rome", "foederati", "hunnic_storm", "opening"])
def test_pyright_clean(tmp_path, script):
    assert pyright(tmp_path, ROOT / f"script/{script}_events.py") == []
