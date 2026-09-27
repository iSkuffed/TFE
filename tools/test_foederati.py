"""Foederati: a zero-tribute subject type whose foedus lapses when either ruler dies (Theodosius: at start)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

SUBJECT = b.MOD / "in_game/common/subject_types/tfe_foederati.txt"
EVENT = b.MOD / "in_game/events/tfe_foederati.txt"
ON_ACTION = b.MOD / "in_game/common/on_action/tfe_foederati.txt"
CB = b.MOD / "in_game/common/casus_belli/tfe_foedus_broken.txt"
BIAS = b.MOD / "in_game/common/biases/tfe_biases.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_foederati_l_english.yml"
SCRIPTS = (SUBJECT, EVENT, ON_ACTION, CB)


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def test_files_are_balanced_and_bom_prefixed():
    for p in SCRIPTS + (LOC,):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in SCRIPTS:
        assert code(p).count("{") == code(p).count("}"), p.name


def test_everything_shown_is_localized():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    wanted = {"tfe_foederati", "tfe_foederati_desc", "tfe_foederati_subject_opinion", "tfe_foederati_overlord_opinion",
              "cb_tfe_foedus_broken", "cb_tfe_foedus_broken_desc"}
    wanted |= set(re.findall(r"(?:title|desc|name) = (tfe_foederati\.[\w.]+)", code(EVENT)))
    assert not wanted - keys, sorted(wanted - keys)
    for key in ("tfe_foederati_subject_opinion", "tfe_foederati_overlord_opinion"):
        assert re.search(rf"^{key} = \{{\s*value = -?\d+", code(BIAS), re.M), key


def test_foederati_pay_no_tribute_and_join_all_wars():
    s = code(SUBJECT)
    assert "subject_pays" not in s
    for war in ("offensive", "defensive"):
        assert re.search(rf"join_{war}_wars_always = \{{ NOT = \{{ scope:actor \?= \{{ is_subject_of = scope:recipient \}} \}} \}}", s)
    # the annona: whatever Rome pays, the foederati receive
    paid = re.search(r"overlord \?= \{ add_gold = -([\d.]+) \}\s*add_gold = ([\d.]+)", s)
    assert paid and paid.group(1) == paid.group(2)


def test_the_foedus_lapses_on_either_death_and_at_start():
    oa = code(ON_ACTION)
    assert re.search(r"on_game_start = \{\s*on_actions = \{ tfe_on_start_theodosius_dead \}", oa)
    assert re.search(r"on_ruler_death = \{\s*on_actions = \{ tfe_on_ruler_death_foedus_lapses \}", oa)
    assert oa.count("trigger_event_non_silently = tfe_foederati.1") == 3   # start, own ruler, overlord's ruler
    ev = code(EVENT)
    assert "tfe_foederati.1 = {" in ev and "cancel_subject = root" in ev
    assert "casus_belli:cb_tfe_foedus_broken" in ev and "cb_tfe_foedus_broken = {" in code(CB)


def test_the_empires_foederati_at_start():
    dip = code(b.MOD / "main_menu/setup/start/12_diplomacy.txt")
    for sub in ("VIS", "SLH"):
        assert re.search(rf"first = EAR second = {sub} subject_type = tfe_foederati\b", dip), sub
