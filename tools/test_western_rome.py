import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))


def flat(rel):
    """a script file without comments, whitespace collapsed: `a = {\n\tb = c\n}` reads `a = { b = c }`."""
    return " ".join(re.sub(r"#[^\n]*", "", (ROOT / rel).read_text(encoding="utf-8-sig")).split())


def block(text, head):
    """the `{ ... }` body that follows `head` in flattened text (brace-matched)."""
    i = text.index(head) + len(head)
    i = text.index("{", i)
    depth = 0
    for j in range(i, len(text)):
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        if depth == 0:
            return text[i + 1:j]
    raise ValueError(head)


TRIGGER = "in_game/common/scripted_triggers/tfe_western_rome.txt"
# A file may name WRE by tag only if it is Honorius's own (the 395 opening, his showdown with Stilicho...) and says so in a
# comment: `honorius-only: <why>` (from a script, `doc.note("honorius-only: ...")`). Every other file must say which West
# it means (tfe_is_western_rome).
MARK = "honorius-only:"
BY_TAG = re.compile(r"c:WRE\b|(?<![\w])tag = WRE\b|GetCountry\('WRE'\)")


def test_the_west_is_either_rome():
    t = flat(TRIGGER)
    assert "tfe_is_western_rome = { OR = { tag = WRE has_variable = tfe_western_rome } }" in t


def test_only_honorius_files_name_wre_by_tag():
    named, marked = set(), set()
    for base in ("in_game", "main_menu/common"):
        for p in (ROOT / base).rglob("*.txt"):
            text, rel = p.read_text(encoding="utf-8-sig"), p.relative_to(ROOT).as_posix()
            if BY_TAG.search(re.sub(r"#[^\n]*", "", text)):
                named.add(rel)
            if MARK in text:
                marked.add(rel)
    named -= {n for n in named if n.startswith(("main_menu/setup/", "in_game/setup/", "main_menu/common/scenarios/",
                                                "main_menu/common/coat_of_arms/"))}
    assert named <= marked, f"name the West with tfe_is_western_rome, or mark the file `{MARK} <why>`: {sorted(named - marked)}"
    assert marked <= named, f"marked {MARK} but names no WRE by tag: {sorted(marked - named)}"


def test_migration_marches_on_any_roman_state():
    ga = flat("in_game/common/generic_actions/tfe_fall_of_the_west.txt")
    assert "declare_war_with_cb = { target = scope:target_rome type = casus_belli:cb_tfe_migration }" in ga
    assert "c:WRE" not in ga and "tfe_is_western_rome" not in ga
    tr = flat("in_game/common/scripted_triggers/tfe_western_rome.txt")
    assert "tfe_is_roman_state = { OR = { tfe_is_roman_empire = yes has_variable = tfe_roman_successor } }" in tr


def test_the_decline_lasts_while_any_west_stands():
    s = flat("in_game/common/situations/tfe_decline_of_the_west.txt")
    assert "NOT = { any_country = { tfe_is_western_rome = yes } }" in block(s, "can_end =")
    assert "NOT = { any_country = { tfe_is_western_rome = yes } }" in block(s, "on_monthly =")
