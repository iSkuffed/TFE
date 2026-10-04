import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
sys.path.insert(0, str(ROOT / "tools"))
import advances as adv  # noqa: E402
import institutions as inst  # noqa: E402
import borders as b  # noqa: E402

KEYS = {"feudalism", "legalism", "meritocracy", "renaissance", "banking", "professional_armies", "new_world",
        "printing_press", "pike_and_shot", "confessionalism", "global_trade", "artillery_institution",
        "manufactories", "scientific_revolution", "military_revolution", "enlightenment", "industrialization",
        "levee_en_masse"}


def test_all_eighteen_are_rethemed():
    assert set(inst.THEMES) == KEYS


def test_spawn_ignores_the_game_rule():
    text = inst.outputs()["in_game/common/institution/tfe_institutions.txt"]
    assert "institution_spawn" not in text and not re.search(r"^\tlocation = ", text, re.M)
    for key in KEYS:
        assert f"tfe_{key}_plausible_location = yes" in text
        assert f"REPLACE:{key} = {{" in text


def test_every_trigger_is_written():
    text = inst.outputs()[inst.TRIGGERS]
    for key in KEYS:
        assert f"tfe_{key}_plausible_location = {{" in text


def test_every_trigger_names_real_regions():
    anc = b.load_hierarchy()
    regions = {a[2] for a in anc.values()} | {a[1] for a in anc.values()}
    for key, (_, _, body) in inst.THEMES.items():
        for name in re.findall(r"(?:region|sub_continent):(\w+)", body):
            assert name in regions, (key, name)


def test_an_institution_is_born_where_its_people_live():
    for key, (_, _, body) in inst.THEMES.items():
        assert "has_owner = yes" in body, key
    for key in KEYS - {"professional_armies"}:
        assert "dominant_culture_is_owners_culture" in inst.THEMES[key][2], key


def test_root_advances_take_the_institution_name():
    for key, (name, desc, _) in inst.THEMES.items():
        assert adv.RENAME[f"{key}_advance"] == (name, desc), key


def test_roman_advances_are_gated_on_either_empire():
    assert adv.ROMAN == "tfe_is_roman_empire = yes"


def test_395_institutions():
    text = (ROOT / "main_menu/setup/395/08_institutions.txt").read_text(encoding="utf-8")
    assert "include" not in text
    rome = b.owned_by({"EAR", "WRE"})  # honorius-only: Roman Law starts in both halves of the Empire
    blocks = dict(re.findall(r"^\s*(\w+) = \{([^}]*)\}", text, re.M))
    assert rome and all("legalism = yes" in blocks.get(loc, "") for loc in rome)
    assert not any(k in text for k in ("renaissance", "banking", "levee_en_masse"))


def test_patrocinium_skips_tribes_armies_and_pops():
    text = (ROOT / "main_menu/setup/395/08_institutions.txt").read_text(encoding="utf-8")
    blocks = dict(re.findall(r"^\s*(\w+) = \{([^}]*)\}", text, re.M))
    s = b._start()
    for t, locs in s["owned"].items():
        if t in s["country_types"] or "tribe" in s["tags"][t]["template"]:
            assert not any("feudalism" in blocks.get(l, "") for l in locs), t


def test_every_institution_can_spawn_in_395():
    owned = b.owned_by(None)  # every owned location
    anc = b.load_hierarchy()
    for key, (_, _, body) in inst.THEMES.items():
        names = set(re.findall(r"(?:region|sub_continent):(\w+)", body))
        assert not names or any(anc[l][2] in names or anc[l][1] in names for l in owned if l in anc), key
