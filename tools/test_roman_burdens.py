import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "script"))
sys.path.insert(0, str(ROOT / "tools"))
import roman_burdens as rb  # noqa: E402

LAWS = rb.LAWS
OUT = rb.outputs()
SETUP = (ROOT / "main_menu/setup/395/10_countries.txt").read_text(encoding="utf-8-sig")
REFORMS = "".join((ROOT / f"in_game/common/government_reforms/{f}.txt").read_text(encoding="utf-8-sig")
                  for f in ("tfe_late_roman_west", "tfe_late_roman_burdens"))


def west_government():
    i = SETUP.index("\t\tWRE = {")
    return SETUP[i:SETUP.index("\n\t\t}", i)]


def test_every_western_burden_has_its_law_and_the_west_starts_under_it():
    gov = west_government()
    reforms = re.findall(r"reforms = \{([^}]*)\}", gov)[0].split()
    assert sorted(reforms) == sorted(r for r, *_ in rb.BURDENS)
    for _, law, policy, _ in rb.BURDENS:
        assert f"{law} = {policy}" in gov
    assert "slavery_laws = slavery_allowed" in gov


def test_only_the_levy_law_and_the_distribution_of_power_wait_for_stilicho():
    locked = {law for _, law, _, stilicho in rb.BURDENS if stilicho}
    assert locked == {"medieval_levy_law", "distribution_of_power_law"}
    for law in locked:
        lock = LAWS.find("custom_tooltip", None, inside=(f"INJECT:{law}", "locked"))
        assert len(lock) == 1
        body = [(n.key, n.op, n.val) for n in LAWS.find("NOT", None, inside=(f"INJECT:{law}", "locked", "custom_tooltip"))[0].val]
        assert body == [("ruler", "?=", "character:tfe_stilicho"), ("has_regent", "=", "no")]
    for law in ("administrative_system", "coin_laws"):
        assert not LAWS.find("locked", None, inside=(f"INJECT:{law}",))


def test_giving_up_the_law_lifts_the_burden():
    fx = OUT["in_game/common/on_action/tfe_roman_burdens.txt"]
    assert "on_policy_changed = {\n\ton_actions = { tfe_on_policy_changed_burdens_lift }" in fx
    for reform, _, policy, _ in rb.BURDENS:
        assert (f"has_reform = government_reform:{reform}\n\t\t\t\tNOT = {{ has_policy = {policy} }}\n\t\t\t}}\n"
                f"\t\t\tremove_reform = government_reform:{reform}") in fx
        assert f"{reform} = {{" in REFORMS


def test_the_new_policies_cannot_be_taken_up_again():
    for _, law, policy, _ in rb.BURDENS:
        if policy.startswith("tfe_"):
            pot = LAWS.find("has_policy", policy, inside=(f"INJECT:{law}", policy, "potential"))
            assert len(pot) == 1


def test_the_senates_are_named_before_any_vanilla_parliament():
    text = (ROOT / "in_game/common/customizable_localization/parliaments.txt").read_text(encoding="utf-8-sig")
    keys = re.findall(r"localization_key = (\w+)", text)
    assert keys[:2] == ["country_flavor_parliament_tfe_senatus", "country_flavor_parliament_tfe_synkletos"]
    loc = OUT["main_menu/localization/english/tfe_roman_burdens_l_english.yml"]
    assert 'country_flavor_parliament_tfe_senatus: "Senātus Rōmānus"' in loc


def test_the_wests_slaves_are_captives_it_does_not_accept():
    import defs_western_start as ws
    accepted = set(re.findall(r"accepted_cultures = \{([^}]*)\}", west_government())[0].split()) | {"roman_culture"}
    cultures = [c for _, c, _ in ws.SLAVES] + [ws.SLAVES_ELSEWHERE[0]]
    assert not accepted & set(cultures), "a slave of an accepted culture is freed"
    fx = (ROOT / "in_game/common/on_action/tfe_western_start.txt").read_text(encoding="utf-8-sig")
    for c in cultures:
        assert f"type = pop_type:slaves culture = culture:{c}" in fx
