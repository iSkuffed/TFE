"""The peoples beyond the limes open hungry: expansionist AI, an army each, tribesmen, tribal privileges, a Hunnic horde
that rides (script/defs_barbarian_start.py, script/defs_start_advances.py, borders.tribal_pops)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "script"))
import borders as b
import defs_barbarian_start
import defs_decline_of_the_west

SETUP = b.MOD / "main_menu/setup/395"
MIGRATORS = defs_decline_of_the_west.MIGRATORS


def code(rel):
    return " ".join(re.sub(r"#[^\n]*", "", (b.MOD / rel).read_text(encoding="utf-8-sig")).split())


def test_the_migrators_are_expansionist_and_the_huns_aggressive():
    got = dict(re.findall(r"(\w{3}) = \{ ai_personality = (\w+) \}", code("main_menu/setup/395/26_ai_personalities.txt")))
    assert got == {**{m: "ai_expansionist" for m in MIGRATORS}, "HNS": "ai_aggressive"}


def test_every_migrator_has_its_own_camp_followers_at_its_capital():
    armies = {m.group(1): m.group(2) for m in re.finditer(
        r"army = \{ country = (\w+) location = (\w+) sub_units = \{ a_camp_followers = \{ strength = 1 \} \} \}",
        code("main_menu/setup/395/27_armies.txt"))}
    countries = (SETUP / "10_countries.txt").read_text(encoding="utf-8")
    for m in MIGRATORS:
        capital = re.search(rf"^\t\t{m} = \{{.*?capital = (\w+)", countries, re.M | re.S).group(1)
        assert armies.get(m) == capital, m


def test_each_migrator_is_granted_every_privilege_it_lacks():
    text = code("in_game/common/on_action/tfe_barbarian_start.txt")
    assert "every_country = { limit = { tfe_is_migrator = yes }" in text
    assert len(defs_barbarian_start.PRIVILEGES) == 14
    for p in defs_barbarian_start.PRIVILEGES:
        assert (f"limit = {{ NOT = {{ has_estate_privilege = estate_privilege:{p} }} }} "
                f"grant_estate_privilege = estate_privilege:{p}") in text, p


def test_the_huns_ride_as_horse_lords_and_lean_decentralised():
    chain = re.findall(r"research_advance = advance_type:(\w+)", code("in_game/common/on_action/tfe_start_advances.txt").split("c:HNS")[1])
    assert chain == ["agriculture_advance", "windmills_advance", "ranching", "horse_riding_advance", "horse_lords"]
    advances = "".join(p.read_text(encoding="utf-8-sig") for p in (b.GAME / "in_game/common/advances").glob("*.txt"))
    for before, adv in zip(chain, chain[1:]):   # each requires the one before it
        assert re.search(rf"\n{adv} = \{{[^\n]*\n(?:(?!\n\}}).)*?requires = {before}\b", advances, re.S), adv
    assert re.search(r"c:HNS \?= \{ set_societal_value = \{ value = 80 type = centralization_vs_decentralization \} \}",
                     code("in_game/common/on_action/tfe_barbarian_start.txt"))


def test_a_european_barbarian_location_is_half_tribesmen_and_rome_is_unchanged():
    pops = (SETUP / "06_pops.txt").read_text(encoding="utf-8")
    sizes = lambda loc, kind: [float(x) for x in re.findall(
        rf"type = {kind}\tsize = ([\d.]+)", re.search(rf"^{loc} = \{{(.*?)^\}}", pops, re.M | re.S).group(1))]
    # tribal_pops on a hand-made location: peasants split by TRIBAL_SHARE, culture and religion kept
    text = "x = {\n\tdefine_pop = {\ttype = peasants\tsize = 4.000\tculture = a\treligion = r }\n}\n"
    out = b.tribal_pops(text, {"x": "FRK"}, {"x": ("europe",)}, 0.5)
    assert out == "x = {\n\tdefine_pop = {\ttype = peasants\tsize = 2.000\tculture = a\treligion = r }\n\t" \
                  "define_pop = {\ttype = tribesmen\tsize = 2.000\tculture = a\treligion = r }\n}\n"
    for owner in ("WRE", None):
        assert b.tribal_pops(text, {"x": owner}, {"x": ("europe",)}) == text
    assert b.tribal_pops(text, {"x": "FRK"}, {"x": ("asia",)}) == text
    # and in the generated file: a Frankish location has both, a Roman one has no tribesmen
    countries = (SETUP / "10_countries.txt").read_text(encoding="utf-8")
    frk = re.search(r"^\t\tFRK = \{.*?own_control_core = \{(.*?)\}", countries, re.M | re.S).group(1).split()
    loc = next(l for l in frk if sizes(l, "peasants") and sizes(l, "tribesmen"))
    assert abs(sum(sizes(loc, "tribesmen")) - sum(sizes(loc, "peasants"))) < 0.01 * len(sizes(loc, "peasants"))
    assert not sizes("arles", "tribesmen") and sizes("arles", "peasants")
