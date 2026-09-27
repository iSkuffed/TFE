"""The Senior Augustus leads the Imperium Romanum and decrees edicts that bind both halves and spend Unity."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

IO = b.MOD / "in_game/common/international_organizations/tfe_roman_empire.txt"
STATUS = b.MOD / "in_game/common/international_organization_special_statuses/tfe_roman_empire.txt"
LAW = b.MOD / "in_game/common/laws/tfe_edicts.txt"
ON_ACTION = b.MOD / "in_game/common/on_action/tfe_senior_augustus.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_edicts_l_english.yml"
SCRIPTS = (STATUS, LAW, ON_ACTION)


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def test_files_are_balanced_and_bom_prefixed():
    for p in SCRIPTS + (LOC,):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in SCRIPTS:
        assert code(p).count("{") == code(p).count("}"), p.name


def test_everything_shown_is_localized():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    names = set(re.findall(r"^(\w+) = \{", code(STATUS) + code(LAW), re.M))
    names |= set(re.findall(r"^\t(tfe_edict_\w+_policy) = \{", code(LAW), re.M))
    wanted = names | {f"{n}_desc" for n in names}
    assert not wanted - keys, sorted(wanted - keys)


def test_the_senior_augustus_leads_the_empire():
    io = code(IO)
    assert "has_leader_country = yes" in io
    assert re.search(r"special_statuses_implemented = \{ tfe_senior_augustus \}", io)
    assert "set_leader_country = root" in code(STATUS)
    oa = code(ON_ACTION)
    assert "country = c:EAR" in oa     # Arcadius, Augustus since 383
    assert "on_ruler_death" in oa and "international_organization_remove_special_status" in oa


def test_every_edict_spends_unity_binds_and_has_a_benefit_and_a_cost():
    law = code(LAW)
    assert "var:tfe_unity >= 50" in law and "NOT = { has_variable = tfe_edict_binds }" in law
    assert "requires_vote = no" in law, "IO laws default to a member vote; edicts are decreed"
    edicts = re.findall(r"^\t(tfe_edict_\w+_policy) = \{(.*?)^\t\}", law, re.M | re.S)
    assert len(edicts) == 5
    for name, body in edicts:
        assert "change_variable = { name = tfe_unity add = -5 }" in body, name
        assert "set_variable = { name = tfe_edict_binds years = 5 }" in body, name
        mods = re.search(r"country_modifier = \{(.*?)\}", body, re.S).group(1)
        values = [float(v) for v in re.findall(r"= (-?[\d.]+)", mods)]
        assert len(values) == 2 and min(values) < 0 < max(values), name

