"""tfe_stilicho events: Stilicho's Glory, the showdown with Honorius, the rising and the win (RoadMap #27). Writes the
events and every string of the feature's script (auto-modifiers, biases, tooltips, the new countries' names)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "script"))
from pdx.api import CharacterFx, CharacterTrig, CountryFx, LocationTrig, RegionFx
from pdx.objects import Doc

import defs_stilicho as S

EXT, INT = "gfx/interface/illustrations/event/backgrounds/exterior/", "gfx/interface/illustrations/event/backgrounds/interior/"

MODIFIER_TEXT = {
    "tfe_stilicho_regency": ("Stilicho's Command", "The Magister Militum commands the West's armies. The army is his and the great houses follow him."),
    "tfe_glory_discredited": ("Stilicho Discredited", "Nobody at court defends Stilicho any more, and the soldiers have stopped cheering his name."),
    "tfe_glory_wanes": ("Confidence Wanes", "Every defeat is laid at Stilicho's door, and the court counts them."),
    "tfe_glory_rises": ("Stilicho's Star Rises", "The legions believe in their general, and recruits come in to serve under him."),
    "tfe_glory_idol": ("Idol of the Army", "The soldiers would follow Stilicho anywhere, even against the Emperor. Honorius knows it."),
    "tfe_olympius_regency": ("Olympius's Regency", "The official who brought Stilicho down rules for Honorius. Nobody trusts him, and he trusts nobody."),
}


def honorius_lives(t):
    return t.link("character:tfe_honorius", CharacterTrig, op="?=")


def crowning(i: CountryFx):
    """tfe_stilicho.3's immediate (root: WRE): the revolter becomes Stilicho's West, and the West splits."""
    with i.random_country() as c:
        with c.limit() as t:
            t.note("marked by tfe_stilicho_rises the moment the revolt started")
            t.has_variable("tfe_stilicho_revolter")
        c.save_scope_as("tfe_stilicho_west")
    with i.link("scope:tfe_stilicho_west", CountryFx, op="?=") as w:
        w.define_unique_country_tag("STILI")
        w.change_country_name("TFE_STILICHO")
        w.change_country_adjective("TFE_STILICHO_ADJ")
        w.change_country_color("map_romansh")
        w.change_country_flag("TFE_STILICHO")
        w.set_country_rank("country_rank:rank_empire")
        w.change_government_type("government_type:monarchy")
        w.add_gold(300)
        w.remove_variable("tfe_stilicho_revolter")
        w.set_variable("tfe_western_rome")
        w.set_variable(name="tfe_usurper_against", value="root", years=10)
        for reform in ("tfe_senatorial_immunities", "tfe_patrocinium", "tfe_disarmed_plebs", "tfe_debased_currency"):
            w.add_reform(f"government_reform:{reform}")
        w.note("Stilicho, or if he has died since the showdown, his son in his place")
        with w.if_() as f:
            with f.limit() as t, t.link("character:tfe_stilicho", CharacterTrig, op="?=") as s:
                s.is_alive(True)
            f.set_new_ruler("character:tfe_stilicho")
            with f.if_() as g:
                with g.limit() as t, t.link("character:tfe_eucherius", CharacterTrig, op="?=") as eu:
                    eu.is_alive(True)
                with g.link("character:tfe_eucherius", CharacterFx) as eu:
                    eu.move_country("scope:tfe_stilicho_west")
                g.set_as_designated_heir("character:tfe_eucherius")
        with w.else_if() as f:
            with f.limit() as t, t.link("character:tfe_eucherius", CharacterTrig, op="?=") as eu:
                eu.is_alive(True)
            f.set_new_ruler("character:tfe_eucherius")
        w.note("a backer leading the rebel side turns Annex Revolter into a white peace: send the backers home")
        with w.every_current_war() as war:
            with war.limit() as t:
                t.is_in_war("root")
            war.save_scope_as("tfe_stilicho_war")
            with war.every_war_participant() as p:
                with p.limit() as t:
                    t.is_at_war_with("root")
                    with t.not_() as n:
                        n.compare("this", "=", "scope:tfe_stilicho_west")
                p.leave_war(war="scope:tfe_stilicho_war", actor="root")
    with i.if_() as f:
        with f.limit() as t:
            t.exists("scope:tfe_stilicho_west")
        f.note("the revolt hands him part of his land, or none of it")
        with f.every_owned_location() as loc:
            with loc.limit() as t:
                t.tfe_stilicho_base_land()
            loc.change_location_owner("scope:tfe_stilicho_west")
        f.note("Arles, the prefecture of the Gauls from about 407, if he holds it")
        with f.if_() as g:
            with g.limit() as t, t.link("location:arles", LocationTrig) as a:
                a.compare("owner", "?=", "scope:tfe_stilicho_west")
            with g.link("scope:tfe_stilicho_west", CountryFx) as w:
                w.set_capital("location:arles")
        f.note("Honorius rules in his own name; the Britains and Africa break away, and Stilicho claims them all")
        with f.if_() as g:
            with g.limit() as t, honorius_lives(t) as h:
                h.is_alive(True)
            g.set_new_ruler("character:tfe_honorius")
        with f.if_() as g:
            with g.limit() as t:
                with t.not_() as n:
                    n.country_exists("c:CONST")
                t.tail("tfe_constantine_rises builds his country out of London")
                with t.link("location:london", LocationTrig) as lon:
                    lon.compare("owner", "?=", "root")
            g.tfe_constantine_rises()
        with f.if_() as g:
            with g.limit() as t:
                t.country_exists("c:GILDO")
            with g.every_owned_location() as loc:
                with loc.limit() as t:
                    t.compare("region", "=", "region:maghreb_region")
                loc.change_location_owner("c:GILDO")
        with f.else_() as g:
            g.tfe_africa_breaks_away()
        for region in ("great_britain_region", "maghreb_region"):
            with f.link(f"region:{region}", RegionFx) as r, r.every_location_in_region() as loc:
                loc.add_core("scope:tfe_stilicho_west")
        f.note("the player follows Stilicho")
        with f.if_() as g:
            with g.limit() as t:
                t.is_ai(False)
            g.change_player("scope:tfe_stilicho_west")


def build():
    doc = Doc()
    doc.note("honorius-only: the showdown is Honorius's (tools/test_western_rome.py)")
    doc.namespace("tfe_stilicho")
    doc.note("Stilicho's Glory (script/defs_stilicho.py): the warning at 80, the showdown with Honorius, the rising, and the\n"
             "win when Stilicho's West takes Honorius's capital.")

    doc.note("the first time Glory reaches 80 (tfe_add_stilicho_glory)")
    with doc.event(1, type="country_event", title="Olympius Whispers", outcome="negative",
                   desc="Olympius, a palace official from the Black Sea coast, has the Emperor's ear at Ravenna. He tells "
                        "Honorius that the army cheers Stilicho's name louder than his own, that Stilicho's son is promised "
                        "to the Emperor's sister, and that a regent's chair has never yet been enough for a man the soldiers "
                        "love.\n\nHonorius says nothing. He has started asking who commands the palace guard.",
                   image=INT + "byz_nobles_interior.dds") as e:
        with e.option("a", text="Let him talk") as o:
            o.custom_tooltip("tfe_stilicho.1.a.tt")

    doc.note("the showdown: yearly at Glory 90+, at once at 100, or on 22 Aug 408 (defs_stilicho.py)")
    with doc.event(2, type="country_event", title="The Emperor's Suspicion", outcome="negative",
                   desc="The court has split. Olympius and his friends say Stilicho means to put Eucherius in the purple, "
                        "and the Emperor half believes them. The officers say Stilicho alone has held the Rhine and the "
                        "Alps, and that the West will not outlive him.\n\nHonorius has asked where we stand.",
                   image=EXT + "byz_soldiers_exterior.dds") as e:
        with e.trigger() as t:
            with t.not_() as n:
                n.has_global_variable("tfe_stilicho_showdown")
            t.tfe_stilicho_serves_us()
        with e.immediate() as i:
            i.set_global_variable("tfe_stilicho_showdown")
        e.note("with Stilicho: he rises, and we follow him (tfe_stilicho_rises)")
        with e.option("a", text="Stand with Stilicho") as o:
            with o.trigger() as t:
                with t.custom_tooltip_block("tfe_stilicho_glory_70_tt") as ct:
                    S.glory_at_least(ct, 70)
                with t.custom_tooltip_block("tfe_stilicho_holds_gaul_tt") as ct, ct.any_owned_location() as loc, \
                        loc.or_() as either:
                    either.compare("region", "=", "region:france_region")
                    with either.and_() as a:
                        a.compare("region", "=", "region:iberia_region")
                        S.glory_at_least(a, 90)
            o.custom_tooltip("tfe_stilicho.2.a.tt")
            with o.hidden_effect() as h:
                h.tfe_stilicho_rises()
            o.ai_chance(0)
        e.note("with the Emperor: Stilicho and Eucherius die, and the East is pleased")
        with e.option("b", text="Stand with the Emperor", historical=True) as o:
            o.custom_tooltip("tfe_stilicho.2.b.tt")
            o.custom_tooltip("tfe_unity_up_20_tt")
            with o.hidden_effect() as h:
                h.note("the East thanks us for putting him down, not for outliving him")
                with h.if_() as f:
                    with f.limit() as t, t.link("character:tfe_stilicho", CharacterTrig, op="?=") as s:
                        s.is_alive(True)
                    with f.go_international_organization_data("tfe_roman_empire", op="?=") as io:
                        io.change_variable(name="tfe_unity", add=20)
                    with f.link("c:EAR", CountryFx, op="?=") as east:
                        east.add_opinion(target="root", modifier="tfe_stilicho_brought_down")
                h.tfe_the_west_loses_stilicho()
            o.ai_chance(1)

    doc.note("The day after the rising: the revolter becomes Stilicho's West, the player follows him, Honorius takes the\n"
             "throne of what is left, and Britain and Africa go their own way (fired by tfe_stilicho_rises)")
    with doc.event(3, type="country_event", hidden=True) as e, e.immediate() as i:
        crowning(i)

    doc.note("Stilicho's West holds Honorius's capital (on_action tfe_on_stilicho_takes_the_capital): it annexes the West,\n"
             "takes its name and flag, and decides what becomes of Honorius. The Imperium Romanum, left with one member,\n"
             "dissolves by its own auto_disband_trigger.")
    with doc.event(4, type="country_event", title="Stilicho Enters [tfe_honorius_seat.GetName]", outcome="positive",
                   desc="The gates are open. Honorius's guards laid down their arms when they saw who led the column, and "
                        "the palace officials are already drafting the proclamations in Stilicho's name. The West has one "
                        "master again.\n\nHonorius waits in the palace to learn what he is now.",
                   image=EXT + "byz_soldiers_exterior.dds") as e:
        with e.trigger() as t:
            t.country_exists("c:WRE")
        with e.immediate() as i:
            with i.link("c:WRE", CountryFx) as w, w.go_capital() as cap:
                cap.save_scope_as("tfe_honorius_seat")
            i.annex_country(country="c:WRE", reason="CivilWar")
            i.change_country_name("WRE")
            i.change_country_adjective("WRE_ADJ")
            i.change_country_flag("WRE")
            i.set_capital("scope:tfe_honorius_seat")
        e.note("no rival Augustus is left, but the East never forgives it")
        with e.option("a", text="Honorius dies") as o:
            with o.trigger() as t, honorius_lives(t) as h:
                h.is_alive(True)
            o.custom_tooltip("tfe_stilicho.4.a.tt")
            o.kill_character(target="character:tfe_honorius", reason="execution")
            with o.link("c:EAR", CountryFx, op="?=") as east:
                east.add_opinion(target="root", modifier="tfe_honorius_executed")
        e.note("he lives out his days at his brother's court in Constantinople")
        with e.option("b", text="Send him to his brother", historical=True) as o:
            with o.trigger() as t, honorius_lives(t) as h:
                h.is_alive(True)
                t.country_exists("c:EAR")
            o.custom_tooltip("tfe_stilicho.4.b.tt")
            with o.link("character:tfe_honorius", CharacterFx) as h:
                h.move_country("c:EAR")
        e.note("Honorius did not live to see it")
        with e.option("c", text="The West is ours") as o:
            with o.trigger() as t, t.not_() as n, honorius_lives(n) as h:
                h.is_alive(True)

    doc.loc.add("tfe_stilicho.1.a.tt", "At #Y 100#! Glory, or if it is still high enough in a year's time, Honorius will force a choice.")
    doc.loc.add("tfe_stilicho_glory_70_tt", "Stilicho's Glory is at least #Y 70#!")
    doc.loc.add("tfe_stilicho_holds_gaul_tt", "We hold land in Gaul, or in Hispania with Glory at #Y 90#! or more")
    doc.loc.add("tfe_stilicho.2.a.tt", "Stilicho's army rises in Gaul, and in Hispania too if his Glory is #Y 90#! or more. "
                "#Y We follow him#!: he becomes our ruler, at war with Honorius, who keeps Italy and the Imperium Romanum. "
                "Britain and Africa break away. Take Honorius's capital to win the West.")
    doc.loc.add("tfe_stilicho.2.b.tt", "Stilicho and his son Eucherius are put to death. Olympius becomes regent. "
                "Stability #R -50#!, the estates grow restless, and Stilicho's Glory is gone.")
    doc.loc.add("tfe_unity_up_20_tt", "[tfe_roman_unity|E]: #G +20#!")
    doc.loc.add("tfe_stilicho.4.a.tt", "Honorius is put to death. No rival Augustus is left in the West, but the East is appalled.")
    doc.loc.add("tfe_stilicho.4.b.tt", "Honorius goes to Constantinople, to live at the Eastern court.")
    for name, (title, desc) in MODIFIER_TEXT.items():
        doc.loc.add(f"AUTO_MODIFIER_NAME_{name}", title)
        doc.loc.add(f"AUTO_MODIFIER_DESC_{name}", desc)
    doc.loc.add("tfe_stilicho_brought_down", "Rid the West of Stilicho")
    doc.loc.add("tfe_honorius_executed", "Put Honorius to death")
    for key, text in (("TFE_STILICHO", "Stilicho's West"), ("TFE_STILICHO_ADJ", "Stilichonian"),
                      ("TFE_AFRICA", "Diocese of Africa"), ("TFE_AFRICA_ADJ", "African"),
                      ("tfe_stilicho_rebels", "Stilicho's Army"), ("tfe_stilicho_rebels_country", "Stilicho's West"),
                      ("tfe_stilicho_rebels_country_adjective", "Stilichonian")):
        doc.loc.add(key, text)
    return doc


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    doc = build()
    return {"in_game/events/tfe_stilicho.txt": doc.text(),
            "main_menu/localization/english/tfe_stilicho_l_english.yml": doc.loc.text()}


if __name__ == "__main__":
    for rel, text in outputs().items():
        (ROOT / rel).write_text(text, encoding="utf-8-sig", newline="\n")
