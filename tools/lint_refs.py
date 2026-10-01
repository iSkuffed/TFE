"""Cross-reference checks for lint_script: names a file uses that must exist somewhere (the game reports none of these
until the moment they fire, and often not even then).

    events     trigger_event_*, `id =` and on_action `events = { }` name an event that is defined
    loc        an event's title, desc and option names are localisation keys that exist
    scopes     `scope:x` is saved (or read by vanilla, for scopes the game itself provides) somewhere
    assets     a building type or government reform has its icon file
    values     `has_advance = x`, `research_advance = advance_type:x`, `subject_type = subject_type:x`: a value that vanilla
               always takes from one registry (and in one form, bare or prefixed) names a key that exists, in that form

`refs(base, roots)` returns problems in `base`'s files, looking names up across `roots` (vanilla, DLC, the mod).
"""
import collections
import functools
import re
from pathlib import Path

import lint_script as ls

EVENT = re.compile(r"[a-z_0-9]+\.\d+")
LOC_KEY = re.compile(r"[\w.\-]+")
LOC_LINE = re.compile(r"^\s+([\w.\-]+):\d*\s+\"", re.M)
SAVES = ("save_scope_as", "save_temporary_scope_as", "target_flag")  # a generic action's target_flag is scope:<flag>
SAVE_VALUES = ("save_scope_value_as", "save_temporary_scope_value_as")
EVENT_CALLS = ("id", "trigger_event_silently", "trigger_event_non_silently")
ICONS = {"building_types": "buildings", "government_reforms": "government_reforms/illustrations"}


def with_dlc(game, mod):
    return [game, *sorted((game / "dlc").glob("*")), *([mod] if mod else [])]


def each(node):
    """every Entry under node, depth first."""
    for e in node:
        yield e
        if isinstance(e.val, list):
            yield from each(e.val)


def trees(base):
    for p in ls.script_files(base):
        try:
            yield p, ls.tree_of(p)
        except ValueError:
            continue  # lint_script reports the parse error


def event_ids(root):
    out = set()
    for p, tree in trees(root):
        if "events" in p.relative_to(root).parts:
            out |= {e.key for e in tree if e.key and EVENT.fullmatch(e.key)}
    return out


def loc_keys(root):
    out = set()
    for area in ("main_menu", "in_game"):
        for p in (root / area / "localization" / "english").rglob("*.yml"):
            out |= set(LOC_LINE.findall(p.read_text(encoding="utf-8-sig")))
    return out


def scope_names(text):
    return re.findall(r"scope:(\w+)", text)


def saved_scopes(tree):
    """names saved in a tree, and names read in it."""
    saved, read = set(), set()
    for e in each(tree):
        for s in (e.key, e.val):
            if isinstance(s, str):
                read.update(scope_names(s))
        if e.key in SAVES and isinstance(e.val, str):
            saved.add(e.val)
        if e.key in SAVE_VALUES and isinstance(e.val, list):
            saved |= {c.val for c in e.val if c.key == "name" and isinstance(c.val, str)}
    return saved, read


def event_refs(tree):
    for e in each(tree):
        if e.key in EVENT_CALLS and isinstance(e.val, str) and EVENT.fullmatch(e.val):
            yield e, e.val
        elif e.key == "events" and isinstance(e.val, list):
            for c in e.val:
                if c.key and c.op is None and EVENT.fullmatch(c.key):
                    yield c, c.key


def loc_refs(event):
    """(entry, key) for the title, desc and option names of one event's body."""
    for e in each(event):
        if e.key in ("title", "desc") and isinstance(e.val, str) and LOC_KEY.fullmatch(e.val):
            yield e, e.val
        if e.key == "option" and isinstance(e.val, list):
            for c in e.val:
                if c.key == "name" and isinstance(c.val, str) and LOC_KEY.fullmatch(c.val):
                    yield c, c.val


def defined_names(root, folder):
    out = set()
    for p, tree in trees(root):
        if p.parent.name == folder:
            out |= {re.sub(r"^(?:REPLACE|INJECT|TRY_INJECT|REPLACE_OR_CREATE|TRY_REPLACE):", "", e.key)  # overrides name the vanilla entry
                    for e in tree if e.key and e.op == "="}
    return out


VALUE = re.compile(r"(?:(\w+):)?(\w+)")
NOT_A_KEY = re.compile(r"yes|no|root|prev|this|from|none|always|never|\d+|scope|var|global_var|local_var|culture|dominant_culture")
MIN_CALLS, MIN_SHARE = 8, 0.9
MIN_FIT = 0.98  # how many of vanilla's own values the registry must hold, or it is a coincidence of names
TEXT_ONLY = {"game_concepts", "trigger_localization", "coat_of_arms", "customizable_localization", "effect_localization"}


def slots(tree):
    """(name, param or None, value) for every `name = value` and `name = { param = value }` under tree."""
    for e in each(tree):
        if not e.key or e.key.endswith(("_list", "_flag")):
            continue
        if isinstance(e.val, str):
            yield e, e.key, None, e.val
        elif isinstance(e.val, list):
            for c in e.val:
                if c.key and c.op == "=" and isinstance(c.val, str):
                    yield c, e.key, c.key, c.val


def parts(v):
    m = VALUE.fullmatch(v)
    if not m or NOT_A_KEY.fullmatch(m.group(2)) or m.group(1) in ("scope", "var", "global_var", "local_var", "c", "country"):
        return None
    return None if re.match(r"[A-Z]{2,}", m.group(2)) else m.groups()  # TAGS are made at run time (GILDO, CONST): no registry holds them


@functools.lru_cache(maxsize=None)
def registries(roots):
    """folder name -> the top-level keys its files define (advances, subject_types, pop_types ...)."""
    out = collections.defaultdict(set)
    for r in roots:
        for p, tree in trees(r):
            out[p.parent.name] |= {e.key for e in tree if e.key and e.op == "="}
    return out


def learn_slots(roots_vanilla, regs):
    """{(name, param): (usual prefix or None, registry folder, form is never mixed, every form seen with a real key)} for the slots vanilla fills from one registry in one form."""
    seen = collections.defaultdict(list)
    for r in roots_vanilla:
        for _, tree in trees(r):
            for _, name, param, v in slots(tree):
                if (g := parts(v)) and not (name == "name" or name == "type" and param is None):
                    seen[name, param].append(g)
    out = {}
    for slot, vals in seen.items():
        if len(vals) < MIN_CALLS:
            continue
        prefix, n = collections.Counter(p for p, _ in vals).most_common(1)[0]
        if n / len(vals) < MIN_SHARE:
            continue
        strict = n == len(vals)  # no call in vanilla uses the other form: only then is the other form an error
        keys = [k for p, k in vals if p == prefix]
        folder, hit = max(((f, sum(k in ks for k in keys)) for f, ks in regs.items() if len(ks) >= 3 and f not in TEXT_ONLY),
                          key=lambda fh: fh[1])
        if hit / len(keys) >= MIN_FIT and len(set(keys)) >= 2:
            forms = {p for p, k in vals if k in regs[folder]}  # the forms vanilla writes a real key in
            out[slot] = (prefix, folder, strict, forms)
    return out


def value_problems(base, roots, vanilla):
    roots = tuple(roots)
    regs = registries(roots)
    learned = learn_slots(tuple(r for r in roots if r != base or vanilla) if not vanilla else roots, regs)
    for p, tree in trees(base):
        rel = p.relative_to(base)
        if rel.parts[:2] == ("main_menu", "setup"):  # start data names things defined in start data (dynasties, tags)
            continue
        for e, name, param, v in slots(tree):
            want = learned.get((name, param))
            if not want or not (g := parts(v)):
                continue
            prefix, key = g
            shown = f"{name} = {v}" if param is None else f"{name} = {{ {param} = {v} }}"
            if prefix not in want[3] and want[2]:
                right = f"{want[0]}:{key}" if want[0] else key
                yield f"{rel}:{e.line}: {shown}: vanilla writes this as `{right}`"
            elif prefix in want[3] and key not in regs[want[1]] and not any(key in ks for ks in regs.values()):
                yield f"{rel}:{e.line}: {shown}: {key} is not defined in {want[1]}"  # a key some other registry holds is a coincidence of names (rank_duchy is a location and a country rank)


def refs(base, roots, vanilla=False):
    events = set().union(*(event_ids(r) for r in roots))
    loc = set().union(*(loc_keys(r) for r in roots))
    saved, read = set(), set()
    for r in roots:
        for _, tree in trees(r):
            s, rd = saved_scopes(tree)
            saved |= s
            read |= rd if r != base else set()  # vanilla's reads are the game's own scopes; the mod's are not
    known = saved | (read if not vanilla else set())
    found = []
    for p, tree in trees(base):
        rel = p.relative_to(base)
        say = lambda e, msg: found.append(f"{rel}:{e.line}: {msg}")
        for e, ev in event_refs(tree):
            if ev not in events:
                say(e, f"event {ev} is not defined")
        if "events" in rel.parts:
            for ev in tree:
                if ev.key and EVENT.fullmatch(ev.key) and isinstance(ev.val, list):
                    for e, key in loc_refs(ev.val):
                        if key not in loc:
                            say(e, f"{ev.key}: localisation key {key} is missing")
        if not vanilla:
            _, reads = saved_scopes(tree)
            unsaved = {n for n in reads if n not in known}
            for e in each(tree):
                for s in (e.key, e.val):
                    for n in scope_names(s) if isinstance(s, str) else ():
                        if n in unsaved:
                            say(e, f"scope:{n} is never saved anywhere (save_scope_as = {n})")
    found += list(value_problems(base, roots, vanilla))
    for folder, icons in ICONS.items():
        for name in sorted(defined_names(base, folder)):
            if not any((r / "main_menu/gfx/interface/icons" / icons / f"{name}.dds").exists() for r in roots):
                found.append(f"{base.name}: {folder} {name} has no icon main_menu/gfx/interface/icons/{icons}/{name}.dds")
    return found
