"""The output tree and the formatter of the typed script layer. See CONTRACT.md.

Python builds Nodes through Scope methods; render() writes PDXScript in the mod's hand-written layout (tabs, LF).
"""
from contextlib import contextmanager

CMP_OPS = ("<", "<=", "=", "!=", ">", ">=", "?=")


class Node:
    """key op val. val is a str (scalar), a list of Node (block) or None (a bare key, or an empty head)."""
    __slots__ = ("key", "op", "val", "lead", "tail")

    def __init__(self, key, op=None, val=None, lead=None, tail=None):
        self.key, self.op, self.val = key, op, val
        self.lead, self.tail = lead or [], tail

    def __eq__(self, o):
        return isinstance(o, Node) and all(getattr(self, s) == getattr(o, s) for s in self.__slots__)

    def __repr__(self):
        return f"Node({self.key!r}, {self.op!r}, {self.val!r})"


class Q(str):
    """a value written "quoted"."""


def fmt(v):
    if isinstance(v, Q):
        return f'"{v}"'
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return str(int(v)) if v == int(v) else repr(v)
    return str(v)


def from_entries(entries):
    """lint_script.parse() output -> [Node]."""
    return [Node(e.key, e.op, from_entries(e.val) if isinstance(e.val, list) else e.val) for e in entries]


# --- the formatter -----------------------------------------------------------------------------------------------
# What the census (tools/pdx/census.py) found in the hand-written files, as plain rules:
# - a block is one line (`k = { a = b c = d }`) or one statement per line. An empty block is `{ }`.
# - a top-level definition (indent 0) is always multi-line; so is any block holding a comment.
# - the data keys in ONE_LINE_DATA (tags, opinions, color...) are one line however long.
# - otherwise a block can be one line only if it is a statement (an effect or trigger call, a scope link, an iterator,
#   or one of the small structure keys in FLAT_OK); property blocks (modifier, cooldown, option, cost, potential...) and
#   sections are always multi-line. A statement is one line when its text is at most WIDTH columns (indent not counted),
#   and it is either a parameter block (`change_variable = { name = x add = -10 }`: up to MAX_LEAVES values, one level
#   of nesting), or a container (scope link, iterator, if, NOT, hidden_effect...) around one statement that is itself
#   one line. `limit` may also hold a few conditions side by side. OR/AND with several statements are multi-line.
WIDTH = 120
CHAIN_WIDTH = 90  # a container around another container
MAX_LEAVES = 4
BOOLEAN = {"OR", "AND", "NAND", "NOR"}
FLAT_OK = {"random", "delay", "overlord", "unit_location", "top_overlord", "ruler", "heir", "capital", "controller", "limit", "NOT", "ai_chance", "hidden_effect", "trigger", "if", "else_if", "owner", "OR", "AND", "NAND", "NOR"}
VERBS = ("set_", "change_", "add_", "clear_", "remove_", "create_", "trigger_", "declare_", "save_", "activate_",
         "every_", "any_", "random_", "ordered_", "split_", "has_", "is_", "can_", "join_", "international_organization_")
ONE_LINE_DATA = {"text", "opinions", "color", "color2", "member_color", "game_data", "on_actions", "tags", "culture_groups"}


def find(nodes, key=None, val=None, /, *, inside=()):
    """every Node under nodes, depth first, whose key (and scalar value) match; a test asks the model instead of the text.
    `inside` is a block key, or keys in order from outermost: only nodes below blocks with those keys (not necessarily
    adjacent). find(doc.nodes, "has_advance", "taxation_advance", inside=("tfe_x.1", "trigger"))."""
    inside = (inside,) if isinstance(inside, str) else tuple(inside)
    want = None if val is None else fmt(val)

    def walk(ns, path):
        for n in ns:
            ancestors = iter(path)
            if ((key is None or n.key == key) and (want is None or n.val == want)
                    and all(k in ancestors for k in inside)):  # `in` consumes the iterator: an ordered subsequence
                yield n
            if isinstance(n.val, list):
                yield from walk(n.val, path + [n.key])
    return list(walk(nodes, []))


def _has_comment(n):
    """a comment on any node inside n (n's own tail is fine after a one-line block)."""
    return isinstance(n.val, list) and any(c.lead or c.tail or _has_comment(c) for c in n.val)


def _depth(n):
    return 0 if not isinstance(n.val, list) else 1 + max((_depth(c) for c in n.val), default=0)


def _leaves(n):
    return 1 if not isinstance(n.val, list) else sum(_leaves(c) for c in n.val)


def _head(n):
    if n.key is None:
        return ""
    return n.key if n.op is None else f"{n.key} {n.op} "


def _flat(n):
    if not isinstance(n.val, list):
        return _head(n) + ("" if n.val is None else fmt(n.val))
    return _head(n) + "{ " + " ".join(_flat(c) for c in n.val) + " }" if n.val else _head(n) + "{ }"


def _section(k):
    return k in ("actions", "possible_production_methods") or k.startswith(("create_visible", "create_enabled", "can_declare", "can_bestow", "can_start", "can_end"))


def _statement(n):
    k = n.key or ""
    return k in FLAT_OK or ":" in k or n.op == "?=" or (k.startswith(VERBS) and not _section(k))


def _container(k):
    return ":" in k or k in ("if", "else_if", "NOT", "limit", "hidden_effect", "owner", "trigger") or k.startswith(
        ("every_", "any_", "random_", "ordered_"))


def _one_line(n, ind):
    """can the block n, written at indent ind, be one line?"""
    kids, k = n.val, n.key or ""
    if not kids:
        return True
    if _has_comment(n) or ind == 0:
        return False
    if k in ONE_LINE_DATA or (all(c.op is None and c.val is None for c in kids) and not _section(k)):
        return True
    if len(_flat(n)) > WIDTH or not _statement(n):
        return False
    blocks = [c for c in kids if isinstance(c.val, list)]
    if k in BOOLEAN:
        return len(kids) == 1 and not blocks
    if k == "ai_chance":
        return not blocks
    if k == "limit" and len(kids) <= 3 and _depth(n) <= 3:
        return not any(c.key in BOOLEAN for c in kids)
    if _container(k):
        return len(kids) == 1 and (not blocks or (len(_flat(n)) <= CHAIN_WIDTH and _one_line(kids[0], ind + 1)))
    return len(blocks) <= 1 and _depth(n) <= 2 and _leaves(n) <= MAX_LEAVES


def _lines(nodes, ind):
    out, pad = [], "\t" * ind
    for n in nodes:
        out += [f"{pad}# {t}".rstrip() for t in n.lead]
        tail = f"\t# {n.tail}" if n.tail else ""
        if not isinstance(n.val, list) or _one_line(n, ind):
            out.append(pad + _flat(n) + tail)
        else:
            out.append(pad + _head(n) + "{")
            out += _lines(n.val, ind + 1)
            out.append(pad + "}" + tail)
    return out


def render(nodes):
    """[Node] -> text: tabs, LF, no BOM, trailing newline. A blank line separates top-level nodes when either is
    multi-line (blank lines inside a block are not reproduced)."""
    out, prev = "", None
    for n in nodes:
        chunk = "\n".join(_lines([n], 0))
        out += ("\n\n" if "\n" in chunk or "\n" in prev else "\n") + chunk if prev is not None else chunk
        prev = chunk
    return out + "\n"


# --- building ----------------------------------------------------------------------------------------------------

class Scope:
    def __init__(self, sink):
        self._sink = sink
        self._lead = []  # note() text waiting for the next node

    def _add(self, node):
        if self._lead:
            node.lead, self._lead = self._lead, []
        self._sink.append(node)
        return node

    @staticmethod
    def _kw(kw):
        return _kwval(kw)

    def _call(self, name, /, *args, **kw):
        name = name.rstrip("_")
        if args and kw:
            raise TypeError(f"{name}: positional and keyword arguments cannot be mixed")
        if len(args) > 1:
            raise TypeError(f"{name}: at most one positional argument")
        if args:
            self._add(Node(name, "=", fmt(args[0])))
        elif kw:
            self._add(Node(name, "=", self._kw(kw)))
        else:
            self._add(Node(name))

    def _cmp(self, name, op, value, /):
        if op not in CMP_OPS:
            raise ValueError(f"{name}: unknown operator {op!r}")
        self._add(Node(name.rstrip("_"), op, fmt(value)))

    @contextmanager
    def _open(self, name, cls, /, *, op="=", **kw):
        node = self._add(Node(name.rstrip("_"), op, self._kw(kw)))
        yield cls(node.val)

    def _run(self, name, cls, body=None, /, *, op="=", **kw):
        """the block as a context manager, or, given body, written at once: body(inner scope)."""
        cm = self._open(name, cls, op=op, **kw)
        if body is None:
            return cm
        with cm as inner:
            body(inner)

    def link(self, text, cls, body=None, *, op="="):
        return self._run(text, cls, body, op=op)

    def saved(self, name, cls):
        """`scope:name` as a typed scope: `with c.saved("x", CountryFx) as s:` writes `scope:x = {`; str() is the ref."""
        return _Saved(self, f"scope:{name}", cls)

    def note(self, text):
        self._lead += str(text).split("\n")

    def tail(self, text):
        if not self._sink:
            raise ValueError("tail() with nothing written yet")
        self._sink[-1].tail = str(text)

    def raw(self, text):
        from lint_script import parse  # lazy: lint_script imports the map tools
        for n in from_entries(parse(text)):
            self._add(n)


class Cmp:
    """a keyword value that carries its operator: `religion_percentage(religion=r, value=Cmp(">=", 0.25))` writes `value >= 0.25`."""

    def __init__(self, op, value):
        if op not in CMP_OPS:
            raise ValueError(f"unknown operator {op!r}")
        self.op, self.value = op, value


def _kwval(v):
    if isinstance(v, dict):
        return [Node(k.rstrip("_"), x.op if isinstance(x, Cmp) else "=", _kwval(x.value if isinstance(x, Cmp) else x)) for k, x in v.items()]
    return fmt(v)


class _Saved:
    def __init__(self, parent, ref, cls):
        self._parent, self._ref, self._cls = parent, ref, cls

    def __str__(self):
        return self._ref

    def __enter__(self):
        self._cm = self._parent._open(self._ref, self._cls)
        return self._cm.__enter__()

    def __exit__(self, *exc):
        return self._cm.__exit__(*exc)
