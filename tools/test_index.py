"""docs/INDEX.md is up to date: rerun `python tools/gen_index.py` after adding or renaming a script or loc file."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_index


def test_index_is_up_to_date():
    assert gen_index.OUT.read_text(encoding="utf-8") == gen_index.build(), "rerun python tools/gen_index.py"


def test_top_level_keys_ignore_nested_blocks_comments_and_strings():
    text = 'ns = x\na.1 = {\n\tb = { c = "}{" }  # d = {\n}\n# e = {\nf = {\n}\n'
    assert gen_index.top_level_keys(text) == [(2, "a.1"), (6, "f")]
