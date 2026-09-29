"""The West's locked reform burdens and separate debased coinage; Africa's grain,
Pannonia's recruits and the frontier works of Britain, the Rhine and the Danube."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b
import location_templates as lt

REFORMS = b.MOD / "in_game/common/government_reforms/tfe_late_roman_west.txt"
AUTO = b.MOD / "in_game/common/auto_modifiers/tfe_late_roman_west.txt"
FRONTIER = b.MOD / "in_game/common/building_types/tfe_frontier.txt"
EFFECTS = b.MOD / "in_game/common/scripted_effects/tfe_lands.txt"
ON_ACTION = b.MOD / "in_game/common/on_action/tfe_lands.txt"
MODS = tuple(b.MOD / f"main_menu/common/static_modifiers/{m}.txt"
             for m in ("tfe_granary_of_rome", "tfe_pannonian_recruiting_grounds", "tfe_latifundia",
                       "tfe_annona_militaris"))
ICONS = b.MOD / "main_menu/gfx/interface/icons"
ICON_MAP = b.MOD / "main_menu/common/modifier_icons/tfe_modifier_icons.txt"
COUNTRIES = b.MOD / "main_menu/setup/start/10_countries.txt"
CITIES = b.MOD / "main_menu/setup/start/07_cities_and_buildings.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_late_roman_west_l_english.yml"
SCRIPTS = (REFORMS, AUTO, FRONTIER, EFFECTS, ON_ACTION) + MODS


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def blocks(*ps):
    return {k: v for p in ps for k, v in re.findall(r"^(\w+) = \{(.*?)^\}", code(p), re.M | re.S)}


def wre():
    return re.search(r"\bWRE = \{(.*?)\n\t\t\}", COUNTRIES.read_text(encoding="utf-8-sig"), re.S).group(1)


def test_files_are_balanced_and_bom_prefixed():
    assert not (b.MOD / "in_game/common/estate_privileges/tfe_late_roman_west.txt").exists()
    for p in SCRIPTS + (LOC,):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
    for p in SCRIPTS:
        assert code(p).count("{") == code(p).count("}"), p.name


def test_everything_shown_is_localized_and_has_an_icon():
    keys = set(re.findall(r"^\s*([\w.]+):\d*\s", LOC.read_text(encoding="utf-8-sig"), re.M))
    wanted = {k for n in blocks(REFORMS, FRONTIER) for k in (n, f"{n}_desc")}
    wanted |= {f"AUTO_MODIFIER_{k}_{m}" for m in blocks(AUTO) for k in ("NAME", "DESC")}
    wanted |= {f"STATIC_MODIFIER_{k}_{m}" for m in blocks(*MODS) for k in ("NAME", "DESC")}
    assert not wanted - keys, sorted(wanted - keys)
    # the map badge of a template modifier is one of its effects' icons, so each has one effect: a bonus shows a plus,
    # a malus a minus (vanilla maps only the plus for most effects)
    icons = {k: dict(re.findall(r'(positive|negative) = "(\S+)"', body))
             for k, body in re.findall(r"^REPLACE:(\w+) = \{(.*?)^\}", code(ICON_MAP), re.M | re.S)}
    def found(path):
        return any((root / "main_menu" / path).exists() for root in (b.MOD, b.GAME))
    for p in MODS:
        effects = re.findall(r"^\t(\w+) = (-?[\d.]+)", blocks(p)[p.stem], re.M)
        assert len(effects) == 1, (p.name, effects)
        effect, value = effects[0][0], float(effects[0][1])
        side = "negative" if value < 0 else "positive"
        vanilla_plus = effect == "local_wheat_output_modifier" and side == "positive"
        assert vanilla_plus or found(icons.get(effect, {}).get(side, "missing")), (p.name, effect, side)
    for n in blocks(FRONTIER):   # a building's icon is named for it
        assert (ICONS / f"buildings/{n}.dds").exists(), n
    for n in blocks(REFORMS):
        assert (ICONS / f"government_reforms/illustrations/{n}.dds").exists(), n


def country_modifier(body):
    match = re.search(r"country_modifier = \{(.*?)^\t\}", body, re.M | re.S)
    assert match, body
    return dict(re.findall(r"^\t\t(\w+) = ([^\s#]+)", match.group(1), re.M))


def test_both_burdens_are_locked_reforms_with_their_original_effects_and_slots():
    reforms = blocks(REFORMS)
    assert set(reforms) == {"tfe_senatorial_immunities", "tfe_patrocinium", "tfe_coinage_reform"}
    expected = {
        "tfe_senatorial_immunities": {
            "global_nobles_estate_power": "0.5",
            "nobles_estate_target_satisfaction": "medium_privilege_target_satisfaction",
            "nobles_estate_max_tax": "-0.25",
            "government_reform_slots": "1",
        },
        "tfe_patrocinium": {
            "global_peasants_estate_power": "0.25",
            "global_nobles_estate_power": "0.25",
            "peasants_estate_target_satisfaction": "medium_privilege_target_satisfaction",
            "peasants_estate_levy_size": "-0.5",
            "global_manpower_modifier": "-0.25",
            "government_reform_slots": "1",
        },
    }
    for name, effects in expected.items():
        body = reforms[name]
        assert re.search(r"potential = \{\s*has_or_had_tag = WRE\s*\}", body)
        assert re.search(r"locked = \{\s*always = yes\s*\}", body), name
        assert country_modifier(body) == effects, name
        assert "on_fully_activated" not in body and "on_deactivate" not in body, name


def test_the_west_starts_with_both_burdens():
    expected = "reforms = { tfe_senatorial_immunities tfe_patrocinium }"
    govs = [line.split(" = ", 1)[1] for line in (b.TOOLS / "governments.txt").read_text(encoding="utf-8").splitlines()
            if line.startswith("WRE = reforms = ")]
    assert govs == [expected]
    assert f"\t\t\t\t{expected}" in wre().replace("\r", "")   # 10_countries is borders.py's output


def test_peraequatio_and_dilectus_are_gone_and_coinage_still_ends_debasement():
    reforms = blocks(REFORMS)
    assert "tfe_peraequatio_reform" not in reforms
    assert "tfe_dilectus_reform" not in reforms
    coin = re.search(r"NOT = \{ has_variable = (\w+) \}", blocks(AUTO)["tfe_debased_coinage"]).group(1)
    assert f"set_variable = {{ name = {coin} }}" in reforms["tfe_coinage_reform"]


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


def test_italys_remaining_wheat_yields_less_so_african_grain_sells_there():
    # graded: the dole-fed centre and south lose more than the north, whose grain went to the court and army in kind
    anc = b.load_hierarchy()
    ours = (b.MOD / "in_game/map_data/location_templates.txt").read_text(encoding="utf-8-sig")
    wheat = {l: m for l, m in re.findall(r"^(\w+) = \{ (?:modifier = (\w+) )?[^\n]*raw_material = wheat\b", ours, re.M)
             if anc[l][2] == "italy_region"}
    islands = {l for l in wheat if anc[l][3] in ("sicily_area", "sardinia_area")}
    north = {l for l in wheat if anc[l][3] in lt.ITALIA_ANNONARIA}
    south = set(wheat) - north - islands
    assert "rome" in south and "milano" in north and len(north) > 20 and south
    assert {wheat[l] for l in south} == {"tfe_latifundia"} and {wheat[l] for l in north} == {"tfe_annona_militaris"}
    assert not any(wheat[l] for l in islands)
    value = {m: float(re.search(r"local_wheat_output_modifier = (-[\d.]+)", blocks(p)[m]).group(1))
             for p in MODS for m in blocks(p) if m in ("tfe_latifundia", "tfe_annona_militaris")}
    assert value["tfe_latifundia"] < value["tfe_annona_militaris"] < 0


def test_roman_britain_mines_and_herds_rather_than_shears():
    anc = b.load_hierarchy()
    ours = (b.MOD / "in_game/map_data/location_templates.txt").read_text(encoding="utf-8-sig")
    assert not re.search(r"\b(england_wool_base|yorkshire_cloth_base)\b", ours)   # medieval: gone everywhere
    goods = dict(re.findall(r"^(\w+) = \{[^\n]*raw_material = (\w+)", ours, re.M))
    britain = {l for l in goods if anc[l][3] in ("home_counties_area", "midlands_area", "west_country_area",
                                                  "east_anglia_area", "wales_area", "northumbria_area")}
    assert {l for l in britain if goods[l] == "wool"} == {"basingstoke", "amesbury", "penllyn", "egremont", "alnwick"}
    assert not {l for l in britain if goods[l] in ("alum", "saffron", "medicaments")}
    assert {l for l in britain if goods[l] == "coal"} == {"newcastle", "hexham", "swansea"}
    for l, g in lt.BRITANNIA.items():
        assert l in britain and goods[l] == g, l


def test_roman_gaul_grows_no_silk_and_the_rhine_bounds_the_vines():
    anc = b.load_hierarchy()
    ours = (b.MOD / "in_game/map_data/location_templates.txt").read_text(encoding="utf-8-sig")
    goods = dict(re.findall(r"^(\w+) = \{[^\n]*raw_material = (\w+)", ours, re.M))
    gaul = {l for l in goods if anc[l][2] == "france_region" or l in lt.GAUL}
    assert not {l for l in gaul if goods[l] in ("silk", "saffron", "coal", "dyes")}
    beyond = set(lt.GAUL) - owned()
    assert beyond and not {l for l in beyond if goods[l] in ("wine", "olives")}
    assert goods["arras"] == "wool" and goods["mayen"] == "stone"   # the Atrebates' cloaks; Mayen's millstones
    for l, g in lt.GAUL.items():
        assert goods[l] == g, l


def test_hispania_grows_nothing_the_arabs_brought():
    anc = b.load_hierarchy()
    ours = (b.MOD / "in_game/map_data/location_templates.txt").read_text(encoding="utf-8-sig")
    goods = dict(re.findall(r"^(\w+) = \{[^\n]*raw_material = (\w+)", ours, re.M))
    hispania = {l for l in goods if anc[l][2] == "iberia_region"}
    arab = ("sugar", "rice", "cotton", "saffron", "silk", "saltpeter", "coal")
    assert not {l for l in hispania if goods[l] in arab}
    assert len({l for l in hispania if goods[l] == "wool"}) <= 10   # the Mesta's flocks were medieval
    assert goods["almaden"] == "mercury" and "almaden_base" in ours   # Sisapo's cinnabar (Pliny)
    assert "toledo_weaponry_base" not in ours
    for l, g in lt.HISPANIA.items():
        assert goods[l] == g, l


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
        assert "is_indestructible = yes" in body, name   # so never lost either


def test_every_location_with_our_modifier_tells_its_story():
    # the goods marker's tooltip shows the location's own flavour text (<location>_desc) under the modifier; vanilla's
    # 1337 texts for Rome, Carthage and the Po towns are replaced, so the file lives in localization/english/replace/
    flavor = b.MOD / "main_menu/localization/english/replace/tfe_location_flavor_l_english.yml"
    assert flavor.read_bytes().startswith(b"\xef\xbb\xbf")
    assert flavor.read_text(encoding="utf-8-sig") == lt.flavor(), "rerun tools/location_templates.py"
    ours = (b.MOD / "in_game/map_data/location_templates.txt").read_text(encoding="utf-8-sig")
    tagged = set(re.findall(r"^(\w+) = \{ modifier = tfe_\w+ ", ours, re.M))
    keys = dict(re.findall(r'^ (\w+)_desc: "(.+)"$', flavor.read_text(encoding="utf-8-sig"), re.M))
    assert set(keys) == tagged, sorted(set(keys) ^ tagged)
    assert "Carthage" in keys["tunis"] and "Papacy" not in keys["rome"]


def test_the_rest_of_the_west_loses_what_came_after_rome():
    anc = b.load_hierarchy()
    ours = (b.MOD / "in_game/map_data/location_templates.txt").read_text(encoding="utf-8-sig")
    goods = dict(re.findall(r"^(\w+) = \{[^\n]*raw_material = (\w+)", ours, re.M))
    regions = ("italy_region", "maghreb_region", "south_german_region", "ireland_region")
    later = ("sugar", "rice", "cotton", "saffron", "silk", "saltpeter", "coal")
    assert not {l for l in goods if anc[l][2] in regions and goods[l] in later}
    for m in ("milan_weaponry_base", "tuscany_fine_cloth_base", "venice_glass_base", "kutna_hora_silver_mines_base",
              "sicily_sulfur_mines"):
        assert m not in ours, m
    assert goods["piombino"] == "iron" and goods["friesach"] == "iron"   # Elban iron at Populonia, ferrum Noricum
    for l, g in (lt.ITALIA | lt.AFRICA | lt.RAETIA_NORICUM | lt.CALEDONIA_HIBERNIA).items():
        assert goods[l] == g, l
