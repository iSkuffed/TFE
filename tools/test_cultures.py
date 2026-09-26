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
       "vandal", "tfe_burgundian", "hunnic", "venedi"}


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
    groups = set(blocks(vanilla_text("culture_groups")))
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
    targets = {to for _, _, to in b.load_culture_rules(RULES, None, None)}
    assert targets and targets <= known, targets - known


def test_the_core_has_no_1337_cultures_left():
    anc = b.load_hierarchy()
    targets = {to for _, _, to in b.load_culture_rules(RULES, None, None)}
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
        assert max(set(by[loc]), key=by[loc].count) == culture, (loc, by[loc])
    for loc, culture in (("toledo", "hispano_roman"), ("konya", "cappadocian_greek_culture"),
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
    for tag, people in (("WRE", {"gallo_roman", "hispano_roman", "afro_roman", "briton"}),
                        ("EAR", {"roman_culture", "syriac_culture", "coptic_culture", "armenian_culture",
                                 "cappadocian_greek_culture", "pontic_greek_culture"})):
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
    def top(loc):
        return max(set(by[loc]), key=by[loc].count)
    assert top("kuku") == "kabyle"
    assert top("nalut") == "eastern_amazigh"
    for loc in ("tangier", "ceuta"):
        assert top(loc) == "afro_roman", loc
    for loc in ("khiva", "kath", "urgench"):
        assert top(loc) == "khorasani_culture", loc
    assert top("korela") == "karelian"
    assert "swedish" not in {c for l, a in b.load_hierarchy().items() if len(a) > 3 and a[3] in ("karelia_area", "kola_area")
                             for c in by.get(l, ())}


def test_the_illyrian_highlands():
    # the coast and the Danube were Latin by 395, the mountains of Dardania, Praevalitana and the Dalmatian
    # hinterland still Illyrian; vanilla has no Illyrian culture, so albanian (their heirs) carries the name
    by = pops_cultures()
    def top(loc):
        return max(set(by[loc]), key=by[loc].count)
    for loc in ("peja", "podgorica", "mostar", "pljevlja", "brskovo"):
        assert top(loc) == "albanian", loc
    for loc in ("dubrovnik", "pola", "belgrad", "sabac"):
        assert top(loc) == "roman_culture", loc
    assert re.search(r'^ albanian: "Illyrian"$', REPLACE.read_text(encoding="utf-8-sig"), re.M)
