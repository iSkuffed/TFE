"""395 cultures: twelve new ones built from vanilla parts, and a rule table that remaps every 1337 pop of the core."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

CULTURES = b.MOD / "in_game/common/cultures/tfe_cultures.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_cultures_l_english.yml"
REPLACE = b.MOD / "main_menu/localization/english/replace/tfe_cultures_replace_l_english.yml"
NEW = {"gallo_roman", "hispano_roman", "afro_roman", "briton", "pictish", "frankish", "alamannic", "suebian",
       "vandal", "tfe_burgundian", "hunnic", "venedi", "romano_british", "thracian", "illyro_roman", "thraco_roman", "dacian",
       "taifal", "roxolan", "iazyges", "phrygian", "galatian", "arranian", "caspian", "nabataean", "assyrian", "chaldean",
       "elymaean", "parthian", "chorasmian"}
GROUPS = b.MOD / "in_game/common/culture_groups/tfe_culture_groups.txt"


def vanilla_text(folder):
    return "\n".join(p.read_text(encoding="utf-8-sig") for p in (b.GAME / "in_game/common" / folder).glob("*.txt"))


def blocks(text):
    return {m.group(1): m.group(2) for m in re.finditer(r"^(\w+)\s*=\s*\{(.*?)^\}", text, re.M | re.S)}


def test_new_cultures_are_defined_from_vanilla_parts():
    assert CULTURES.read_bytes().startswith(b"\xef\xbb\xbf")
    text = CULTURES.read_text(encoding="utf-8-sig")
    assert text.count("{") == text.count("}")
    defs = blocks(text)
    assert set(defs) == NEW
    languages = vanilla_text("languages")
    groups = set(blocks(vanilla_text("culture_groups"))) | set(blocks(GROUPS.read_text(encoding="utf-8-sig")))
    for name, body in defs.items():
        lang = re.search(r"language = (\w+)", body).group(1)
        assert re.search(rf"^\s*{lang}\s*=\s*\{{", languages, re.M), (name, lang)
        mine = re.findall(r"\w+", re.search(r"culture_groups = \{(.*?)\}", body, re.S).group(1))
        assert mine and set(mine) <= groups, (name, mine)
        assert re.search(r"color = rgb \{ \d+ \d+ \d+ \}", body), name


def test_cultures_are_localized_and_roman_is_roman():
    for p in (LOC, REPLACE):
        assert p.read_bytes().startswith(b"\xef\xbb\xbfl_english:")
    keys = dict(re.findall(r'^ (\w+): "(.*)"', LOC.read_text(encoding="utf-8-sig"), re.M))
    assert NEW <= set(keys)
    assert re.search(r'^ roman_culture: "Roman"$', REPLACE.read_text(encoding="utf-8-sig"), re.M)


RULES = b.TOOLS / "cultures.txt"
POPS = b.MOD / "main_menu/setup/start/06_pops.txt"


def pops_cultures():
    return {m.group(1): re.findall(r"culture = (\w+)", m.group(2))
            for m in re.finditer(r"^(\w+) = \{(.*?)^\}", POPS.read_text(encoding="utf-8"), re.M | re.S)}


def top(loc):
    # the culture with the most people (pops split by faith would skew a count of entries)
    body = re.search(rf"^{loc} = \{{(.*?)^\}}", POPS.read_text(encoding="utf-8"), re.M | re.S).group(1)
    size = {}
    for s, c in re.findall(r"size = ([\d.]+)\s+culture = (\w+)", body):
        size[c] = size.get(c, 0) + float(s)
    return max(size, key=size.get)


def test_rules_parse_and_first_match_wins():
    anc = {"here": ("europe", "western_europe", "iberia_region", "castile_area", "toledo_province")}
    text = "here = {\n\tdefine_pop = { type = peasants size = 1 culture = castilian religion = catholic }\n" \
           "\tdefine_pop = { type = nobles size = 1 culture = basque religion = catholic }\n}\n"
    rules = [("VIS", "*", "gothic_culture"), ("iberia_region", "basque", "basque"),
             ("iberia_region", "*", "hispano_roman")]
    out = b.pop_cultures(text, {}, anc, rules)
    assert re.findall(r"culture = (\w+)", out) == ["hispano_roman", "basque"]
    out = b.pop_cultures(text, {"here": "VIS"}, anc, rules)
    assert re.findall(r"culture = (\w+)", out) == ["gothic_culture", "gothic_culture"]


def test_unknown_scopes_and_cultures_are_refused(tmp_path):
    for bad in ("nowhere_region | * | roman_culture", "iberia_region | * | klingon"):
        p = tmp_path / "rules.txt"
        p.write_text(bad + "\n", encoding="utf-8")
        try:
            b.load_culture_rules(p, {"iberia_region"}, {"roman_culture"})
        except ValueError:
            continue
        raise AssertionError(bad)


def test_every_rule_target_exists():
    known = set(blocks(vanilla_text("cultures"))) | NEW
    targets = {c for _, _, to in b.load_culture_rules(RULES, None, None) for c, _ in b.mix(to)}
    assert targets and targets <= known, targets - known


def test_the_core_has_no_1337_cultures_left():
    anc = b.load_hierarchy()
    targets = {c for _, _, to in b.load_culture_rules(RULES, None, None) for c, _ in b.mix(to)}
    left = {}
    for loc, cults in pops_cultures().items():
        if anc[loc][2] in b.CULTURE_REGIONS:
            for c in set(cults) - targets:
                left.setdefault(c, loc)
    assert not left, sorted(left.items())[:20]


def test_spot_checks():
    own = {l: t for t, locs in b.owned_by_tag(b.compute()["owner"]).items() for l in locs}
    by = pops_cultures()
    def only(loc, culture):   # the dominant people; minorities (Jews, Griko...) may stay
        assert top(loc) == culture, (loc, by[loc])
    for loc, culture in (("toledo", "hispano_roman"), ("konya", "greek_culture"),
                         ("tunis", "afro_roman"), ("aleppo", "syriac_culture"), ("rome", "roman_culture"),
                         ("paris", "gallo_roman"), ("alexandria", "greek_culture")):
        only(loc, culture)
    for tag, culture in (("FRK", "frankish"), ("HNS", "hunnic")):
        loc = next(l for l, t in own.items() if t == tag and l in by)
        only(loc, culture)


STAND_INS = {"lower_saxon", "swabian", "high_alemannic", "burgundian", "bashkir", "welsh", "scottish",
             "eastern_pomeranian", "prussian", "turkmen_culture"}   # 1337 cultures once borrowed for 395 peoples


def test_tags_and_characters_use_395_cultures():
    known = set(blocks(vanilla_text("cultures"))) | NEW
    tags = b.load_tags()
    for t, d in tags.items():
        assert d["culture"] in known and d["culture"] not in STAND_INS, (t, d["culture"])
    chars = (b.MOD / "main_menu/setup/start/05_characters.txt").read_text(encoding="utf-8-sig")
    used = set(re.findall(r"culture = (\w+)", chars))
    assert used <= known and not used & STAND_INS, used & STAND_INS


def test_the_empires_accept_their_provincials():
    text = (b.MOD / "main_menu/setup/start/10_countries.txt").read_text(encoding="utf-8")
    for tag, people in b.ACCEPTED_CULTURES.items():
        people = set(people)
        block = text[text.index(f"\t\t{tag} = {{"):].split("\n\t\t}\n")[0]
        accepted = re.search(r"accepted_cultures = \{([^}]*)\}", block)
        assert accepted and set(accepted.group(1).split()) == people, tag
        # after the include, which may bring its own
        assert block.index("accepted_cultures") > block.index("include =")


def test_roman_is_a_living_culture():
    # vanilla ships roman_culture dormant (active = no) for the Latin revival; in 395 it has 10M pops
    text = CULTURES.read_text(encoding="utf-8-sig")
    body = re.search(r"^REPLACE:roman_culture = \{(.*?)^\}", text, re.M | re.S).group(1)
    assert re.search(r"^\tactive = yes$", body, re.M)
    assert "color = map_ROM" in body and "language = roman_dialect" in body
    for c in ("greek_culture", "gallo_roman", "hispano_roman", "afro_roman"):
        assert re.search(rf"{c} = kindred", body), c


def test_review_spot_checks():
    # Berbers inland keep Amazigh cultures even inside Roman areas; Roman ports stay Afro-Roman;
    # Khwarazm is Iranian in 395 (vanilla khorezmian_culture is Turkic); Karelians are no Swedes
    by = pops_cultures()
    assert top("kuku") == "kabyle"
    assert top("nalut") == "eastern_amazigh"
    for loc in ("tangier", "ceuta"):
        assert top(loc) == "afro_roman", loc
    for loc in ("khiva", "kath", "urgench"):
        assert top(loc) == "chorasmian", loc
    assert top("korela") == "karelian"
    assert "swedish" not in {c for l, a in b.load_hierarchy().items() if len(a) > 3 and a[3] in ("karelia_area", "kola_area")
                             for c in by.get(l, ())}


def test_the_illyrian_highlands():
    # the coast and the Danube were Latin by 395, the mountains of Dardania, Praevalitana and the Dalmatian
    # hinterland still Illyrian; vanilla has no Illyrian culture, so albanian (their heirs) carries the name
    by = pops_cultures()
    for loc in ("peja", "podgorica", "mostar", "pljevlja", "brskovo"):
        assert top(loc) == "albanian", loc
    for loc in ("dubrovnik", "pola", "sabac"):
        assert top(loc) == "illyro_roman", loc
    assert top("belgrad") == "thraco_roman"
    assert re.search(r'^ albanian: "Illyrian"$', REPLACE.read_text(encoding="utf-8-sig"), re.M)


def effective_groups():
    # REPLACE: blocks in tfe_cultures.txt win over vanilla and TFE definitions
    text = CULTURES.read_text(encoding="utf-8-sig")
    defs = {**blocks(vanilla_text("cultures")), **blocks(text),
            **{m.group(1): m.group(2) for m in re.finditer(r"^REPLACE:(\w+) = \{(.*?)^\}", text, re.M | re.S)}}
    return {k: set(re.findall(r"\w+", re.search(r"culture_groups = \{(.*?)\}", v, re.S).group(1)))
            for k, v in defs.items() if "culture_groups" in v}


def test_the_roman_and_greek_groups():
    # vanilla greek_group is shown as "Roman": the Latin provincials join it; Greek-speakers get their own group,
    # tfe_hellenic_group ("Greek"); Greek proper sits in both. The Goths of 395 are no Romans.
    assert GROUPS.read_bytes().startswith(b"\xef\xbb\xbf")
    assert "tfe_hellenic_group" in blocks(GROUPS.read_text(encoding="utf-8-sig"))
    loc = LOC.read_text(encoding="utf-8-sig")
    assert re.search(r'^ tfe_hellenic_group: "Greek"$', loc, re.M) and re.search(r'^ romano_british: "Romano-British"$', loc, re.M)
    g = effective_groups()
    for c in ("roman_culture", "greek_culture", "gallo_roman", "hispano_roman", "afro_roman", "romano_british"):
        assert "greek_group" in g[c], c
    for c in ("greek_culture", "cappadocian_greek_culture", "pontic_greek_culture", "griko_culture", "romanyoti", "thracian"):
        assert "tfe_hellenic_group" in g[c], c
    for c in ("cappadocian_greek_culture", "pontic_greek_culture", "griko_culture", "romanyoti", "gothic_culture"):
        assert "greek_group" not in g[c], c
    assert "german_group" in g["gothic_culture"] and "jewish_group" in g["romanyoti"]


def test_replaced_cultures_keep_vanilla_looks():
    text = CULTURES.read_text(encoding="utf-8-sig")
    vanilla = blocks(vanilla_text("cultures"))
    for name, body in re.findall(r"^REPLACE:(\w+) = \{(.*?)^\}", text, re.M | re.S):
        for key in ("language", "color"):
            assert re.search(rf"{key} = (\S+)", body).group(1) == re.search(rf"{key} = (\S+)", vanilla[name]).group(1), (name, key)
        tags = lambda s: set(re.search(r"tags = \{(.*?)\}", s).group(1).split())
        assert tags(body) == tags(vanilla[name]), name


def test_rules_can_pick_a_social_class():
    anc = {"here": ("asia", "near_east", "egypt_region", "lower_egypt_area", "cairo_province")}
    text = "here = {\n\tdefine_pop = { type = peasants size = 1 culture = coptic_culture religion = x }\n" \
           "\tdefine_pop = { type = burghers size = 1 culture = coptic_culture religion = x }\n}\n"
    rules = [("egypt_region", "burghers:*", "greek_culture"), ("egypt_region", "*", "coptic_culture")]
    assert re.findall(r"culture = (\w+)", b.pop_cultures(text, {}, anc, rules)) == ["coptic_culture", "greek_culture"]


def test_greeks_of_the_east():
    by = pops_cultures()
    for loc in ("antioch", "latakia", "hama", "sidon", "acre", "jaffa", "gaza", "majdal", "jerusalem", "irbid", "amman",
                "bosra", "tinnis", "faiyum", "el_bahnasa", "ashmunayn", "akhmim"):
        assert top(loc) == "greek_culture", loc
    assert top("beirut") == "roman_culture"                      # Berytus, Latin colony and law school
    assert top("safed") == "mizrahi"                             # Galilee of the Patriarchs
    assert top("nablus") == "samaritan_culture"
    assert "mizrahi" in by["alexandria"]
    text = POPS.read_text(encoding="utf-8")
    anc = b.load_hierarchy()
    for m in re.finditer(r"^(\w+) = \{(.*?)^\}", text, re.M | re.S):
        if anc[m.group(1)][3] in ("levant_area", "lower_egypt_area", "upper_egypt_area"):
            for c in re.findall(r"type = (?:burghers|nobles)\s+size = [\d.]+\s+culture = (\w+)", m.group(2)):
                assert c in ("greek_culture", "roman_culture", "mizrahi", "samaritan_culture", "armenian_culture",
                             "bedouin_culture"), (m.group(1), c)


def test_balkans_and_britain():
    by = pops_cultures()
    for loc in ("skopje", "shtip"):
        assert top(loc) == "thraco_roman", loc
    assert top("durres") == "illyro_roman"
    for loc in ("smolyan", "bansko", "melnik"):
        assert top(loc) == "thracian", loc
    for loc in ("london", "colchester", "st_albans", "cirencester", "bath", "leicester", "york"):
        assert top(loc) == "romano_british", loc
    for loc in ("exeter", "truro", "cardiff", "carlisle", "leeds"):
        assert top(loc) == "briton", loc
    for loc in ("pembroke", "carmarthen", "anglesey", "carnarvon"):
        assert top(loc) == "irish", loc
    text = (b.MOD / "main_menu/setup/start/10_countries.txt").read_text(encoding="utf-8")
    for tag in ("WRE", "EAR"):
        block = text[text.index(f"\t\t{tag} = {{"):].split("\n\t\t}\n")[0]
        accepted = set(re.search(r"accepted_cultures = \{([^}]*)\}", block).group(1).split())
        assert "albanian" in accepted, tag
    assert "romano_british" in set(b.ACCEPTED_CULTURES["WRE"])


def test_the_aramaic_group():
    # the Aramaic-speakers of 395 are no Arabs: Syriac, Mandaean, Samaritan, and the Jews of Galilee and Babylon
    assert "tfe_aramaic_group" in blocks(GROUPS.read_text(encoding="utf-8-sig"))
    assert re.search(r'^ tfe_aramaic_group: "Aramaic"$', LOC.read_text(encoding="utf-8-sig"), re.M)
    g = effective_groups()
    for c in ("syriac_culture", "mandean_culture", "samaritan_culture", "mizrahi"):
        assert "tfe_aramaic_group" in g[c] and "arabic_group" not in g[c], c
    assert "jewish_group" in g["mizrahi"]


def test_greeks_and_romans_are_kindred():
    # every Latin and Greek people of the Empire holds every other one kindred
    text = CULTURES.read_text(encoding="utf-8-sig")
    defs = {m.group(1): m.group(2) for m in re.finditer(r"^(?:REPLACE:)?(\w+) = \{(.*?)^\}", text, re.M | re.S)}
    both = ["roman_culture", "gallo_roman", "hispano_roman", "afro_roman", "romano_british", "illyro_roman", "thraco_roman",
            "greek_culture", "cappadocian_greek_culture", "pontic_greek_culture", "griko_culture", "phrygian", "galatian"]
    for c in both:
        opinions = dict(re.findall(r"(\w+) = (\w+)", re.search(r"opinions = \{(.*?)\}", defs[c], re.S).group(1)))
        for other in both:
            assert other == c or opinions.get(other) == "kindred", (c, other)
