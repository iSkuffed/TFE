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
# files that may name WRE by tag: Honorius's own things. Every other file must say which West it means.
STAY = {
    "in_game/common/international_organizations/tfe_roman_empire.txt",   # the Imperium Romanum's seat and Unity
    "in_game/common/generic_actions/tfe_roman_empire.txt",
    "in_game/common/on_action/tfe_opening.txt", "in_game/events/tfe_opening.txt",   # the 395 opening
    "in_game/common/on_action/tfe_gildo.txt", "in_game/events/tfe_gildo.txt",
    "in_game/common/on_action/tfe_decline_of_the_west.txt",   # day one: only WRE exists
    "in_game/common/situations/tfe_decline_of_the_west.txt",  # can_start is the WRE-only 395 opening
    "in_game/common/on_action/tfe_stilicho.txt", "in_game/events/tfe_stilicho.txt",   # the showdown is Honorius's
    "in_game/common/scripted_effects/tfe_stilicho.txt", "in_game/common/scripted_effects/tfe_usurpers.txt",
    "in_game/common/auto_modifiers/tfe_stilicho.txt",   # Olympius rules for Honorius, not for Stilicho
    "in_game/common/customizable_localization/country_history.txt",
    "in_game/gui/panels/situation/tfe_decline_of_the_west.gui",   # the header and Gildo's hold are WRE's
    "in_game/common/formable_countries/00_formable_countries.txt",   # vanilla, left alone
    TRIGGER,
}
BY_TAG = re.compile(r"c:WRE\b|(?<![\w])tag = WRE\b|GetCountry\('WRE'\)")


def test_the_west_is_either_rome():
    t = flat(TRIGGER)
    assert "tfe_is_western_rome = { OR = { tag = WRE has_variable = tfe_western_rome } }" in t


def test_only_honorius_files_name_wre_by_tag():
    named = set()
    for base in ("in_game", "main_menu/common"):
        for p in (ROOT / base).rglob("*.txt"):
            if BY_TAG.search(re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))):
                named.add(p.relative_to(ROOT).as_posix())
    named -= {n for n in named if n.startswith(("main_menu/setup/", "in_game/setup/", "main_menu/common/scenarios/",
                                                "main_menu/common/coat_of_arms/"))}
    assert named <= STAY, sorted(named - STAY)


def test_migrate_west_marches_on_either_west():
    ga = flat("in_game/common/generic_actions/tfe_migratory.txt")
    west = block(ga, "tfe_migrate_west =")
    assert "declare_war_with_cb = { target = scope:tfe_victim type = casus_belli:cb_tfe_migration }" in west
    assert "any_neighbor_country = { tfe_is_western_rome = yes }" in west
    assert "c:WRE" not in west
    fx = flat("in_game/common/scripted_effects/tfe_migratory.txt")
    assert "every_country = { limit = { tfe_is_western_rome = yes } scope:tfe_host = { add_casus_belli = { target = prev" in fx


def test_the_decline_lasts_while_any_west_stands():
    s = flat("in_game/common/situations/tfe_decline_of_the_west.txt")
    assert "NOT = { any_country = { tfe_is_western_rome = yes } }" in block(s, "can_end =")
    assert "NOT = { any_country = { tfe_is_western_rome = yes } }" in block(s, "on_monthly =")
