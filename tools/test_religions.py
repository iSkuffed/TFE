"""395 religions: one Nicene church (vanilla orthodox), Arians and Donatists, the old gods, and a rule table for every pop."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

RELIGIONS = b.MOD / "in_game/common/religions/tfe_religions.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_religions_l_english.yml"
REPLACE = b.MOD / "main_menu/localization/english/replace/tfe_religions_replace_l_english.yml"
RULES = b.TOOLS / "religions.txt"
NEW = {"arianism", "donatism", "celtic_paganism", "slavic_paganism", "arabian_paganism", "religio_romana", "priscillianism",
       "montanism", "messalianism", "nuragic_religion", "basque_paganism", "zalmoxism", "illyrian_paganism", "armazi_religion"}
# what may live in the core in 395: nothing born later (Islam, Druze, the medieval heresies), no Latin papacy
OF_395 = NEW | {"orthodox", "nestorianism", "hellenism_religion", "norse", "tengri", "alan_paganism", "romuva",
                "muinaisusko", "votian_religion", "sapmi_shamanism", "mari_paganism", "erzya_religion",
                 "moksha_religion", "komi_paganism", "udmurt_paganism", "obian_paganism", "samoyedic_paganism",
                 "khabzeism", "vainakh_paganism",
                "lezgin_paganism", "godala_religion", "judaism", "samaritanism", "mandeaism", "manichaeism",
                "zoroastrian", "mahayana", "hindu"}


def blocks(text):
    return {m.group(1): m.group(2) for m in re.finditer(r"^(?:REPLACE:)?(\w+)\s*=\s*\{(.*?)^\}", text, re.M | re.S)}


def pops():
    text = (b.MOD / "main_menu/setup/start/06_pops.txt").read_text(encoding="utf-8")
    return {loc: re.findall(r"type = (\w+)\s+size = [\d.]+\s+culture = (\w+)\s+religion = (\w+)", body)
            for loc, body in re.findall(r"^(\w+) = \{(.*?)^\}", text, re.M | re.S)}


def majority(loc):
    # the faith with the most people, which is what the map shows
    text = (b.MOD / "main_menu/setup/start/06_pops.txt").read_text(encoding="utf-8")
    body = re.search(rf"^{loc} = \{{(.*?)^\}}", text, re.M | re.S).group(1)
    size = {}
    for s, r in re.findall(r"size = ([\d.]+)\s+culture = \w+\s+religion = (\w+)", body):
        size[r] = size.get(r, 0) + float(s)
    return max(size, key=size.get)


def test_new_religions_are_defined_with_names_and_icons():
    assert RELIGIONS.read_bytes().startswith(b"\xef\xbb\xbf")
    text = RELIGIONS.read_text(encoding="utf-8-sig")
    assert text.count("{") == text.count("}")
    defs = blocks(text)
    assert NEW <= set(defs)
    loc = LOC.read_text(encoding="utf-8-sig")
    for r in NEW:
        assert re.search(r"group = (christian|folk_european_group)\b", defs[r]), r
        for key in (r, f"{r}_ADJ", f"{r}_desc"):
            assert re.search(rf'^ {key}: ".+"$', loc, re.M), key
        assert (b.MOD / f"main_menu/gfx/interface/icons/religion/{r}.dds").exists(), r
    assert r in b.known_religions()


def test_hellenism_is_switched_on_for_395():
    body = blocks(RELIGIONS.read_text(encoding="utf-8-sig"))["hellenism_religion"]
    assert "REPLACE:hellenism_religion" in RELIGIONS.read_text(encoding="utf-8-sig")
    assert "enable" not in body and "group = folk_european_group" in body


def test_the_church_is_one_and_nicene():
    loc = REPLACE.read_text(encoding="utf-8-sig")
    for key, name in (("orthodox", "Nicene Christianity"), ("orthodox_ADJ", "Nicene"), ("norse", "Germanic Paganism"),
                      ("nestorianism", "Church of the East")):
        assert re.search(rf'^ {key}: "{name}"$', loc, re.M), key
    tags = b.load_tags(b.TOOLS / "tags.txt")
    assert tags["WRE"]["religion"] == tags["EAR"]["religion"] == "orthodox"
    for t in ("VIS", "GEP", "HAS", "RUG"):
        assert tags[t]["religion"] == "arianism", t
    assert "catholic" not in {d["religion"] for d in tags.values()}


def test_rules_can_set_religion_by_culture():
    anc = {"here": ("europe", "western_europe", "italy_region", "lazio_area", "roma_province")}
    text = "here = {\n\tdefine_pop = { type = peasants size = 1 culture = roman_culture religion = catholic }\n" \
           "\tdefine_pop = { type = nobles size = 1 culture = roman_culture religion = catholic }\n" \
           "\tdefine_pop = { type = burghers size = 1 culture = mizrahi religion = catholic }\n}\n"
    rules = [("*", "mizrahi", "judaism"), ("here", "nobles:*", "hellenism_religion"), ("italy_region", "*", "orthodox")]
    out = b.pop_cultures(text, {}, anc, rules, field="religion")
    assert re.findall(r"religion = (\w+)", out) == ["orthodox", "hellenism_religion", "judaism"]
    assert out.count("culture = roman_culture") == 2


def test_a_rule_can_split_a_pop_between_faiths():
    anc = {"here": ("europe", "western_europe", "italy_region", "lazio_area", "roma_province")}
    text = "here = {\n\tdefine_pop = { type = peasants size = 10 culture = roman_culture religion = catholic }\n}\n"
    rules = [("here", "*", "religio_romana 60 orthodox 30 manichaeism 10")]
    out = b.pop_cultures(text, {}, anc, rules, field="religion")
    got = re.findall(r"size = ([\d.]+) culture = roman_culture religion = (\w+)", out)
    assert got == [("6.000", "religio_romana"), ("3.000", "orthodox"), ("1.000", "manichaeism")]
    assert out.count("type = peasants") == 3 and out.count("\n\tdefine_pop") == 3


def test_every_rule_target_exists():
    targets = {r for _, _, to in b.load_culture_rules(RULES, None, None) for r, _ in b.mix(to)}
    assert targets and targets <= b.known_religions(), targets - b.known_religions()


def test_the_core_keeps_only_religions_of_395():
    anc = b.load_hierarchy()
    left = {}
    for loc, ps in pops().items():
        if anc[loc][2] in (b.CULTURE_REGIONS | {"ural_region"}):
            for kind, culture, religion in ps:
                if religion not in OF_395:
                    left.setdefault((culture, religion), loc)
    assert not left, sorted(left.items())[:20]


@pytest.mark.parametrize("loc, religion", [
    ("constantinople", "orthodox"), ("antioch", "orthodox"), ("milano", "orthodox"), ("alexandria", "orthodox"),
    ("harran", "hellenism_religion"), ("baalbek", "hellenism_religion"), ("aswan", "hellenism_religion"),
    ("jerusalem", "orthodox"), ("safed", "judaism"), ("nablus", "samaritanism"),
    ("cashel", "celtic_paganism"), ("uppsala", "norse"), ("tarnovo", "arianism"),
    ("baghdad", "nestorianism"), ("toledo", "orthodox"), ("isfahan", "zoroastrian"),
    # the 395 map after the reference: the West's pagani, the East's Hellenes and the sects between
    ("narbonne", "manichaeism"), ("lugo", "priscillianism"), ("avila", "priscillianism"), ("sassari", "nuragic_religion"),
    ("kutahya", "montanism"), ("ankara", "celtic_paganism"), ("homs", "hellenism_religion"), ("karak", "arabian_paganism"),
    ("tbilisi", "armazi_religion"), ("mystras", "hellenism_religion"), ("granada", "manichaeism"),
    ("zaragoza", "religio_romana"), ("rennes", "celtic_paganism")])
def test_spot_checks(loc, religion):
    assert majority(loc) == religion, (loc, pops()[loc])


def test_mixed_places():
    p = pops()
    assert ("nobles", "roman_culture", "religio_romana") in {x for x in p["rome"]}   # Symmachus' senate
    assert any(r == "orthodox" for _, _, r in p["rome"])
    assert any(r == "donatism" for _, c, r in p["constantine_ALG"])                       # Numidia
    assert any(r == "nestorianism" for _, c, r in p["mosul"] if c == "assyrian")   # the Persian church
    himyar = b.owned_by_tag(b.compute()["owner"])["HIM"]
    assert any(r == "judaism" for l in himyar for k, _, r in p.get(l, []) if k in ("nobles", "clergy"))   # Himyar's court
    assert any(r == "celtic_paganism" for k, c, r in p["london"] if k == "peasants")
    assert {r for ps in p.values() for _, c, r in ps if c == "venedi"} == {"slavic_paganism"}
    assert any(r == "arabian_paganism" for _, c, r in p["mecca"])
    # minorities: most Roman places hold more than one faith
    anc = b.load_hierarchy()
    roman = [l for l, ps in p.items() if anc[l][2] in ("italy_region", "france_region", "iberia_region", "anatolia_region")]
    mixed = [l for l in roman if len({r for _, _, r in p[l]}) > 1]
    assert len(mixed) > 0.8 * len(roman), (len(mixed), len(roman))


def test_ural_and_carpathian_religions_match_the_395_rules():
    for loc, religion in (("ufa", "obian_paganism"), ("sarapul", "udmurt_paganism"),
                          ("cherdyn", "komi_paganism"), ("laish", "tengri"),
                          ("mukachevo", "zalmoxism")):
        assert majority(loc) == religion, (loc, pops()[loc])


def test_late_faiths_fall_to_the_neighbours():
    # culture in the region first, then the area, then the region
    anc = {"a": ("x", "y", "r1", "area1", "p1"), "b": ("x", "y", "r1", "area2", "p2"), "c": ("x", "y", "r1", "area2", "p3")}
    text = ("a = {\n\tdefine_pop = { type = peasants size = 1 culture = cx religion = sunni }\n}\n"
            "b = {\n\tdefine_pop = { type = peasants size = 1 culture = cx religion = hindu }\n"
            "\tdefine_pop = { type = peasants size = 1 culture = cy religion = sunni }\n}\n"
            "c = {\n\tdefine_pop = { type = peasants size = 5 culture = cz religion = bantu_religion }\n}\n")
    out, lost = b.purge_late_faiths(text, anc)
    assert re.findall(r"religion = (\w+)", out) == ["hindu", "hindu", "bantu_religion", "bantu_religion"]
    assert not lost
    out, lost = b.purge_late_faiths("a = {\n\tdefine_pop = { type = peasants size = 1 culture = cx religion = sunni }\n}\n", anc)
    assert lost == ["a"]


def test_no_faith_born_after_395_anywhere():
    late = {(loc, r) for loc, ps in pops().items() for _, _, r in ps if r in b.LATE_FAITHS}
    assert not late, sorted(late)[:20]
    assert {"sunni", "shia", "catholic", "miaphysite", "tibetan_buddhism"} <= b.LATE_FAITHS
    assert not {d["religion"] for d in b.load_tags(b.TOOLS / "tags.txt").values()} & b.LATE_FAITHS
    chars = (b.MOD / "main_menu/setup/start/05_characters.txt").read_text(encoding="utf-8-sig")
    assert not set(re.findall(r"religion = (\w+)", chars)) & b.LATE_FAITHS


def test_kush_and_aksum():
    assert "kushite_religion" in blocks(RELIGIONS.read_text(encoding="utf-8-sig"))
    assert re.search(r'^ kushite_religion: "Kushite Religion"$', LOC.read_text(encoding="utf-8-sig"), re.M)
    assert (b.MOD / "main_menu/gfx/interface/icons/religion/kushite_religion.dds").exists()
    tags = b.load_tags(b.TOOLS / "tags.txt")
    assert tags["NOB"]["religion"] == tags["BMY"]["religion"] == "kushite_religion"
    assert tags["AXU"]["religion"] == "orthodox"
    own = b.owned_by_tag(b.compute()["owner"])
    p = pops()
    nubia = [r for l in own["NOB"] for _, _, r in p.get(l, [])]
    assert max(set(nubia), key=nubia.count) == "kushite_religion"
    aksum = [(k, r) for l in own["AXU"] for k, _, r in p.get(l, [])]
    assert {r for k, r in aksum if k == "nobles"} == {"orthodox"}
    assert "arabian_paganism" in {r for k, r in aksum if k == "peasants"}   # Almaqah and Mahrem
    assert {r for _, _, r in p["lhasa"]} == {"bon"} if "lhasa" in p else True
