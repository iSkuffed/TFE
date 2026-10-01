"""Integrity of the 395 characters, dynasties and governments (bad references crash or silently drop in-game)."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

START_DATE = (395, 1, 18)
TRAIT_FIELDS = {"ruler_trait": "ruler", "general_trait": "general", "health_trait": "health", "child_trait": "child"}
ESTATES = {"nobles_estate", "clergy_estate", "burghers_estate", "peasants_estate"}


def parse(toks, i=0):
    """Paradox script -> list of (key, value); value is a token or a nested list."""
    out = []
    while i < len(toks) and toks[i] != "}":
        key = toks[i]
        if toks[i + 1] == "{":
            val, i = parse(toks, i + 2)
            i += 1
        else:
            val, i = toks[i + 1], i + 2
        out.append((key, val))
    return out, i


def date(s):
    return tuple(int(x) for x in s.split("."))


def loc_keys(files):
    text = "\n".join(p.read_text(encoding="utf-8-sig") for p in files)
    return set(re.findall(r"^\s*([\w.]+):\d*\s", text, re.M)) - {"l_english"}


@pytest.fixture(scope="module")
def chars():
    text = (b.MOD / "main_menu/setup/start/05_characters.txt").read_text(encoding="utf-8")
    (_, db), = parse(b.tokens(text))[0]
    return db   # ordered list of (id, fields)


@pytest.fixture(scope="module")
def game():
    ours = b.MOD / "main_menu/localization/english/tfe_characters_l_english.yml"
    dyn = b.tokens((b.GAME / "main_menu/setup/start/04_dynasties.txt").read_text(encoding="utf-8-sig")
                   + (b.TOOLS / "tfe_dynasties.txt").read_text(encoding="utf-8"))
    traits = {}
    for p in (b.GAME / "in_game/common/traits").glob("*.txt"):
        for name, body in re.findall(r"^(\w+) = \{(.*?)^\}", p.read_text(encoding="utf-8-sig"), re.M | re.S):
            traits[name] = re.search(r"category = (\w+)", body).group(1)
    countries = (b.MOD / "main_menu/setup/start/10_countries.txt").read_text(encoding="utf-8")
    return dict(vanilla_loc=loc_keys((b.GAME / "main_menu/localization/english").rglob("*.yml")),
                our_loc=loc_keys([ours]), our_loc_text=ours.read_text(encoding="utf-8"),
                dynasties={t for i, t in enumerate(dyn[:-1]) if dyn[i + 1] == "{" and t.endswith("_dynasty")},
                anc=b.load_hierarchy(), traits=traits,
                cultures=b.known_cultures(),
                religions=b.known_religions(),
                landed=set(re.findall(r"^\t\t([A-Z][A-Z0-9]{2}) = \{", countries, re.M)))


def fields(body):
    d = {}
    for k, v in body:
        d.setdefault(k, []).append(v)
    return d


def test_characters_are_valid(chars, game):
    seen, problems = {}, []
    for cid, body in chars:
        f = fields(body)
        one = {k: v[0] for k, v in f.items()}
        err = problems.append
        if cid in seen:
            err(f"{cid}: defined twice")
        if not cid.startswith("tfe_"):
            err(f"{cid}: id must start with tfe_")
        for req in ("first_name", "culture", "religion", "birth_date", "birth", "tag"):
            if req not in one:
                err(f"{cid}: missing {req}")
        if one.get("culture") not in game["cultures"]:
            err(f"{cid}: unknown culture {one.get('culture')}")
        if one.get("religion") not in game["religions"]:
            err(f"{cid}: unknown religion {one.get('religion')}")
        if one.get("birth") not in game["anc"]:
            err(f"{cid}: unknown birth location {one.get('birth')}")
        if one.get("tag") not in game["landed"]:
            err(f"{cid}: tag {one.get('tag')} owns no land")
        if "birth_date" in one and date(one["birth_date"]) >= START_DATE:
            err(f"{cid}: born after the start")
        if "death_date" in one and date(one["death_date"]) < date(one.get("birth_date", "0.1.1")):
            err(f"{cid}: dies before birth")
        for rel in ("father", "mother"):
            if rel in one and one[rel] not in seen:
                err(f"{cid}: {rel} {one[rel]} must be defined earlier")
        if "dynasty" in one and one["dynasty"] not in game["dynasties"]:
            err(f"{cid}: unknown dynasty {one['dynasty']}")
        if "estate" in one and one["estate"] not in ESTATES:
            err(f"{cid}: unknown estate {one['estate']}")
        for field, cat in TRAIT_FIELDS.items():
            for t in f.get(field, []):
                if game["traits"].get(t) != cat:
                    err(f"{cid}: {t} is not a {cat} trait")
        for stat in ("adm", "dip", "mil"):
            if stat in one and not 0 <= int(one[stat]) <= 100:
                err(f"{cid}: {stat} out of range")
        for block in ("first_name", "nickname"):
            for v in f.get(block, []):
                key = dict(v)["name"]
                if key not in game["vanilla_loc"] and key not in game["our_loc"]:
                    err(f"{cid}: {block} {key} not localized")
        seen[cid] = one
    ids = set(seen)
    for cid, one in seen.items():
        if "spouse" in one and one["spouse"] not in ids:
            problems.append(f"{cid}: spouse {one['spouse']} undefined")
    assert not problems, "\n".join(problems)


def test_our_localization_does_not_shadow_vanilla(game):
    assert game["our_loc_text"].startswith("﻿l_english:")
    assert not game["our_loc"] & game["vanilla_loc"], sorted(game["our_loc"] & game["vanilla_loc"])


def test_governments_reference_living_characters_of_that_country(chars):
    db = {cid: fields(body) for cid, body in chars}
    problems = []
    for no, tag, line in b.parse_kv_file(b.TOOLS / "governments.txt"):
        if line.startswith(("privilege", "reforms")):   # not people (test_late_roman_west.py)
            continue
        for ref in re.findall(r"\btfe_\w+", line):
            if ref not in db:
                problems.append(f"governments.txt:{no}: {ref} undefined")
        m = re.match(r"(ruler|heir|consort|active_regent)\s*=\s*(\w+)$", line)
        if m and m.group(2) in db:
            c = db[m.group(2)]
            if c["tag"][0] != tag:
                problems.append(f"governments.txt:{no}: {m.group(2)} belongs to {c['tag'][0]}, not {tag}")
            if "death_date" in c and date(c["death_date"][0]) < START_DATE:
                problems.append(f"governments.txt:{no}: {m.group(2)} is dead at the start")
    assert not problems, "\n".join(problems)


def test_key_rulers_and_their_ages(chars):
    db = {cid: fields(body) for cid, body in chars}
    govs, _ = b.load_governments(b.TOOLS / "governments.txt", b.load_tags())
    # a regency ends by crowning its heir: with Honorius as ruler it waited for the heir instead, and he never ruled
    assert "heir = tfe_honorius" in govs["WRE"] and "active_regent = tfe_stilicho" in govs["WRE"]
    assert not any(line.startswith("ruler =") for line in govs["WRE"])
    assert "unsuited_for_country_ruling" not in db["tfe_honorius"].get("ruler_trait", [])   # blocks him for life
    # crowned, his heir is Eucherius, not Arcadius by blood: an heir ruling the East makes a union
    events = (b.MOD / "in_game/events/tfe_opening.txt").read_text(encoding="utf-8-sig")
    assert "set_as_designated_heir = character:tfe_eucherius" in events
    assert "ruler = tfe_arcadius" in govs["EAR"] and "ruler = tfe_alaric" in govs["VIS"]
    assert db["tfe_honorius"]["birth_date"] == ["384.9.9"]      # 10 at the start: minor under Stilicho
    assert db["tfe_arcadius"]["birth_date"][0].startswith("377")



def test_the_sons_of_theodosius(chars):
    # Honorius grows up slow and never takes the field; Arcadius is a middling emperor his ministers steer
    db = {cid: fields(body) for cid, body in chars}
    hon, arc = db["tfe_honorius"], db["tfe_arcadius"]
    assert "child_slow" in hon.get("child_trait", []) and "craven" in hon.get("ruler_trait", [])
    assert "raised_by_eunuchs" not in arc.get("ruler_trait", [])   # the eunuch system is not in play in 395
    assert "naive" in arc.get("ruler_trait", [])
    assert int(arc["adm"][0]) >= 40 and int(arc["dip"][0]) >= 40, (arc["adm"], arc["dip"])
    # both sons of a Spanish-born, Latin-speaking emperor: Roman, ruling Greek-speaking provincials in the East
    assert arc["culture"] == hon["culture"] == ["roman_culture"]

def test_portrait_modifiers_target_defined_characters(chars):
    text = (b.MOD / "main_menu/gfx/portraits/portrait_modifiers/tfe_historical_chr.txt").read_text(encoding="utf-8-sig")
    refs = set(re.findall(r"character:(\w+)", text))
    assert "tfe_honorius" in refs and refs <= {cid for cid, _ in chars}, refs - {cid for cid, _ in chars}
    assert text.count("{") == text.count("}")


def test_caucasian_kings(chars):
    govs, _ = b.load_governments(b.TOOLS / "governments.txt", b.load_tags())
    assert "ruler = tfe_trdat" in govs["IBR"] and "ruler = tfe_vramshapuh" in govs["ASK"]


def test_asian_rulers(chars):
    govs, _ = b.load_governments(b.TOOLS / "governments.txt", b.load_tags())
    for tag, cid in (("NWI", "tfe_tuoba_gui"), ("LQN", "tfe_yao_xing"), ("WQN", "tfe_qifu_qiangui"), ("WAK", "tfe_nintoku"),
                     ("LNY", "tfe_bhadravarman"), ("TRM", "tfe_purnawarman"), ("KTI", "tfe_aswawarman")):
        assert f"ruler = {cid}" in govs[tag], tag
    assert "heir = tfe_mulawarman" in govs["KTI"]


def test_arabian_and_central_asian_rulers(chars):
    govs, _ = b.load_governments(b.TOOLS / "governments.txt", b.load_tags())
    for tag, cid in (("LKM", "tfe_numan"), ("KDT", "tfe_kidara")):
        assert f"ruler = {cid}" in govs[tag], tag
