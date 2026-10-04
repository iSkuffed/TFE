"""Stilicho reforms the West: each of the West's four locked burdens (government_reforms/tfe_late_roman_west.txt and
tfe_late_roman_burdens.txt) is held in place by a law the West starts with, and changing that law is the only way to
lift it. The levy law and the distribution of power stay locked until Stilicho himself wears the purple."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryFx, CountryTrig
from pdx.objects import Doc
from pdx.objects_defs import Defs

AWAITS_STILICHO = "tfe_awaits_stilicho_tt"
# (reform, law, the West's starting policy, locked until Stilicho rules)
BURDENS = (
    ("tfe_disarmed_plebs", "medieval_levy_law", "tfe_plebs_disarmed", True),
    ("tfe_patrocinium", "distribution_of_power_law", "dop_favor_the_nobles", True),
    ("tfe_senatorial_immunities", "administrative_system", "autonomous_councils", False),
    ("tfe_debased_currency", "coin_laws", "tfe_debased_coinage", False),
)


def stilicho_is_emperor(t: CountryTrig):
    """Stilicho rules in his own right: a regent's chair is not the purple"""
    t.compare("ruler", "?=", "character:tfe_stilicho")
    t.has_regent(False)


def laws():
    doc = Doc()
    for reform, law, policy, stilicho in BURDENS:
        new = policy.startswith("tfe_")
        if not (new or stilicho):
            continue
        doc.note(f"TFE: {law} holds {reform} in place" + (" until Stilicho rules" if stilicho else ""))
        with doc.entry(f"INJECT:{law}") as b:
            if stilicho:
                with b.triggers("locked", CountryTrig) as t:
                    t.has_policy(policy)
                    t.has_reform(f"government_reform:{reform}")
                    with t.custom_tooltip_block(AWAITS_STILICHO) as c, c.not_() as n:
                        stilicho_is_emperor(n)
            if new:
                with b.block(policy) as p:
                    p.field("unique", True)
                    p.note("held only: once given up it is gone")
                    with p.triggers("potential", CountryTrig) as t:
                        t.has_policy(policy)
                    if policy == "tfe_debased_coinage":
                        p.note("Bullion Coins' minting: copper and some silver")
                        p.data("country_modifier", silver_used_for_minting=True, copper_used_for_minting=True,
                               goods_gold_impacts_inflation=-1.0, minting_inflation_threshold=0.02,
                               minting_income_factor=0.1)
                        p.raw("estate_preferences = { crown_estate }")
                    p.field("years", 0)
    doc.loc.add(AWAITS_STILICHO, "Only Stilicho, ruling as Emperor and not as regent, can lift this burden")
    doc.loc.add("tfe_plebs_disarmed", "Disarmed Plebs")
    doc.loc.add("tfe_plebs_disarmed_desc", "No law calls the plebs to arms; another forbids them to bear any. Change this "
                "law and the [ShowGovernmentReformName('tfe_disarmed_plebs')] reform goes with it.")
    doc.loc.add("tfe_debased_coinage", "Debased Coinage")
    doc.loc.add("tfe_debased_coinage_desc", "The mints strike copper and a little silver, and the gold the army is owed "
                "must be bought with it. Change this law and the [ShowGovernmentReformName('tfe_debased_currency')] "
                "reform goes with it.")
    # the parliament's name (customizable_localization/parliaments.txt): the West's senate in Rome, the East's in
    # Constantinople, raised to its equal by Constantius II
    doc.loc.add("country_flavor_parliament_tfe_senatus", "Senātus Rōmānus")
    doc.loc.add("country_flavor_parliament_tfe_synkletos", "Synklētos")
    return doc


def on_actions():
    d = Defs()
    d.note("TFE: a West that gives up the law holding a burden in place (roman_burdens.py) loses the burden with it")
    d.hook("on_policy_changed", "tfe_on_policy_changed_burdens_lift")
    with d.on_action("tfe_on_policy_changed_burdens_lift") as a, a.effect(CountryFx) as e:
        for reform, _, policy, _ in BURDENS:
            with e.if_() as i:
                with i.limit() as t:
                    t.scope_type("country")
                    t.has_reform(f"government_reform:{reform}")
                    with t.not_() as n:
                        n.has_policy(policy)
                i.remove_reform(f"government_reform:{reform}")
    return d


LAWS = laws()


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/laws/tfe_roman_burdens.txt": LAWS.text(),
            "in_game/common/on_action/tfe_roman_burdens.txt": on_actions().text(),
            "main_menu/localization/english/tfe_roman_burdens_l_english.yml": LAWS.loc.text()}
