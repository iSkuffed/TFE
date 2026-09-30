"""Infer EU5 effect/trigger call shapes: from vanilla script (what the game really accepts) and from the docs' usage hints.

A spec is a dict: shapes (set of bare/scalar/block/cmp), req and opt (block keys, in order), kinds (scalar value kinds).
`scan(game)` walks vanilla (~7 s) and returns {"E"|"T": {name: stat}, "iter": {"E.every": {key: count}, ...}}.
"""
import collections
import itertools
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import borders as b
from lint_script import EFFECT_BLOCKS, TRIGGER_BLOCKS, parse

EB = EFFECT_BLOCKS | {"else_effect"}
TB = TRIGGER_BLOCKS | {"trigger_else", "alternative_limit", "is_visible", "can_be_picked", "is_valid_target"}
ITER = re.compile(r"(every|random|ordered|any)_")
ITER_KEYS = {"count", "percent", "order_by", "position", "max", "min", "check_range_bounds", "alias", "weight"}
IDENT = re.compile(r"[A-Za-z_]\w*")
NONEQ = {"<", ">", "<=", ">=", "!="}


def vkind(v):
    if v in ("yes", "no"):
        return "bool"
    return "other"


def vanilla_files(game):
    for base in [game] + sorted((game / "dlc").glob("*")):
        for area in ("in_game", "main_menu"):
            for p in sorted((base / area).rglob("*.txt")):
                parts = p.relative_to(base).parts
                if parts[:2] != ("in_game", "map_data") and not {"gfx", "localization", "gui"} & set(parts):
                    yield p


def scan(game, names, mod=None):
    """names: {"E": set of effect names, "T": set of trigger names} (docs + scripted). mod: the mod's root, scanned too."""
    stats = collections.defaultdict(lambda: {"n": 0, "shapes": collections.Counter(), "keys": collections.Counter(), "pos": collections.Counter(),
                                             "kinds": collections.Counter(), "badops": collections.Counter()})
    iters = collections.defaultdict(collections.Counter)

    def walk(entries, mode):
        for e in entries:
            k = e.key
            if k is None:
                if isinstance(e.val, list):
                    walk(e.val, mode)
                continue
            if mode and k in names[mode]:
                s = stats[(mode, k)]
                s["n"] += 1
                if e.op is None:
                    s["shapes"]["bare"] += 1
                elif isinstance(e.val, list):
                    s["shapes"]["block"] += 1
                    inner = {x.key for x in e.val if x.key and IDENT.fullmatch(x.key)}
                    s["keys"].update(inner)
                    order = list(dict.fromkeys(x.key for x in e.val if x.key in inner))
                    for i, key in enumerate(order):  # where in the block this key usually sits, 0 = first, 1 = last
                        s["pos"][key] += i / max(len(order) - 1, 1)
                    for x in e.val:
                        if x.key and x.op in NONEQ:
                            s["badops"][x.key] += 1
                    m = ITER.match(k)
                    if m:
                        iters[f"{mode}.{m.group(1)}"].update(inner & ITER_KEYS)
                else:
                    s["shapes"]["scalar"] += 1
                    s["kinds"][vkind(e.val)] += 1
            nmode = "E" if k in EB else "T" if k in TB else mode
            if isinstance(e.val, list):
                walk(e.val, nmode)

    for p in itertools.chain(vanilla_files(game), vanilla_files(mod) if mod else ()):
        try:
            tree = parse(p.read_text(encoding="utf-8-sig"))
        except ValueError:
            continue
        s = str(p)
        if "scripted_effects" in s or "scripted_triggers" in s:
            mode = "E" if "scripted_effects" in s else "T"
            for x in tree:
                if isinstance(x.val, list):
                    walk(x.val, mode)
        else:
            walk(tree, None)
    return {"E": {n: stats[("E", n)] for n in names["E"] if stats[("E", n)]["n"]},
            "T": {n: stats[("T", n)] for n in names["T"] if stats[("T", n)]["n"]},
            "iter": iters}


def spec_vanilla(name, st, names):
    """a stat -> spec, or None when the calls show no usable shape (only calls with effects inside, say).
    Keys that are themselves effect/trigger names and rare are the block's body, not its parameters."""
    shapes = set(st["shapes"])
    keys = []
    for k, c in sorted(st["keys"].items(), key=lambda kc: (-kc[1], kc[0])):
        if k in names and c < st["shapes"]["block"] / 2:
            continue
        keys.append(k)
    if "block" in shapes and not keys:
        return None
    n = st["shapes"]["block"]
    req = [k for k in keys if st["keys"][k] == n] if n >= 3 else []
    order = sorted(keys, key=lambda k: (st["pos"][k] / st["keys"][k], k))  # vanilla's usual order, so ports diff cleanly
    # a key vanilla only ever writes with `>=`, `<`...: the caller passes Cmp(op, value)
    types = {k: "Cmp" for k in keys if st["badops"][k] == st["keys"][k]}
    return {"shapes": shapes, "req": req, "opt": [k for k in keys if k not in req], "kinds": set(st["kinds"]),
            "order": order, "types": types}


def hint(name, desc):
    """a docs description -> spec from a `name = { k = v ... }` or `name = x` usage line, or None."""
    m = re.search(rf"\b{name}\s*=\s*(\{{)?", desc)
    if not m:
        return None
    if not m.group(1):
        return {"shapes": {"scalar"}, "req": [], "opt": [], "kinds": set()} if re.match(r"\s*[<\w\"]", desc[m.end():]) else None
    depth, i = 1, m.end()
    while i < len(desc) and depth:
        depth += {"{": 1, "}": -1}.get(desc[i], 0)
        i += 1
    body = desc[m.end():i - 1]
    while re.search(r"\{[^{}]*\}", body):
        body = re.sub(r"\{[^{}]*\}", "X", body)
    body = re.sub(r"#[^\n]*", "", body)
    keys = []
    for ks in re.findall(r"(?<![\w:])(\w+(?:/\w+)*)\s*=", body):
        for k in ks.split("/"):
            if IDENT.fullmatch(k) and k not in keys:
                keys.append(k)
    return {"shapes": {"block"}, "req": [], "opt": keys, "kinds": set()} if keys else None
