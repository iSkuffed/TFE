"""The definition-file ports (script/defs_*.py): each reproduces its hand-written file, lints clean, and type-checks."""
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))
import lint_script as ls  # noqa: E402

MODULES = sorted(p.stem for p in (ROOT / "script").glob("defs_*.py"))
OUT = {rel: text for m in MODULES for rel, text in importlib.import_module(m).outputs().items()}


def tree(entries):
    return [(e.key, e.op, tree(e.val) if isinstance(e.val, list) else e.val) for e in entries]


@pytest.mark.parametrize("rel", sorted(OUT))
def test_parses_equal_to_the_committed_file(rel):
    assert tree(ls.parse(OUT[rel])) == tree(ls.parse((ROOT / rel).read_text(encoding="utf-8-sig")))


@pytest.mark.parametrize("rel", sorted(OUT))
def test_generated_file_lints_clean(rel):
    if not (ls.DOCS / "effects.log").exists():
        pytest.skip("no script docs")
    lin = ls.Linter(ls.Knowledge([ls.b.GAME, ls.b.MOD]))
    folder, tree = Path(rel).parent.name, ls.parse(OUT[rel])
    if folder in ("scripted_effects", "scripted_triggers"):  # as ls.lint does: each entry's body is the effect/trigger
        for e in tree:
            lin.walk(rel, e.val, "effect" if folder == "scripted_effects" else "trigger")
    else:
        lin.walk(rel, tree, "other")
    assert lin.found == []


def test_pyright_clean_over_defs(tmp_path):
    (tmp_path / "pyrightconfig.json").write_text(json.dumps({"extraPaths": [str(ROOT / "tools")]}))
    files = [str(ROOT / "script" / f"{m}.py") for m in MODULES]
    try:
        r = subprocess.run([sys.executable, "-m", "pyright", "--outputjson", *files], cwd=tmp_path, capture_output=True, text=True, timeout=300)
        errors = [d for d in json.loads(r.stdout)["generalDiagnostics"] if d["severity"] == "error"]
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as e:
        pytest.skip(f"pyright cannot run here ({e!r}); use `uv run --with pyright`")
    assert errors == []
