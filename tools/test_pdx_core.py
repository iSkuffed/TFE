"""tools/pdx/core.py: building nodes, fmt, and the formatter (incl. how closely it matches the mod's own files)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent / "pdx"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import Node, Q, Scope, fmt, from_entries, render  # noqa: E402


def built(fn):
    """what fn writes, as the body of a definition (top-level blocks are always multi-line)."""
    sink = []
    fn(Scope(sink))
    body = render([Node("t", "=", sink)]).split("\n")[1:-2]
    return "".join(ln[1:] + "\n" for ln in body)


def test_fmt():
    assert (fmt(True), fmt(False)) == ("yes", "no")
    assert (fmt(5), fmt(-10), fmt(0.5), fmt(2.0)) == ("5", "-10", "0.5", "2")
    assert fmt(Q("a b")) == '"a b"'
    assert fmt("scope:x") == "scope:x"


def test_call_forms():
    def f(s):
        s._call("always")  # bare
        s._call("add_gold", 5)  # scalar
        s._call("set_variable", name="x", value=True)  # block
        s._call("change_variable", name="x", add={"value": 2, "multiply": 0.5})  # nested dict
        s._call("if_", limit_=1)  # trailing underscores: name and keyword
    assert built(f) == ("always\nadd_gold = 5\nset_variable = { name = x value = yes }\n"
                        "change_variable = { name = x add = { value = 2 multiply = 0.5 } }\nif = { limit = 1 }\n")


def test_call_positional_and_keyword_is_an_error():
    with pytest.raises(TypeError):
        Scope([])._call("x", 1, a=2)


def test_cmp():
    assert built(lambda s: s._cmp("gold", ">=", 100)) == "gold >= 100\n"
    assert built(lambda s: s._cmp("owner", "?=", "c:EAR")) == "owner ?= c:EAR\n"
    with pytest.raises(ValueError):
        Scope([])._cmp("gold", "=>", 1)


def test_open_nests_and_keeps_order():
    def f(s):
        with s._open("if", Scope, chance=5) as i:
            with i._open("limit", Scope) as lim:
                lim._cmp("var:x", "<", 0)
            i._call("add_gold", 1)
    assert built(f) == "if = {\n\tchance = 5\n\tlimit = { var:x < 0 }\n\tadd_gold = 1\n}\n"


def test_link_and_saved():
    def f(s):
        with s.link("c:EAR", Scope, op="?=") as c:
            c._call("add_gold", 1)
        with s.saved("actor", Scope) as a:
            a._call("add_gold", 2)
        assert str(s.saved("actor", Scope)) == "scope:actor"
    assert built(f) == "c:EAR ?= { add_gold = 1 }\nscope:actor = { add_gold = 2 }\n"


def test_raw_parses_and_appends():
    def f(s):
        s.raw("a = b\nset_variable = { name = e }")
        s._call("z")
    assert built(f) == "a = b\nset_variable = { name = e }\nz\n"


def test_note_and_tail_placement():
    def f(s):
        s.note("why")
        s._call("a", 1)
        s.tail("because")
        with s._open("blk", Scope) as b:
            b.note("inner")
            b._call("x", 1)
    assert built(f) == "# why\na = 1\t# because\nblk = {\n\t# inner\n\tx = 1\n}\n"


def test_tail_on_block_and_comment_forces_multiline():
    n = Node("limit", "=", [Node("a", "=", "1", tail="c")])
    assert render([Node("x", "=", [Node("limit", "=", [Node("a", "=", "1")], tail="t")])]) == "x = {\n\tlimit = { a = 1 }\t# t\n}\n"
    assert render([Node("x", "=", [n])]) == "x = {\n\tlimit = {\n\t\ta = 1\t# c\n\t}\n}\n"


def test_layout_examples_from_the_mod():
    one = "x = {\n\tlimit = { var:x < 0 }\n\tai_chance = { base = 2 }\n\topinions = { a = b c = d }\n\ttags = { p q r }\n"
    text = one + "\thidden_effect = { change_variable = { name = x add = -10 } }\n}\n"
    assert render(from_entries(_parse(text))) == text
    deep = "x = {\n\tlimit = {\n\t\tOR = {\n\t\t\ta = 1\n\t\t\tb = 2\n\t\t}\n\t\tc = 3\n\t}\n}\n"
    assert render(from_entries(_parse(deep))) == deep


def _parse(text):
    import lint_script
    return lint_script.parse(text)


def test_census_identical_rate_does_not_regress():
    """Measured 2026-09-30: 53 of 79 hand-written files byte-identical (67%). The guard is 60%: a formatter change that
    drops below it is worse at matching the mod, so look at `python tools/pdx/census.py` before lowering it."""
    import census
    same, diff, skipped, _, _ = census.run()
    assert not skipped
    assert len(same) / (len(same) + len(diff)) >= 0.60
