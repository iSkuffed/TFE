"""Rome raises no peasant levies: both empires buy recruits and pay a standing army. The West starts with its field army
fed in kind; the East is larger but wounded in 395 (Thrace ravaged by the Goths, the Huns over the Caucasus, Isauria)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

AUTO = b.MOD / "in_game/common/auto_modifiers/tfe_roman_balance.txt"
MODS = b.MOD / "main_menu/common/static_modifiers/tfe_east_395.txt"
ON_ACTION = b.MOD / "in_game/common/on_action/tfe_east_395.txt"
EVENT = b.MOD / "in_game/events/tfe_east_395.txt"
ARMIES = b.MOD / "main_menu/setup/start/27_armies.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_east_395_l_english.yml"
SCRIPTS = (AUTO, MODS, ON_ACTION, EVENT)
MEN = {"a_footmen": 500, "a_armored_horsemen": 200}   # age 1: infantry 0.5, cavalry 0.2 of REGIMENT_SIZE 1000


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def blocks(p):
    return dict(re.findall(r"^([\w.]+) = \{(.*?)^\}", code(p), re.M | re.S))


def test_files_are_balanced_and_bom_prefixed():
    for p in SCRIPTS + (LOC,):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
        if p != LOC:
            assert code(p).count("{") == code(p).count("}"), p.name


def test_rome_buys_recruits_instead_of_raising_levies():
    auto = blocks(AUTO)
    rec = auto["tfe_roman_recruitment"]
    assert set(re.findall(r"has_or_had_tag = (\w+)", rec)) == {"WRE", "EAR"}
    assert "global_army_levy_size_modifier = -0.6" in rec
    kind = auto["tfe_rations_in_kind"]
    assert set(re.findall(r"has_or_had_tag = (\w+)", kind)) == {"WRE"}
    assert "army_maintenance_efficiency = 0.3" in kind


def test_the_west_starts_with_its_field_army():
    armies = re.findall(r"army = \{\s*country = (\w+)\s*location = (\w+)\s*sub_units = \{(.*?)\}\s*\}", code(ARMIES), re.S)
    men = sum(MEN[u] for tag, _, units in armies if tag == "WRE" for u in re.findall(r"(\w+) = \{", units))
    regiments = sum(len(re.findall(r"(\w+) = \{", units)) for tag, _, units in armies if tag == "WRE")
    assert 9000 <= men <= 10500 and 20 <= regiments <= 24, (men, regiments)
    places = {loc for tag, loc, _ in armies if tag == "WRE"}
    assert places == {"milano", "trier"}   # the praesental army at Mediolanum, the Gallic army at Augusta Treverorum


def test_the_east_is_wounded_where_history_wounded_it():
    oa, ev, mods = code(ON_ACTION), code(EVENT), blocks(MODS)
    assert set(mods) == {"tfe_ravaged_by_the_goths", "tfe_hunnic_ravages", "tfe_isaurian_brigands"}
    for area in ("thrace_area", "bulgaria_area", "serbia_area", "macedonia_area"):
        assert f"area:{area}" in oa, area
    assert "modifier = tfe_ravaged_by_the_goths years = 15" in oa and "decaying = yes" in mods["tfe_ravaged_by_the_goths"]
    assert "province_definition:icel_province" in oa and "modifier = tfe_isaurian_brigands" in oa
    assert re.search(r"id = tfe_east_395\.1 days = \d+", oa)
    for place in ("area:armenian_highlands_area", "area:cappadocia_area", "area:cilicia_area",
                  "province_definition:antakya_province", "province_definition:halab_province"):
        assert place in ev, place
    assert "modifier = tfe_hunnic_ravages years = 2" in ev
    assert "filastin_province" not in ev   # the Huns reached Syria and Antioch, not Palestine


def test_everything_shown_is_localized():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    wanted = {f"AUTO_MODIFIER_{k}_{m}" for m in blocks(AUTO) for k in ("NAME", "DESC")}
    wanted |= {f"STATIC_MODIFIER_{k}_{m}" for m in blocks(MODS) for k in ("NAME", "DESC")}
    wanted |= set(re.findall(r"(?:title|desc|name) = (tfe_east_395\.[\w.]+)", code(EVENT)))
    assert not wanted - keys, sorted(wanted - keys)
