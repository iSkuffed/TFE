"""Every country starts with Taxation and what it requires (script/defs_start_advances.py)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

ON_ACTION = b.MOD / "in_game/common/on_action/tfe_start_advances.txt"
ADVANCES = b.GAME / "in_game/common/advances/0_age_of_traditions.txt"


def test_taxation_and_its_prerequisites_are_researched_in_order_on_day_one():
    text = ON_ACTION.read_text(encoding="utf-8-sig")
    assert "on_game_start = {" in text and "every_country = {" in text
    granted = re.findall(r"research_advance = advance_type:(\w+)", text)
    assert granted[-1] == "taxation_advance"
    # vanilla's chain: each granted advance requires the one before it, the first requires nothing
    vanilla = ADVANCES.read_text(encoding="utf-8-sig")
    def requires(adv):
        body = vanilla.split(f"\n{adv} = {{")[1].split("\n}")[0]
        return re.findall(r"requires = (\w+)", body)
    assert requires(granted[0]) == []
    for before, adv in zip(granted, granted[1:]):
        assert requires(adv) == [before], adv
