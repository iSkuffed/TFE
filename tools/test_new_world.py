"""The Americas leave the world: nobody lives there, nobody owns it, nobody can, and no advance reaches for it."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))
import borders as b  # noqa: E402
import advances as adv  # noqa: E402

ANC = b.load_hierarchy()
AMERICA = {l for l, a in ANC.items() if a[0] == "america"}
TAGS = ("MOC", "NAZ", "TKL", "TTH", "ZPT")


def test_no_one_lives_in_the_americas():
    pops = (ROOT / "main_menu/setup/395/06_pops.txt").read_text(encoding="utf-8")
    assert not AMERICA & set(re.findall(r"^(\w+) = \{", pops, re.M))


def test_no_american_countries():
    countries = (ROOT / "main_menu/setup/395/10_countries.txt").read_text(encoding="utf-8")
    assert not any(re.search(rf"\b{t}\b", countries) for t in TAGS)


def test_the_americas_are_not_ownable():
    text = (ROOT / "in_game/map_data/default.map").read_text(encoding="utf-8")
    block = text.split("non_ownable = {", 1)[1].split("}", 1)[0].split()
    assert AMERICA <= set(block)


def test_no_advance_grants_flat_colonial_range():
    text, _ = adv.build()
    assert "colonial_range = " not in text
    granting = {k for k, n in adv.vanilla().items() if any(c.key == "colonial_range" for c in n.val)}
    assert granting and granting <= set(adv.STRIP)
