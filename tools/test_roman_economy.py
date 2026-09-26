"""The empires' start economy: vanilla's 1337 castles, pops and missing governors left the West losing ~470 gold a month."""
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

START = b.MOD / "main_menu/setup/start"
CITIES = START / "07_cities_and_buildings.txt"
TWINS = b.MOD / "in_game/common/town_setups/tfe_unfortified.txt"
VANILLA_SETUPS = b.GAME / "in_game/common/town_setups/00_default.txt"
FORT_TYPES = {"stockade", "castle", "bastion", "star_fort", "fortress", "city_walls", "coastal_fort"}


def owners():
    text = (START / "10_countries.txt").read_text(encoding="utf-8-sig")
    own, caps = {}, {}
    for t in b.ROMAN_EMPIRES:
        block = re.search(rf"\b{t} = \{{(.*?)\n\t\t\}}", text, re.S).group(1)
        for l in re.findall(r"\w+", re.search(r"own_control_core = \{(.*?)\}", block, re.S).group(1)):
            own[l] = t
        caps[t] = re.search(r"capital = (\w+)", block).group(1)
    return own, caps


def setups(p):
    # a preset may copy_from another and add levels on top ("base 3 -> 5" beside "= 2" in vanilla's comments)
    raw = {m.group(1): re.sub(r"#[^\n]*", "", m.group(2))
           for m in re.finditer(r"^(\w+)\s*=\s*\{(.*?)^\}", p.read_text(encoding="utf-8-sig"), re.M | re.S)}
    def flat(name):
        body = raw[name]
        base = re.search(r"copy_from = (\w+)", body)
        out = dict(flat(base.group(1))) if base else {}
        for k, v in re.findall(r"(\w+) = (\d+)", body):
            out[k] = out.get(k, 0) + int(v)
        return out
    return {n: flat(n) for n in raw}


def towns():
    text = CITIES.read_text(encoding="utf-8-sig")
    return {l: (r, s) for l, r, s in re.findall(r"^\s*(\w+) = \{[^}]*rank = (\w+)[^}]*town_setup\s*=\s*(\w+)", text, re.M)}


def buildings(kind):
    text = CITIES.read_text(encoding="utf-8-sig")
    return re.findall(rf"^\s*{kind}\s*= \{{ tag = (\w+) level = 1 location = (\w+) \}}", text, re.M)


def test_roman_towns_get_no_castles_from_their_town_presets():
    own, _ = owners()
    known = setups(VANILLA_SETUPS) | setups(TWINS)
    roman = [(l, s) for l, (r, s) in towns().items() if l in own]
    assert len(roman) > 300
    fortified = [(l, s) for l, s in roman if FORT_TYPES & set(known[s])]
    assert not fortified, fortified[:5]


def test_unfortified_presets_are_vanilla_minus_the_forts():
    assert TWINS.read_bytes().startswith(b"\xef\xbb\xbf")
    vanilla, twins = setups(VANILLA_SETUPS), setups(TWINS)
    assert twins
    for name, twin in twins.items():
        base = vanilla[name.removeprefix("tfe_unfortified_")]
        assert twin == {k: v for k, v in base.items() if k not in FORT_TYPES}, name


def test_the_empires_keep_a_few_frontier_fortresses():
    own, _ = owners()
    forts = buildings("castle")
    per = defaultdict(int)
    for tag, loc in forts:
        assert own.get(loc) == tag, (tag, loc)
        per[tag] += 1
    # vanilla presets gave the West 175 castles and the East 33
    assert 8 <= per["WRE"] <= 15 and 6 <= per["EAR"] <= 12, dict(per)


def test_diocesan_seats_start_with_local_governors():
    own, caps = owners()
    ranks = dict(re.findall(r"^\s*(\w+) = \{[^}]*rank = (\w+)", CITIES.read_text(encoding="utf-8-sig"), re.M))
    govs = buildings("local_governor")
    per = defaultdict(int)
    for tag, loc in govs:
        # the building needs a city of the owner's that is not its capital
        assert own.get(loc) == tag and ranks.get(loc) in ("city", "megalopolis") and loc != caps[tag], (tag, loc)
        per[tag] += 1
    assert per["WRE"] >= 5 and per["EAR"] >= 4, dict(per)


def pops_by_location(text):
    return {m.group(1): sum(float(x) for x in re.findall(r"size = ([\d.]+)", m.group(2)))
            for m in re.finditer(r"^(\w+) = \{(.*?)^\}", text, re.M | re.S)}


def test_roman_regions_have_395_populations():
    own, _ = owners()
    anc = b.load_hierarchy()
    ours = pops_by_location((START / "06_pops.txt").read_text(encoding="utf-8"))
    vanilla = pops_by_location((b.GAME / "main_menu/setup/start/06_pops.txt").read_text(encoding="utf-8-sig"))
    total = defaultdict(float)
    for l, t in own.items():
        total[t, anc[l][2]] += ours.get(l, 0)
    for key, millions in b.ROMAN_POPULATION_M.items():
        assert abs(total[key] / 1000 - millions) <= 0.01 * millions, (key, total[key] / 1000)
    assert set(total) == set(b.ROMAN_POPULATION_M), set(total) ^ set(b.ROMAN_POPULATION_M)
    # the rest of the world keeps vanilla's numbers (Society of Pops lands are thinned separately)
    assert ours["paris"] != vanilla["paris"] and ours["baghdad"] == vanilla["baghdad"]
