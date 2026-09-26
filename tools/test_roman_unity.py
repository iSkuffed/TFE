"""The Imperium Romanum organization: its script must load (balanced, localized, landed members)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

IO = b.MOD / "in_game/common/international_organizations/tfe_roman_empire.txt"
CB = b.MOD / "in_game/common/casus_belli/tfe_war_of_the_augusti.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_roman_empire_l_english.yml"
START = b.MOD / "main_menu/setup/start"


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def loc_keys():
    return set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))


def test_script_files_are_balanced_and_bom_prefixed():
    for p in (IO, CB, LOC):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in (IO, CB):
        assert code(p).count("{") == code(p).count("}"), p.name


def test_everything_shown_to_the_player_is_localized():
    keys = loc_keys()
    io = code(IO)
    wanted = {"tfe_roman_empire", "tfe_roman_empire_desc", "tfe_unity", "tfe_unity_desc", "tfe_unity_DISPLAY",
              "cb_tfe_war_of_the_augusti", "cb_tfe_war_of_the_augusti_desc"}
    wanted |= set(re.findall(r'desc = "(\w+)"', io))
    assert not wanted - keys, sorted(wanted - keys)


def test_unity_thresholds_match_the_design():
    io = code(IO)
    assert "tfe_roman_empire = {" in io and "tfe_unity = {" in io
    assert re.search(r"has_military_access = \{\s*var:tfe_unity >= 75", io)
    assert re.search(r"join_defensive_wars_auto_call = \{[^}]*var:tfe_unity >= 75", io)
    assert re.search(r"join_defensive_wars_can_call = \{[^}]*var:tfe_unity >= 50", io)
    assert "scope:recipient.var:tfe_unity < 50" in io                       # civil war below 50
    assert re.search(r"auto_disband_trigger = \{[^}]*var:tfe_unity <= 0", io)
    assert "TFE_UNITY_ACCESS_DENIED" in io                                   # denied access drains unity
    assert "cb_tfe_war_of_the_augusti = {" in code(CB) and "var:tfe_unity < 50" in code(CB)


def test_setup_creates_the_io_with_both_landed_empires_and_mutual_access():
    countries = (START / "10_countries.txt").read_text(encoding="utf-8")
    landed = set(re.findall(r"^\t\t([A-Z][A-Z0-9]{2}) = \{", countries, re.M))
    setup = code(START / "15_international_organizations.txt")
    m = re.search(r"type = tfe_roman_empire.*?members = \{([^}]*)\}", setup, re.S)
    assert m and set(m.group(1).split()) == {"WRE", "EAR"} <= landed
    dip = code(START / "12_diplomacy.txt")
    for a, c in (("WRE", "EAR"), ("EAR", "WRE")):
        assert re.search(rf"scripted_oneway = \{{ first = {a} second = {c} type = military_access \}}", dip)


def test_io_has_member_opinion_and_diplomatic_status():
    # error.log: "needs an opinion of other members, add io_opinion_tfe_roman_empire in /biases/"
    bias = b.MOD / "in_game/common/biases/tfe_biases.txt"
    assert bias.read_bytes().startswith(b"\xef\xbb\xbf") and re.search(r"io_opinion_tfe_roman_empire = \{\s*value = \d+", code(bias))
    assert {"diplomatic_status_tfe_roman_empire_name", "diplomatic_status_tfe_roman_empire_tooltip"} <= loc_keys()


FORMABLES = "in_game/common/formable_countries/00_formable_countries.txt"


def test_the_empires_cannot_form_vanilla_countries_except_rome():
    # the AI forms any formable it can: WRE turned into Italy, EAR into Byzantium, Eastern Jin into CHI (with Ming effects)
    text = (b.MOD / FORMABLES).read_text(encoding="utf-8-sig")
    blocks = re.split(r"^(?=\w+ = \{)", text, flags=re.M)
    potentials = {bl.split()[0]: re.search(r"potential = \{(.*?)\n\t\}", bl, re.S).group(1)
                  for bl in blocks if re.match(r"\w+ = \{", bl)}
    assert len(potentials) == len(re.findall(r"^\w+ = \{", (b.GAME / FORMABLES).read_text(encoding="utf-8-sig"), re.M))
    for bl in blocks:
        assert len(re.findall(r"^\tpotential = \{", bl, re.M)) <= 1, bl.split()[0]   # a second one would shadow ours
    for key, pot in potentials.items():
        barred = "NOR = { tag = WRE tag = EAR tag = JIN }" in pot
        assert barred == (key != "ROM_f"), key   # restoring the whole Empire stays a goal


def test_formables_override_is_regenerated_from_the_current_game():
    vanilla = (b.GAME / FORMABLES).read_text(encoding="utf-8-sig")
    assert (b.MOD / FORMABLES).read_text(encoding="utf-8-sig") == b.bar_empires_from_formables(vanilla)


def test_io_panel_override_is_regenerated_from_the_current_game():
    # the two Augusti head the Imperium's window (leaders in the IO, the union header in the panel)
    assert "add_to_list = leaders" in code(IO)
    vanilla = (b.GAME / b.IO_PANEL).read_text(encoding="utf-8-sig")
    assert (b.MOD / b.IO_PANEL).read_text(encoding="utf-8-sig") == b.augusti_in_io_header(vanilla)
