import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
import arms  # noqa: E402

OUT = arms.outputs()
TEXT = OUT["in_game/common/goods_demand/tfe_arms.txt"]
LOC = OUT["main_menu/localization/english/replace/tfe_arms_l_english.yml"]


def test_no_unit_or_pop_buys_firearms():
    assert "firearms" not in TEXT


def test_nothing_generated_buys_firearms():
    for rel, text in OUT.items():
        assert not re.search(r"^\s*firearms\s*=", text, re.M), rel


def test_every_firearms_entry_is_replaced_and_costs_the_same():
    entries = arms.vanilla_firearms_entries()
    assert {"infantry_construction", "rifle_infantry_maintenance", "korean_gunnery_construction", "pop_demand"} <= set(entries)
    for entry, before in entries.items():
        block = TEXT.split(f"REPLACE:{entry} = {{", 1)[1].split("}", 1)[0]
        weaponry = float(block.split("weaponry =", 1)[1].split()[0])
        assert abs(weaponry - (before[0] + before[1])) < 1e-9, entry


def test_a_demand_keeps_its_other_goods():
    block = TEXT.split("REPLACE:heavy_infantry_construction = {", 1)[1].split("}", 1)[0]
    assert "leather = 0.1" in block and "tools = 0.1" in block and "category = regiment_construction" in block


def test_cannons_are_siege_equipment():
    assert ' cannons: "Siege Equipment"' in LOC
    assert ' cannon_maker: "Siege Workshop"' in LOC and ' cannons_factory: "Arsenal"' in LOC


def test_every_renamed_unit_exists_and_has_text():
    keys = arms.vanilla_unit_keys()
    for key, (name, desc) in arms.UNITS.items():
        assert key in keys and name and desc, key
        assert f' {key}: "{name}"' in LOC and f' {key}_desc: "{desc}"' in LOC
        assert '"' not in name + desc, key


def test_the_brief_names_are_used():
    got = {k: v[0] for k, v in arms.UNITS.items()}
    assert got["a_handgonners"] == "Plumbatarii" and got["a_grenadiers"] == "Plumbatarii Veterani"
    assert got["a_musketeers"] == "Scutati" and got["a_hunters"] == "Exculcatores"
    assert [got[k] for k in ("a_pistoleers", "a_cuirassiers", "a_light_dragoons")] == ["Cataphracti", "Clibanarii", "Equites Sagittarii"]
    assert [got[k] for k in ("n_carrack", "n_caravel", "n_flute", "n_galleon", "n_war_galleon")] == \
        ["Navis Oneraria", "Dromon", "Chelandion", "Great Dromon", "Ousiakos"]
    assert [got[k] for k in ("n_frigate", "n_twodecker", "n_threedecker", "n_ship_of_the_line")] == \
        ["Liburna", "Bireme", "Trireme", "Pamphylos"]


def test_no_gunpowder_name_is_left_on_a_buildable_unit():
    gunpowder = ("arquebus", "musket", "cannon", "pistol", "grenadier", "fusilier", "dragoon", "frigate", "galleon", "carrack")
    assert not [n for n, _ in arms.UNITS.values() if any(w in n.lower() for w in gunpowder)]


def test_the_top_road_keeps_its_numbers_but_not_its_rails():
    text = OUT["in_game/common/road_types/tfe_roads.txt"]
    block = text.split("REPLACE:railroad = {", 1)[1].split("\n}", 1)[0]
    assert "spline_style_id = 2" in block and "proximity = 15" in block and "level = 4" in block
    assert "color = map_modern_road" in block and "movement_cost = -0.8" in block and "market_access = -0.4" in block


def test_the_roads_are_renamed():
    assert ' railroad: "Via Publica"' in LOC and ' modern_road: "Military Road"' in LOC
    assert ' gravel_road: "Track"' in LOC and ' paved_road: "Paved Road"' in LOC


FOLDERS = {
    "in_game/common/goods_demand": {"from_events.txt"},
    "in_game/common/production_methods": set(),
    "in_game/common/building_types": set(),
}
GAME = arms.b.GAME


def firearms_inputs(text):
    """{top-level entry} of every `firearms = <amount>` line in a vanilla file (a plain scan, not the parser's)."""
    found, entry, depth = set(), None, 0
    for line in text.splitlines():
        line = line.split("#", 1)[0]
        if depth == 0 and "{" in line and "=" in line:
            entry = line.split("=", 1)[0].strip()
        if depth >= 1 and line.split("=", 1)[0].strip() == "firearms":
            found.add(entry)
        depth += line.count("{") - line.count("}")
    return found


def test_every_vanilla_block_that_buys_firearms_is_replaced():
    for folder, skip in FOLDERS.items():
        replaced = set(arms.vanilla_firearms_blocks()[folder]) | (set(arms.vanilla_road_demands()) if folder.endswith("goods_demand") else set())
        written = {line.split(" = ", 1)[0].removeprefix("REPLACE:") for line in OUT[f"{folder}/tfe_arms.txt"].splitlines()
                   if line.startswith("REPLACE:")}
        assert replaced == written, folder
        for p in sorted((GAME / folder).glob("*.txt")):
            if p.name not in skip:
                assert firearms_inputs(p.read_text(encoding="utf-8-sig")) <= written, p.name


def test_the_plain_scan_finds_the_inputs_it_should():
    assert "barracks" in firearms_inputs((GAME / "in_game/common/building_types/manpower_buildings.txt").read_text(encoding="utf-8-sig"))
    assert "soldier_building_maintenance" in firearms_inputs(
        (GAME / "in_game/common/production_methods/unsorted_building_inputs.txt").read_text(encoding="utf-8-sig"))


def test_no_replaced_building_or_method_is_also_changed_by_another_tfe_file():
    for folder in ("in_game/common/production_methods", "in_game/common/building_types"):
        keys = set(arms.vanilla_firearms_blocks()[folder])
        for p in sorted((ROOT / folder).glob("*.txt")):
            if p.name == "tfe_arms.txt":
                continue
            text = p.read_text(encoding="utf-8-sig")
            for key in keys:
                assert not re.search(rf"^(?:\w+:)?{key}\s*=", text, re.M), (p.name, key)


def test_a_replaced_building_keeps_everything_but_firearms():
    text = OUT["in_game/common/building_types/tfe_arms.txt"]
    block = text.split("REPLACE:armory = {", 1)[1].split("\nREPLACE:", 1)[0]
    assert "weaponry = 1" in block and "leather = 0.5" in block and "can_recruit_regiment_in_this_location = yes" in block


def _demands(text):
    from lint_script import parse
    from pdx.core import from_entries
    return {n.key.removeprefix("REPLACE:"): {k.key: float(k.val) for k in n.val if k.key not in ("category", "hidden", "copy_from")}
            for n in from_entries(parse(text)) if n.key and isinstance(n.val, list)}


def test_no_road_demands_a_good_that_cannot_exist():
    late = {"steel", "firearms"} | set(arms.LATE_GOODS)
    ours = _demands(TEXT)
    names = arms.road_demand_names()
    assert len(names) == 8  # build and maintain, for each of the four roads
    for name in names:
        if name in ours:
            assert not set(ours[name]) & late, name
        else:  # vanilla's own demand, kept: it must never have asked for one
            vanilla = next(d for p in sorted((GAME / "in_game/common/goods_demand").glob("*.txt"))
                           for d in [_demands(p.read_text(encoding="utf-8-sig"))] if name in d)[name]
            assert not set(vanilla) & late, name


def test_the_via_publica_costs_the_same_with_period_goods():
    ours = _demands(TEXT)
    for name, vanilla in arms.vanilla_road_demands().items():
        before = {k.key: float(k.val) for k in vanilla.val if k.key != "category"}
        value = lambda d: sum(a * arms.goods_price(g) for g, a in d.items())  # noqa: E731
        assert abs(value(before) - value(ours[name])) < 1e-6, name
        assert "steel" not in ours[name] and ours[name]["stone"] > 0 and ours[name]["iron"] > 0
    assert set(arms.vanilla_road_demands()) == {"build_railroad_demand", "maintain_railroad_demand"}
