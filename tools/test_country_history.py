"""Every 395 country's agenda tells its own 395 history, not vanilla's 1337 one."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

RULES = b.MOD / "in_game/common/customizable_localization/country_history.txt"
LOC = b.MOD / "main_menu/localization/english/tfe_country_history_l_english.yml"
START = b.MOD / "main_menu/setup/395/10_countries.txt"


def test_every_start_country_has_its_history():
    tags = set(re.findall(r"^\t\t(\w{3}) = \{", START.read_text(encoding="utf-8-sig"), re.M))
    rules = dict(re.findall(r"localization_key = (\w+) trigger = \{ tag = (\w{3}) \}", RULES.read_text(encoding="utf-8-sig")))
    loc = dict(re.findall(r'^ (\w+): "(.*)"$', LOC.read_text(encoding="utf-8-sig"), re.M))
    assert set(rules.values()) == tags, sorted(set(rules.values()) ^ tags)
    assert all(key == f"tfe_history_{tag}" for key, tag in rules.items())
    assert set(loc) == set(rules) | {"tfe_history_fallback"}, sorted(set(loc) ^ (set(rules) | {"tfe_history_fallback"}))
    for key, text in loc.items():
        assert '"' not in text and "[" not in text, key   # plain text: a stray quote or script code breaks the line
        assert text.count("\\n\\n") == 1, key            # two paragraphs, like vanilla's


def test_files_are_bom_prefixed():
    for p in (RULES, LOC):
        assert p.read_bytes().startswith(b"\xef\xbb\xbf"), p.name
