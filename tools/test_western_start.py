"""The West opens at -25 stability, 35% inflation and 55 legitimacy."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

ON_ACTION = b.MOD / "in_game/common/on_action/tfe_western_start.txt"


def code():
    return " ".join(re.sub(r"#[^\n]*", "", ON_ACTION.read_text(encoding="utf-8-sig")).split())


def test_the_west_starts_unstable_inflated_and_half_legitimate():
    body = re.search(r"c:WRE \?= \{(.*?)\}", code()).group(1)
    assert re.search(r"set_stability = -25\b", body)
    assert re.search(r"set_inflation = 0\.35\b", body)
    assert re.search(r"set_legitimacy = 55\b", body)


def test_it_runs_on_game_start():
    assert "on_game_start" in code() and "tfe_on_start_western_state" in code()
