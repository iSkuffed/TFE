"""Cross-reference checks for lint_script: names a file uses that must exist somewhere (the game reports none of these
until the moment they fire, and often not even then).

    events     trigger_event_*, `id =` and on_action `events = { }` name an event that is defined
    loc        an event's title, desc and option names are localisation keys that exist
    scopes     `scope:x` is saved (or read by vanilla, for scopes the game itself provides) somewhere
    assets     a building type or government reform has its icon file

`refs(base, roots)` returns problems in `base`'s files, looking names up across `roots` (vanilla, DLC, the mod).
"""
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
    for folder, icons in ICONS.items():
        for name in sorted(defined_names(base, folder)):
            if not any((r / "main_menu/gfx/interface/icons" / icons / f"{name}.dds").exists() for r in roots):
                found.append(f"{base.name}: {folder} {name} has no icon main_menu/gfx/interface/icons/{icons}/{name}.dds")
    return found
