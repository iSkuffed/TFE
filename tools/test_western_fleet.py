"""The West starts with the fleets of Ravenna and Misenum: 30 transports and 5 galleys."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

ON_ACTION = b.MOD / "in_game/common/on_action/tfe_western_fleet.txt"
UNIT_TYPES = b.GAME / "in_game/common/unit_types"


def code(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig"))


def ships():
    """{(port, unit type): count} created on day one"""
    out = {}
    for port, body in re.findall(r"location:(\w+) = \{(.*?)\n\t\t\}", code(ON_ACTION), re.S):
        assert re.search(r"owner \?= \{\s*tfe_is_western_rome = yes\s*\}", body), port   # whichever West holds it
        # create_num_sub_unit = { count type } makes nothing in game: one create_sub_unit per ship, in a counted while
        assert "create_num_sub_unit" not in body, port
        for n, t in re.findall(r"while = \{\s*count = (\d+)\s*create_sub_unit = unit_type:(\w+)\s*\}", body):
            out[(port, t)] = int(n)
    return out


def test_thirty_transports_and_five_galleys_at_ravenna_and_misenum():
    fleet = ships()
    assert {p for p, _ in fleet} == {"ravenna", "naples"}   # Classis Ravennas, and Classis Misenensis on the bay of Naples
    assert sum(n for (_, t), n in fleet.items() if t == "n_cog") == 30
    assert sum(n for (_, t), n in fleet.items() if t == "n_traditional_galley") == 5


def test_the_ships_are_the_first_ages_and_the_ports_are_the_wests():
    vanilla = "".join(p.read_text(encoding="utf-8-sig") for p in UNIT_TYPES.glob("navy_*.txt"))
    for t in ("n_cog", "n_traditional_galley"):
        body = re.search(rf"^{t} = \{{(.*?)^\}}", vanilla, re.M | re.S).group(1)
        assert 'age = "age_1_traditions"' in body, t
    wre = re.search(r"\n\t\tWRE = \{(.*?)\n\t\t\}", (b.MOD / "main_menu/setup/395/10_countries.txt")
                    .read_text(encoding="utf-8"), re.S).group(1)
    for port in ("ravenna", "naples"):
        assert re.search(rf"\b{port}\b", wre), port
    assert "WRE" not in code(ON_ACTION)   # test_western_rome.py: only Honorius's files name WRE by tag
