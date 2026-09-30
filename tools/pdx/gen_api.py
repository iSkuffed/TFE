"""Write tools/pdx/api.py: scope-typed Python bindings for EU5's effects and triggers.

    python tools/pdx/gen_api.py

Inputs: the docs logs (effects/triggers/event_targets.log, see lint_script.DOCS), vanilla script (call shapes, infer.py)
and overrides.py. The output is committed; rerun this after an EU5 patch and never edit api.py by hand.
"""
import keyword
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import borders as b
import infer
import overrides as ov
from lint_script import DOCS, definitions, doc_names, script_files, tree_of

OUT = HERE / "api.py"
RESERVED = {"note", "tail", "raw", "link", "saved", "limit"}  # Scope's own methods, and `limit`
MODE_NAME = {"E": "Fx", "T": "Trig"}
SCOPE_RE = re.compile(r"\w+")


def doc_blocks(log):
    """name -> {desc, scopes, targets, traits}"""
    out = {}
    for blk in re.split(r"^## ", (DOCS / log).read_text(encoding="utf-8-sig"), flags=re.M)[1:]:
        name = blk.split("\n", 1)[0].strip()
        sc = re.search(r"\*\*Supported Scopes\*\*: (.*)", blk)
        tg = re.search(r"\*\*Supported Targets\*\*: (.*)", blk)
        split = lambda m: [s.strip() for s in m.group(1).split(",") if SCOPE_RE.fullmatch(s.strip())] if m else []
        out[name] = {"desc": blk, "scopes": split(sc), "targets": split(tg), "traits": "\nTraits:" in blk}
    return out


def doc_targets():
    """event_targets.log -> [(name, inputs, outputs, needs_data)]"""
    out = []
    for blk in re.split(r"^### ", (DOCS / "event_targets.log").read_text(encoding="utf-8-sig"), flags=re.M)[1:]:
        name = blk.split("\n", 1)[0].strip()
        scopes = lambda k: [s.strip() for m in re.findall(rf"^{k}: (.*)", blk, re.M) for s in m.split(",")]
        if re.fullmatch(r"\w+", name) and scopes("Output Scopes"):
            out.append((name, scopes("Input Scopes"), scopes("Output Scopes"), "Requires Data: yes" in blk))
    return out


def script_params(roots):
    """{scripted name: its `$param$`s in order of first use}, read from the scripted effect's or trigger's own body."""
    out = {}
    for root in roots:
        for p in script_files(root):
            if p.parent.name not in ("scripted_effects", "scripted_triggers"):
                continue
            try:
                tree = tree_of(p)
            except ValueError:
                continue
            for e in tree:
                if e.key and isinstance(e.val, list):
                    seen = []
                    stack = [e.val]
                    while stack:
                        for x in stack.pop(0):
                            for s in (x.key, x.val):
                                if isinstance(s, str):
                                    seen += re.findall(r"\$(\w+)(?:\|[^$]*)?\$", s)
                            if isinstance(x.val, list):
                                stack.append(x.val)
                    out[e.key] = list(dict.fromkeys(seen))
    return out


def scripted_docs(docs):
    """the scripted effects/triggers of vanilla, its DLCs and the mod, as doc-like entries (scope unknowable: any)."""
    roots = [b.GAME, *sorted((b.GAME / "dlc").glob("*")), b.MOD]
    found, params = definitions(roots), script_params(roots)
    return {m: {n: {"desc": "", "scopes": [], "targets": [], "traits": False, "scripted": True, "params": params.get(n, [])}
                for n in sorted(found[k]) if n.isidentifier() and n not in docs[m]}
            for m, k in (("E", "effects"), ("T", "triggers"))}


def cls(scope, mode):
    return "".join(p.title() for p in scope.split("_")) + MODE_NAME[mode]


def pyname(n):
    return n + "_" if keyword.iskeyword(n) or n in RESERVED else n


def fix_modifier(name, sp):
    """the docs say `name =`, the game needs `modifier =`"""
    if re.fullmatch(r"add_\w+_modifier", name):
        for k in ("req", "opt"):
            sp[k] = ["modifier" if x == "name" else x for x in sp[k]]
        sp["opt"] = [x for i, x in enumerate(sp["opt"]) if x not in sp["req"] and x not in sp["opt"][:i]]
    return sp


# --- building the specs ------------------------------------------------------------------------------------------

def build(mode, docs, scan, names):
    """-> {name: (kind, spec)}; kind: override, iterator, vanilla, docs, fallback, splice"""
    claimed = set(ov.COMMON_NAMES) | set(ov.FX_NAMES if mode == "E" else ov.TRIG_NAMES)
    over = ov.SPEC_FX if mode == "E" else ov.SPEC_TRIG
    missing = [n for n in list(over) + sorted(claimed) if n not in docs]
    assert not missing, f"overrides name things the docs lack: {missing}"
    prefixes = ("every", "random", "ordered") if mode == "E" else ("any",)
    out = {}
    for name, d in docs.items():
        m = infer.ITER.match(name)
        if d.get("scripted"):  # `tfe_x = yes`, or a parameter block whose keys the call sites show
            sp = infer.spec_vanilla(name, scan[mode][name], names) if name in scan[mode] else None
            sp = {**(sp or {"shapes": {"scalar"}, "req": [], "opt": [], "kinds": {"bool"}}), "scripted": True}
            fresh = [k for k in d["params"] if k not in sp["req"] + sp["opt"]]  # parameters no call site has used yet
            if fresh or (d["params"] and "block" not in sp["shapes"]):
                sp = {**sp, "shapes": sp["shapes"] | {"block"}, "opt": sp["opt"] + fresh,
                      "order": sp.get("order", []) + fresh}
            out[name] = ("scripted", {**sp, "shapes": sp["shapes"] - {"bare"} or {"scalar"}})
        elif name in claimed:
            out[name] = ("splice", None)
        elif name in over:
            out[name] = ("override", over[name])
        elif m and m.group(1) in prefixes and (len(d["targets"]) == 1 or "_in_" in name):
            keys = ov.FAMILY[m.group(1)] + (ov.ITER_EXTRA if not d["targets"] else [])
            out[name] = ("iterator", {"shapes": {"iter"}, "req": [], "opt": keys, "kinds": set()})
        else:
            sp = infer.spec_vanilla(name, scan[mode][name], names) if name in scan[mode] else None
            kind = "vanilla"
            if sp is None:
                sp, kind = infer.hint(name, d["desc"].split("\n", 1)[1]), "docs"
            if d["traits"]:  # a comparison trigger: `gold >= 100`; vanilla's block form, if any, stays
                sp, kind = sp or {"shapes": set(), "req": [], "opt": [], "kinds": set()}, kind if sp else "traits"
                sp["shapes"] = (sp["shapes"] - {"scalar", "bare"}) | {"cmp"}
            if sp is None:
                out[name] = ("fallback", None)
            else:
                out[name] = (kind, fix_modifier(name, sp))
    return out


# --- rendering ---------------------------------------------------------------------------------------------------

def params(sp):
    keys = sp["req"] + sp["opt"]
    if sp.get("order"):  # keyword-only parameters may come in any order; the call writes them in vanilla's
        keys = sorted(keys, key=lambda k: sp["order"].index(k) if k in sp["order"] else len(sp["order"]))
    ann = lambda k: sp.get("types", {}).get(k, "Any")
    parts = [f"{pyname(k)}: {ann(k)}" + ("" if k in sp["req"] else (" | None" if ann(k) != "Any" else "") + " = None")
             for k in keys]
    return ", ".join(parts), ", ".join(f"{pyname(k)}={pyname(k)}" for k in keys)


def method(name, sp, mode):
    """a spec -> one method's source (indented four spaces)"""
    py, sh = pyname(name), sp["shapes"]
    if sp.get("scripted"):
        if "block" not in sh:
            return f'    def {py}(self, _v: bool | str | float = True, /) -> None: self._call("{name}", _v)'
        sig, call = params({**sp, "req": [], "opt": sp["req"] + sp["opt"]})
        return (f'    def {py}(self, _v: bool | str | float | None = None, /, *, {sig}) -> None:\n'
                f'        _scripted(self, "{name}", _v, dict({call}))')
    if sh != {"block"}:  # one signature serves several shapes, so no key can be required
        sp = {**sp, "req": [], "opt": sp["req"] + sp["opt"]}
    val = "bool | str" if sp["kinds"] == {"bool"} else "Any"
    sig, call = params(sp)
    kw = f", **_kw({call})" if call else ""
    if sh == {"bare"}:
        return f'    def {py}(self) -> None: self._call("{name}")'
    if sh == {"scalar"}:
        return f'    def {py}(self, _v: {val}, /) -> None: self._call("{name}", _v)'
    if sh == {"cmp"}:
        return f'    def {py}(self, _v: Any, /, op: Op = "=") -> None: self._cmp("{name}", op, _v)'
    if sh == {"block"}:
        return f'    def {py}(self, *, {sig}) -> None: self._call("{name}"{kw})'
    if "cmp" in sh:
        return (f'    def {py}(self, _v: Any = None, /, *, op: Op = "=", {sig}) -> None:\n'
                f"        if _v is None:\n            self._call(\"{name}\"{kw})\n        else:\n"
                f'            self._cmp("{name}", op, _v)')
    star = f", *, {sig}" if sig else ""
    return f'    def {py}(self, _v: {val} = None, /{star}) -> None: self._call("{name}", *_pos(_v){kw})'


def iterator(name, sp, target):
    sig, call = params(sp)
    star = f"*, {sig}" if sig else ""
    tcls = target if target != "Any" else "AnyFx"
    if target == "Any" and re.search(r"_in_(global_|local_)?list$", name):  # the list's element type is the caller's to say
        return (f"    def {pyname(name)}(self, of: type[_S], /{', ' + star if star else ''}) -> ContextManager[_S]:\n"
                f'        return self._open("{name}", of{f", **_kw({call})" if call else ""})')
    return (f"    def {pyname(name)}(self{', ' + star if star else ''}) -> ContextManager[{target}]:\n"
            f'        return self._open("{name}", {tcls}{f", **_kw({call})" if call else ""})')


def links(mode, targets, known):
    """go_<name> scope links -> {scope or "none": [(method name, source)]}"""
    out = {}
    any_cls = "AnyFx" if mode == "E" else "AnyTrig"
    plain = {n for n, _, _, data in targets if not data}
    for name, ins, outs, data in targets:
        outs = [s for s in outs if s in known]
        if not outs:
            continue
        ret, c = (cls(outs[0], mode),) * 2 if len(outs) == 1 else ("Any", any_cls)
        arg, text = (", data: Any, /, *, op: Op = \"=\"", f'f"{name}:{{data}}"') if data else (", *, op: Op = \"=\"", f'"{name}"')
        name = f"{name}_data" if data and name in plain else name  # the docs give `location` both ways
        src = f"    def go_{name}(self{arg}) -> ContextManager[{ret}]:\n        return self.link({text}, {c}, op=op)"
        for s in [i for i in ins if i in known] or ["none"]:
            out.setdefault(s, []).append((f"go_{name}", src))
    return out


def generate(docs=None, scan=None):
    t0 = time.time()
    docs = docs or {"E": doc_blocks("effects.log"), "T": doc_blocks("triggers.log")}
    scripted = scripted_docs(docs)
    docs = {m: {**scripted[m], **docs[m]} for m in docs}
    names = {m: set(docs[m]) for m in docs}
    scan = scan or infer.scan(b.GAME, names, b.MOD)
    targets = doc_targets()
    scopes = {s for m in docs for d in docs[m].values() for s in d["scopes"] + d["targets"]}
    scopes |= {s for _, ins, outs, _ in targets for s in ins + outs}
    known = sorted(scopes - {"none", "all", "value"})
    known_set = set(known)
    built = {m: build(m, docs[m], scan, names[m]) for m in "ET"}
    body = {m: {s: [] for s in ["none"] + known} for m in "ET"}  # scope -> [(method name, source)]
    unverified, counts = [], {m: {"total": len(docs[m])} for m in "ET"}
    for m in "ET":
        for name, (kind, sp) in sorted(built[m].items()):
            counts[m][kind] = counts[m].get(kind, 0) + 1
            d = docs[m][name]
            if kind == "splice":
                continue
            if kind == "iterator":
                tg = d["targets"]
                target = cls(tg[0], m) if len(tg) == 1 and tg[0] in known_set else "Any"
                src = iterator(name, sp, target)
            elif sp and sp.get("opens"):  # a block whose body runs in another scope (the new country, say)
                src = iterator(name, sp, sp["opens"])
            elif kind == "fallback":
                unverified.append(f"{MODE_NAME[m]}.{name}")
                src = f'    def {pyname(name)}(self, *args: Any, **kw: Any) -> None: self._call("{name}", *args, **kw)'
            else:
                src = method(name, sp, m)
            for s in d["scopes"] or ["none"]:
                body[m][s if s in known_set else "none"].append((pyname(name), src))
        for s, items in links(m, targets, known_set).items():
            body[m][s].extend(items)
    out = [HEADER, ov.PRELUDE]
    for m, base, extra in (("E", "AnyFx", ov.FX + ov.COMMON), ("T", "AnyTrig", ov.TRIG + ov.COMMON)):
        for s in ["none"] + known:
            c = base if s == "none" else cls(s, m)
            items = sorted(body[m][s])
            dup = [n for n in {n for n, _ in items} if [x for x, _ in items].count(n) > 1]
            assert not dup, f"{c}: duplicate methods {dup}"
            lines = [f"\n\nclass {c}({'Scope' if s == 'none' else base}):"]
            if m == "E":
                lines.append(ov.LIMIT.replace("{T}", "AnyTrig" if s == "none" else cls(s, "T")).strip("\n"))
            if s == "none":
                lines.append(extra.strip("\n"))
            lines += [src for _, src in items]
            out.append("\n".join(lines if len(lines) > 1 else lines + ["    pass"]))
    out.append(ov.POSTLUDE)
    out.append("\n\nUNVERIFIED = frozenset({\n" + "".join(f'    "{n}",\n' for n in sorted(unverified)) + "})\n")
    return "\n".join(out), counts, time.time() - t0


HEADER = '''"""Scope-typed EU5 effects and triggers. GENERATED by tools/pdx/gen_api.py: never edit by hand, rerun it after an EU5 patch.

`CountryFx` holds the effects a country scope accepts, `CountryTrig` its triggers; `AnyFx`/`AnyTrig` the any-scope ones
(every scope class derives from them). UNVERIFIED lists the names with only a loose signature: no vanilla call, no docs hint.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, ContextManager, Generic, Iterator, Literal, TypeVar

from pdx.core import Scope
'''


def main():
    text, counts, secs = generate()
    OUT.write_text(text, encoding="utf-8")
    kinds = ["total", "vanilla", "docs", "traits", "override", "iterator", "splice", "scripted", "fallback"]
    print(f"{'':10}" + "".join(f"{k:>10}" for k in kinds))
    for m, label in (("E", "effects"), ("T", "triggers")):
        print(f"{label:10}" + "".join(f"{counts[m].get(k, 0):>10}" for k in kinds))
    print(f"wrote {OUT} ({len(text.splitlines())} lines, {len(text) // 1024} KiB) in {secs:.1f} s")


if __name__ == "__main__":
    main()
