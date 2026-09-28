"""The West's burdens (tax-free senators, a hidden levy, a debased coin) and the reforms that lift them; Africa's grain,
Pannonia's recruits and the frontier works of Britain, the Rhine and the Danube."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b
import location_templates as lt

PRIVILEGES = b.MOD / "in_game/common/estate_privileges/tfe_late_roman_west.txt"
REFORMS = b.MOD / "in_game/common/government_reforms/tfe_late_roman_west.txt"
AUTO = b.MOD / "in_game/common/auto_modifiers/tfe_late_roman_west.txt"
FRONTIER = b.MOD / "in_game/common/building_types/tfe_frontier.txt"
EFFECTS = b.MOD / "in_game/common/scripted_effects/tfe_lands.txt"
ON_ACTION = b.MOD / "in_game/common/on_action/tfe_lands.txt"
MODS = tuple(b.MOD / f"main_menu/common/static_modifiers/{m}.txt"
             for m in ("tfe_granary_of_rome", "tfe_pannonian_recruiting_grounds"))
ICONS = b.MOD / "main_menu/gfx/interface/icons"
ICON_MAP = b.MOD / "main_menu/common/modifier_icons/tfe_modifier_icons.txt"
COUNTRIES = b.MOD / "main_menu/setup/start/10_countries.txt"
CITIES = b.MOD / "main_menu/setup/start/07_cities_and_buildings.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_late_roman_west_l_english.yml"
SCRIPTS = (PRIVILEGES, REFORMS, AUTO, FRONTIER, EFFECTS, ON_ACTION) + MODS


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def blocks(*ps):
    return {k: v for p in ps for k, v in re.findall(r"^(\w+) = \{(.*?)^\}", code(p), re.M | re.S)}


def wre():
    return re.search(r"\bWRE = \{(.*?)\n\t\t\}", COUNTRIES.read_text(encoding="utf-8-sig"), re.S).group(1)


def test_files_are_balanced_and_bom_prefixed():
    for p in SCRIPTS + (LOC,):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in SCRIPTS:
        assert code(p).count("{") == code(p).count("}"), p.name


def test_everything_shown_is_localized_and_has_an_icon():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    wanted = {k for n in blocks(PRIVILEGES, REFORMS, FRONTIER) for k in (n, f"{n}_desc")}
    wanted |= {f"AUTO_MODIFIER_{k}_{m}" for m in blocks(AUTO) for k in ("NAME", "DESC")}
    wanted |= {f"STATIC_MODIFIER_{k}_{m}" for m in blocks(*MODS) for k in ("NAME", "DESC")}
    wanted |= set(re.findall(r"text = (\w+)", code(PRIVILEGES)))
    assert not wanted - keys, sorted(wanted - keys)
    # the map badge of a template modifier is one of its effects' icons, so each has one effect, with a plus icon
    ours = dict(re.findall(r'^REPLACE:(\w+) = \{\s*positive = "gfx/interface/icons/(\S+)"', code(ICON_MAP), re.M))
    for p in MODS:
        effects = re.findall(r"^\t(\w+) = -?[\d.]+", blocks(p)[p.stem], re.M)
        assert len(effects) == 1, (p.name, effects)
        assert effects[0] in ("local_wheat_output_modifier",) or (ICONS / ours[effects[0]]).exists(), effects[0]
    for n in blocks(FRONTIER):   # a building's icon is named for it
        assert (ICONS / f"buildings/{n}.dds").exists(), n


def test_every_privilege_gives_its_estate_power():
    # else the game logs "The privilege '...' has no power set"
    for name, body in blocks(PRIVILEGES).items():
        estate = re.search(r"estate = (\w+)_estate", body).group(1)
        assert f"global_{estate}_estate_power = " in body, name


def test_the_west_starts_with_both_burdens():
    govs = [l.split(" = ", 1)[1] for l in (b.TOOLS / "governments.txt").read_text(encoding="utf-8").splitlines()
            if l.startswith("WRE = privilege = ")]
    assert govs == [f"privilege = {{ {' '.join(blocks(PRIVILEGES))} }}"]
    assert f"\t\t\t\t{govs[0]}" in wre().replace("\r", "")   # 10_countries is borders.py's output


def test_each_burden_is_locked_until_its_reform_and_never_returns():
    reforms = blocks(REFORMS)
    for name, body in blocks(PRIVILEGES).items():
        done = re.search(r"can_revoke = \{.*?has_variable = (\w+)", body, re.S).group(1)
        assert any(f"set_variable = {{ name = {done} }}" in r for r in reforms.values()), name
        assert f"set_variable = {{ name = {name}_revoked }}" in body, name
        assert f"NOT = {{ has_variable = {name}_revoked }}" in body, name
    coin = re.search(r"NOT = \{ has_variable = (\w+) \}", blocks(AUTO)["tfe_debased_coinage"]).group(1)
    assert any(f"set_variable = {{ name = {coin} }}" in r for r in reforms.values())
    for name, body in reforms.items():   # done once, so the slot can be freed afterwards
        assert "on_fully_activated" in body and "NOT = { has_variable" in body, name


def owned():
    return set(re.search(r"own_control_core = \{(.*?)\}", wre(), re.S).group(1).split())


def test_the_granaries_are_the_wests_and_start_fully_worked():
    known = set(re.findall(r"^(\w+) = \{", (b.MAP / "location_templates.txt").read_text(encoding="utf-8-sig"), re.M))
    assert "tunis" in lt.GRANARIES   # Carthage
    assert not set(lt.GRANARIES) - known and not set(lt.GRANARIES) - owned(), set(lt.GRANARIES) - known - owned()
    worked = re.findall(r"location:(\w+) = \{ tfe_work_granary_to_the_limit = yes \}", code(ON_ACTION))
    assert worked == list(lt.GRANARIES)


def test_the_map_carries_the_lands_modifiers():
    # template modifiers: they badge the goods marker in the raw-material map mode (vanilla: Almaden, Skane)
    ours = (b.MOD / "in_game/map_data/location_templates.txt").read_text(encoding="utf-8-sig")
    assert ours == lt.build(), "rerun tools/location_templates.py"
    tagged = dict(re.findall(r"^(\w+) = \{ modifier = (tfe_\w+) ", ours, re.M))
    assert {m for m in tagged.values()} == {p.stem for p in MODS}
    assert {l for l, m in tagged.items() if m == "tfe_granary_of_rome"} == set(lt.GRANARIES)
    assert len([m for m in tagged.values() if m == "tfe_pannonian_recruiting_grounds"]) > 40
    for l in lt.GRANARIES:
        assert re.search(rf"^{l} = \{{[^\n]*raw_material = wheat\b", ours, re.M), l


def test_italy_gave_a_fifth_of_its_wheat_land_to_the_villas():
    anc = b.load_hierarchy()
    vanilla = (b.MAP / "location_templates.txt").read_text(encoding="utf-8-sig")
    ours = (b.MOD / "in_game/map_data/location_templates.txt").read_text(encoding="utf-8-sig")
    def wheat(text):
        return {l for l in re.findall(r"^(\w+) = \{[^\n]*raw_material = wheat\b", text, re.M)
                if anc[l][2] == "italy_region"}
    before, after = wheat(vanilla), wheat(ours)
    assert after < before and round(len(before) * 0.2) == len(before - after) == len(lt.ITALIAN_VILLAS)
    assert "rome" in after   # the Po valley, Sicily and Sardinia keep theirs too
    assert not {anc[l][3] for l in before - after} & {"lombardy_area", "sicily_area", "sardinia_area"}


def test_the_frontier_works_hold_a_zone_of_control_on_roman_frontier_land():
    placed = re.findall(r"^\s*(tfe_\w+) = \{ tag = (\w+) level = 1 location = (\w+) \}",
                        CITIES.read_text(encoding="utf-8-sig"), re.M)
    assert {k for k, _, _ in placed} == set(blocks(FRONTIER)) == set(b.ROMAN_FRONTIER)
    assert [(k, t, l) for k, places in b.ROMAN_FRONTIER.items() for t in b.ROMAN_EMPIRES
            for l in places.get(t, ())] == placed
    castles = {l for t in b.ROMAN_EMPIRES for l in b.ROMAN_FORTS[t]}
    text = COUNTRIES.read_text(encoding="utf-8-sig")
    for kind, tag, loc in placed:
        block = re.search(rf"\b{tag} = \{{.*?own_control_core = \{{(.*?)\}}", text, re.S).group(1)
        assert loc in block.split() and loc not in castles, (kind, tag, loc)
    for name, body in blocks(FRONTIER).items():
        assert "propagating_zone_of_control = yes" in body and "local_defensive = " in body, name
        assert re.search(r"country_potential = \{\s*always = no\s*\}", body), name   # placed at start, never built
