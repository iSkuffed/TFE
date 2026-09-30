"""The files written by script/*.py are up to date: rerun `python script/run.py` after editing a script."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
import run


def test_generated_script_files_are_up_to_date():
    stale = [rel for rel, text in run.all_outputs().items()
             if (ROOT / rel).read_text(encoding="utf-8-sig") != text]
    assert not stale, f"rerun python script/run.py: {stale}"


def test_generated_files_start_with_a_bom_except_start_files():
    for rel in run.all_outputs():
        assert (ROOT / rel).read_bytes().startswith(b"\xef\xbb\xbf") == (run.encoding(rel) == "utf-8-sig"), rel
