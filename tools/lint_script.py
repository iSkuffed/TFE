"""Lint TFE's PDXScript against EU5's own docs (effects/triggers/modifiers/event_targets.log).

    python tools/lint_script.py            # the mod: exit 1 on any problem
    python tools/lint_script.py --vanilla  # vanilla's own files: a hit here is a linter false positive

The docs come from the `script_docs` console command (see CLAUDE.md). Without them the lint is skipped.
"""
import functools
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

# the docs sit beside the mod folder; EU5_DOCS for a checkout elsewhere (a jj workspace, say)
DOCS = Path(os.environ.get("EU5_DOCS") or b.MOD.parent.parent / "docs")
OUTCOMES = {"positive", "neutral", "negative"}
# keys whose block is a list of effects / of triggers, wherever they appear
EFFECT_BLOCKS = {"immediate", "after", "effect", "hidden_effect", "on_accept", "on_decline", "on_start", "on_end"}
TRIGGER_BLOCKS = {"trigger", "limit", "potential", "allow", "is_shown", "is_valid", "can_start", "can_end", "visible"}
BOOLEAN = {"AND", "OR", "NOT", "NAND", "NOR"}
DESCEND = BOOLEAN | {"if", "else_if", "else", "while"}
# keys that only structure or parameterise a block: legal next to effects/triggers, never looked up in the docs
STRUCTURE = DESCEND | {"modifier", "count", "percent", "order_by", "max", "min", "position", "check_range_bounds",
                       "alternative_limit", "weight", "chance", "switch", "fallback", "name", "desc", "title",
                       "custom_description", "text", "subject", "ai_chance", "ai_will_do", "exclusive", "highlight",
                       "reason", "tooltip", "list", "type", "variable", "add", "multiply", "divide", "factor", "value",
                       "target", "scope", "random_list", "subtract", "modulo", "alias", "texture"}


# --- parsing -----------------------------------------------------------------------------------------------------

class Entry:
    __slots__ = ("key", "op", "val", "line")

    def __init__(self, key, op, val, line):
        self.key, self.op, self.val, self.line = key, op, val, line


TOKEN = re.compile(r'''\s+|#[^\n]*|"(?:[^"\\]|\\.)*"|@\[[^\]]*\]|\?=|!=|<=|>=|[{}=<>]|[^\s{}=<>"#]+''')
OPS = ("=", "?=", "!=", "<", ">", "<=", ">=")


def parse(text):
    """text -> [Entry]. A block value is a list of Entry; `{ 1 2 }` items are Entry(None...) or bare keys."""
    toks, line = [], 1
    for m in TOKEN.finditer(text):
        t = m.group()
        if not t.isspace() and t[0] != "#":
            toks.append((t, line))
        line += t.count("\n")
    toks.append(("}", line))  # closes the implicit file-level block
    pos = 0

    def block():
        nonlocal pos
        out = []
        while pos < len(toks):
            t, ln = toks[pos]
            pos += 1
            if t == "}":
                return out
            if t == "{":
                out.append(Entry(None, None, block(), ln))
            elif pos < len(toks) and toks[pos][0] in OPS:
                op = toks[pos][0]
                pos += 1
                if pos >= len(toks) - 1:
                    raise ValueError(f"line {ln}: `{t} {op}` has no value")
                v = toks[pos][0]
                if v == "{":
                    pos += 1
                    out.append(Entry(t, op, block(), ln))
                elif toks[pos + 1][0] == "{":  # `rgb { 1 2 3 }`: a tagged block
                    pos += 2
                    out.append(Entry(t, op, block(), ln))
                else:
                    pos += 1
                    out.append(Entry(t, op, v, ln))
            else:
                out.append(Entry(t, None, None, ln))
        raise ValueError("a '{' is never closed")

    out = block()
    if pos < len(toks):
        raise ValueError(f"line {toks[pos - 1][1]}: a '}}' has no '{{'")
    return out


@functools.lru_cache(maxsize=None)
def tree_of(path):
    return parse(path.read_text(encoding="utf-8-sig"))


# --- what EU5 knows ----------------------------------------------------------------------------------------------

def doc_names(log, marker):
    return set(re.findall(rf"^{marker} (\w+)", (DOCS / log).read_text(encoding="utf-8-sig"), re.M))


def script_files(base):
    for area in ("in_game", "main_menu"):
        for p in sorted((base / area).rglob("*.txt")):
            parts = p.relative_to(base).parts
            if parts[:2] != ("in_game", "map_data") and "gfx" not in parts:
                yield p


def definitions(roots):
    """names the files define: scripted effects/triggers (a file of them, or inline `scripted_effect x = {`), static
    modifiers, script values."""
    out = {"effects": set(), "triggers": set(), "statics": set(), "values": set()}
    where = {"scripted_effects": "effects", "scripted_triggers": "triggers", "static_modifiers": "statics",
             "script_values": "values"}
    for root in roots:
        for p in script_files(root):
            try:
                tree = tree_of(p)
            except ValueError:
                continue
            if p.parent.name in where:
                out[where[p.parent.name]] |= {e.key for e in tree if e.key}
            for prev, e in zip(tree, tree[1:]):
                if prev.key in ("scripted_effect", "scripted_trigger") and prev.op is None:
                    out[prev.key[9:] + "s"].add(e.key)
    return out


class Knowledge:
    def __init__(self, roots):
        d = definitions(roots)
        self.effects = doc_names("effects.log", "##") | d["effects"]
        self.triggers = doc_names("triggers.log", "##") | d["triggers"]
        self.statics, self.values = d["statics"], d["values"]
        self.targets = doc_names("event_targets.log", "###")
        self.modifier_keys = set(re.findall(r"^Tag: (\w+),", (DOCS / "modifiers.log").read_text(encoding="utf-8-sig"), re.M))

    def is_link(self, k):
        """a scope change or a value, not an effect or trigger: c:ROM, scope:x, a.b, owner, ROOT, 10, -5, @const."""
        return (k is None or ":" in k or "." in k or k in self.targets or k.lower() in ("root", "this", "prev", "from")
                or "$" in k or k in ("ADM", "DIP", "MIL") or re.match(r"""[-\d@"]""", k) or k in self.values)


# --- checks ------------------------------------------------------------------------------------------------------

class Linter:
    def __init__(self, know):
        self.know, self.found = know, []

    def say(self, path, e, msg):
        self.found.append(f"{path}:{e.line}: {msg}")

    def walk(self, path, entries, ctx):
        """ctx is 'effect', 'trigger' or 'other' (look for the next effect/trigger block, check nothing)."""
        k = self.know
        for e in entries:
            key = e.key
            if key in EFFECT_BLOCKS and isinstance(e.val, list):
                self.walk(path, e.val, "effect")
                continue
            if key in TRIGGER_BLOCKS and isinstance(e.val, list):
                self.walk(path, e.val, "trigger")
                continue
            self.check_keyword(path, e)
            if ctx == "other":
                if isinstance(e.val, list):
                    self.walk(path, e.val, "other")
                continue
            iterator = key and re.match(r"(every|random|ordered)_" if ctx == "effect" else r"any_", key)
            if key in STRUCTURE:
                if isinstance(e.val, list) and key in DESCEND:
                    self.walk(path, e.val, ctx)
            elif k.is_link(key) or iterator:
                if isinstance(e.val, list):
                    self.walk(path, e.val, ctx)
            elif key in (k.effects if ctx == "effect" else k.triggers):
                if isinstance(e.val, list) and key in ("random_list", "switch"):
                    self.walk(path, e.val, ctx)
            else:
                self.say(path, e, f"unknown {ctx} `{key}`")

    def check_keyword(self, path, e):
        """the traps that are wrong wherever they appear."""
        key = e.key
        if key == "outcome" and e.val not in OUTCOMES:
            self.say(path, e, f"outcome = {e.val}: must be positive, neutral or negative")
        if key == "exists" and isinstance(e.val, str) and e.val.startswith(("c:", "country:")):
            self.say(path, e, f"exists = {e.val}: use country_exists, exists is true for landless leftovers")
        if key and re.fullmatch(r"add_\w+_modifier", key) and isinstance(e.val, list):
            names = {c.key for c in e.val}
            if "modifier" not in names and "name" in names:
                self.say(path, e, f"{key} takes `modifier =`, `name =` silently does nothing")
            for c in e.val:
                if (c.key == "modifier" and isinstance(c.val, str) and c.val not in self.know.statics
                        and not re.search(r"[:$]", c.val)):
                    self.say(path, c, f"{key} names a modifier that is not defined: {c.val}")


def lint(vanilla=False):
    if not (DOCS / "effects.log").exists():
        print(f"skipped: no {DOCS}/effects.log (run `script_docs` in the game console)")
        return []
    base = b.GAME if vanilla else b.MOD
    lin = Linter(Knowledge([b.GAME] if vanilla else [b.GAME, b.MOD]))
    for p in script_files(base):
        rel = p.relative_to(base)
        # vanilla's setup/start files carry no BOM, so ours (generated to match) needn't either
        if not vanilla and rel.parts[:3] != ("main_menu", "setup", "start") and not p.read_bytes().startswith(b"\xef\xbb\xbf"):
            lin.found.append(f"{rel}:1: no UTF-8 BOM")
        try:
            tree = tree_of(p)
        except ValueError as err:
            lin.found.append(f"{rel}: {err}")
            continue
        folder = p.parent.name
        if folder in ("scripted_effects", "scripted_triggers"):
            for e in tree:
                if isinstance(e.val, list):
                    lin.walk(rel, e.val, "effect" if folder == "scripted_effects" else "trigger")
        else:
            lin.walk(rel, tree, "other")
    return lin.found


if __name__ == "__main__":
    problems = lint("--vanilla" in sys.argv)
    print("\n".join(problems) or "clean")
    sys.exit(1 if problems else 0)
