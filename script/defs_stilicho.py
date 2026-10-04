"""Stilicho's Glory (RoadMap #27): the confidence Rome has in one man. Triggers, effects, on_actions, the Glory tiers
and the East's opinion of how it ends. Glory is a variable on the Decline of the West's situation, so it follows
Stilicho if he rises."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx, CharacterTrig, CountryFx, CountryTrig, LocationTrig, RebelsFx
from pdx.objects import Doc
from pdx.objects_defs import Defs

DECLINE = "tfe_decline_of_the_west"
GLORY = "tfe_stilicho_glory"
SHOWDOWN_DAYS = 4961   # 395.1.18 + 4961 days (365-day years) = 22 August 408, the day Stilicho fell

# (name, from, below, modifiers): the tiers of Glory. Morale nets against Debased Currency (-15%) and his command (+10%).
TIERS = (
    ("tfe_glory_discredited", None, 25, {"land_morale_modifier": -0.1, "monthly_legitimacy": -0.1,
                                         "global_estate_target_satisfaction": -0.05}),
    ("tfe_glory_wanes", 25, 50, {"land_morale_modifier": -0.05, "monthly_legitimacy": -0.05}),
    ("tfe_glory_rises", 75, 90, {"land_morale_modifier": 0.1, "global_manpower_modifier": 0.1}),
    ("tfe_glory_idol", 90, None, {"land_morale_modifier": 0.2, "global_manpower_modifier": 0.15}),
)


def glory_at_least(t, n):
    """`situation:tfe_decline_of_the_west ?= { has_variable = .. var:tfe_stilicho_glory >= n }` inside a trigger."""
    with t.go_situation(DECLINE, op="?=") as s:
        s.has_variable(GLORY)
        s.var(GLORY, ">=", n)


def glory_between(t, lo, hi):
    """a tier's potential: Stilicho serves this country and Glory is in [lo, hi) (None = open)."""
    t.tfe_stilicho_serves_us()
    with t.go_situation(DECLINE, op="?=") as s:
        s.has_variable(GLORY)
        if lo is not None:
            s.var(GLORY, ">=", lo)
        if hi is not None:
            s.var(GLORY, "<", hi)


def migrating(t):
    """a host still on the road: tfe_migrating stays set once it settles, so check tfe_settled too"""
    t.has_variable("tfe_migrating")
    with t.not_() as n:
        n.has_variable("tfe_settled")


def triggers():
    d = Defs()
    d.note("TFE: Stilicho's Glory. Scope: a country. Stilicho is alive and in its service: the regent of Honorius's West, or\n"
           "the ruler of his own once he rises. `prev`, not root: root is whoever asked.")
    with d.trigger("tfe_stilicho_serves_us", CountryTrig) as t:
        with t.link("character:tfe_stilicho", CharacterTrig, op="?=") as s:
            s.is_alive(True)
            s.compare("employer", "?=", "prev")
    d.note("Scope: a location. The land Stilicho's army holds: Gaul, and Hispania too at Glory 90 (tfe_stilicho_takes_hispania)")
    with d.trigger("tfe_stilicho_base_land", LocationTrig) as t, t.or_() as o:
        o.compare("region", "=", "region:france_region")
        with o.and_() as a:
            a.compare("region", "=", "region:iberia_region")
            a.has_global_variable("tfe_stilicho_takes_hispania")
    return d


def effects():
    d = Defs()
    d.note("TFE: Stilicho's Glory. Scope: a country. Glory moves by $amount$ if Stilicho serves this country and the bar is\n"
           "open (it closes when he falls). Kept 0-100. The first time it reaches 80 Olympius starts whispering\n"
           "(tfe_stilicho.1); at 100 the showdown comes (tfe_stilicho.2).")
    with d.effect("tfe_add_stilicho_glory", CountryFx) as e, e.if_() as i:
        with i.limit() as t:
            t.tfe_stilicho_serves_us()
            with t.go_situation(DECLINE, op="?=") as s:
                s.has_variable(GLORY)
        with i.go_situation(DECLINE) as s:
            s.change_variable(name=GLORY, add="$amount$")
            s.clamp_variable(name=GLORY, min=0, max=100)
        with i.if_() as w:
            with w.limit() as t:
                for flag in ("tfe_stilicho_warned", "tfe_stilicho_showdown"):
                    with t.not_() as n:
                        n.has_global_variable(flag)
                glory_at_least(t, 80)
            w.set_global_variable("tfe_stilicho_warned")
            w.trigger_event_non_silently("tfe_stilicho.1")
        with i.if_() as w:
            with w.limit() as t:
                with t.not_() as n:
                    n.has_global_variable("tfe_stilicho_showdown")
                glory_at_least(t, 100)
            w.trigger_event_non_silently("tfe_stilicho.2")
    the_west_loses_stilicho(d)
    rises(d)
    return d


def the_west_loses_stilicho(d):
    d.note("Scope: WRE. Stilicho is gone: put to death with his son at the showdown, or already dead. The Glory bar closes;\n"
           "Olympius, the official who brought him down, rules until Honorius's regency ends; the estates are furious.")
    with d.effect("tfe_the_west_loses_stilicho", CountryFx) as e:
        e.set_global_variable("tfe_stilicho_fell")
        with e.go_situation(DECLINE, op="?=") as s:
            s.remove_variable(GLORY)
        with e.if_() as i:
            with i.limit() as t:
                t.has_regent(True)
            i.create_character(first_name="name_olympius", culture="culture:roman_culture", religion="religion:orthodox",
                               estate="estate_type:nobles_estate", age=45, adm=30, dip=35, mil=5,
                               save_scope_as="tfe_olympius")
            i.set_regent("scope:tfe_olympius")
        for who in ("tfe_stilicho", "tfe_eucherius"):
            with e.if_() as i:
                with i.limit() as t, t.link(f"character:{who}", CharacterTrig, op="?=") as c:
                    c.is_alive(True)
                i.kill_character(target=f"character:{who}", reason="execution")
        e.add_stability(-50)


def rises(d):
    d.note("Scope: WRE. Stilicho's army rises as a revolt, not a war, as Gildo's did: Honorius can then annex it from the\n"
           "war screen. The revolter exists as soon as the revolt starts, so it is marked here: a big revolt can come out\n"
           "landless, and a host in Gaul is at war with us too. Tomorrow tfe_stilicho.3 makes it Stilicho's West, hands\n"
           "it the land and moves the player to it.")
    with d.effect("tfe_stilicho_rises", CountryFx) as e:
        with e.if_() as i:
            with i.limit() as t:
                glory_at_least(t, 90)
            i.set_global_variable("tfe_stilicho_takes_hispania")
        e.create_rebel(category="nationalist", name="tfe_stilicho_rebels", culture="culture:roman_culture",
                       religion="religion:orthodox", save_scope_as="tfe_stilicho_rebels")
        with e.every_owned_location() as loc:
            with loc.limit() as t:
                t.tfe_stilicho_base_land()
            with loc.every_pop() as p:
                p.change_pop_allegiance("scope:tfe_stilicho_rebels")
        with e.every_country() as c:
            with c.limit() as t:
                t.is_at_war_with("root")
            c.set_variable("tfe_old_enemy")
        with e.link("scope:tfe_stilicho_rebels", RebelsFx, op="?=") as r:
            r.start_revolt(True)
        with e.random_country() as c:
            with c.limit() as t:
                t.is_at_war_with("root")
                with t.not_() as n:
                    n.has_variable("tfe_old_enemy")
            c.set_variable("tfe_stilicho_revolter")
        with e.every_country() as c:
            with c.limit() as t:
                t.has_variable("tfe_old_enemy")
            c.remove_variable("tfe_old_enemy")
        e.trigger_event_silently(id="tfe_stilicho.3", days=1)


def on_actions():
    d = Defs()
    d.note("honorius-only: the showdown is Honorius's (tools/test_western_rome.py)")
    d.note("TFE: Stilicho's Glory. On day one his regency is stretched to 408 (the setup ends it at Honorius's majority,\n"
           "9 Sep 400), and the showdown is set for 22 Aug 408 in case Glory never forces it sooner.")
    d.hook("on_game_start", "tfe_on_start_stilicho")
    with d.on_action("tfe_on_start_stilicho") as a, a.effect(AnyFx) as e:
        with e.link("c:WRE", CountryFx, op="?=") as w:
            w.extend_regency(8)
            w.trigger_event_non_silently(id="tfe_stilicho.2", days=SHOWDOWN_DAYS)

    d.note("Battles Stilicho himself commands. Root is the country; scope:actor is its unit. A great battle (vanilla's own\n"
           "size test) fires only its own hook: vanilla lists the same one-off reactions under both.")
    d.hook("on_battle_won", "tfe_on_stilicho_battle_won")
    d.hook("on_battle_lost", "tfe_on_stilicho_battle_lost")
    d.hook("on_great_battle_won", "tfe_on_stilicho_great_battle_won")
    d.hook("on_great_battle_lost", "tfe_on_stilicho_great_battle_lost")
    for name, amount in (("battle_won", 2), ("battle_lost", -3), ("great_battle_won", 5), ("great_battle_lost", -6)):
        with d.on_action(f"tfe_on_stilicho_{name}") as a:
            with a.trigger(CountryTrig) as t:
                t.compare("scope:actor.leader", "?=", "character:tfe_stilicho")
            with a.effect(CountryFx) as e, e.link("scope:actor.owner", CountryFx, op="?=") as c:
                c.tfe_add_stilicho_glory(amount=amount)

    d.note("A war ends: a host still on the road beaten (+5) or taking our land (-8), Gildo and the Huns beaten (+10) or\n"
           "winning (-10). Fires for both sides; the effect only moves Glory for the country Stilicho serves.")
    d.hook("on_ending_war", "tfe_on_stilicho_war_ended")
    with d.on_action("tfe_on_stilicho_war_ended") as a:
        with a.trigger(CountryTrig) as t:
            t.tfe_stilicho_serves_us()
            t.exists("scope:winner")
            t.exists("scope:loser")
        with a.effect(CountryFx) as e:
            enemies = ((migrating, 5, -8), (lambda x: x.tag("GILDO"), 10, -10),
                       (lambda x: x.tag("HNS"), 10, -10))
            for enemy, won, lost in enemies:
                for us, them, amount in (("scope:winner", "scope:loser", won), ("scope:loser", "scope:winner", lost)):
                    with e.if_() as i:
                        with i.limit() as t:
                            t.compare("this", "=", us)
                            with t.link(them, CountryTrig) as x:
                                enemy(x)
                        i.tfe_add_stilicho_glory(amount=amount)

    d.note("Core land ceded in a peace. Not to a migration (that war's -8 counts) nor to a usurper (Gildo's -10 counts),\n"
           "and never our own transfers: the revolt, Britain and Africa move land by effect, not by treaty.")
    d.hook("on_took_location_in_peace_treaty", "tfe_on_stilicho_land_ceded")
    with d.on_action("tfe_on_stilicho_land_ceded") as a:
        with a.trigger(CountryTrig) as t:
            with t.link("scope:location", LocationTrig) as loc:
                loc.is_core_of("scope:loser")
            with t.not_() as n, n.and_() as both:
                migrating(both)
            with t.not_() as n:
                n.has_variable("tfe_usurper_against")
        with a.effect(CountryFx) as e, e.link("scope:loser", CountryFx) as loser:
            loser.tfe_add_stilicho_glory(amount=-1)

    showdown_hooks(d)

    d.note("Stilicho's West takes Honorius's capital, whatever it is (Ravenna in 402): the West is his (tfe_stilicho.4).\n"
           "Root is the country, scope:target the location, fortified (on_siege_won) or not (on_location_occupied).")
    d.hook("on_location_occupied", "tfe_on_stilicho_takes_the_capital")
    d.hook("on_siege_won", "tfe_on_stilicho_takes_the_capital")
    with d.on_action("tfe_on_stilicho_takes_the_capital") as a:
        with a.trigger(CountryTrig) as t:
            t.has_variable("tfe_western_rome")
            with t.not_() as n:
                n.tag("WRE")
            t.is_at_war_with("c:WRE")
            with t.link("c:WRE", CountryTrig, op="?=") as w:
                w.compare("capital", "=", "scope:target")
        a.events("tfe_stilicho.4")

    d.note("The same for Constantine's empire out of Britain (CONST): if it is the usurper that holds Honorius's capital,\n"
           "the West is his (tfe_stilicho.5).")
    d.hook("on_location_occupied", "tfe_on_constantine_takes_the_capital")
    d.hook("on_siege_won", "tfe_on_constantine_takes_the_capital")
    with d.on_action("tfe_on_constantine_takes_the_capital") as a:
        with a.trigger(CountryTrig) as t:
            t.tag("CONST")
            t.is_at_war_with("c:WRE")
            with t.link("c:WRE", CountryTrig, op="?=") as w:
                w.compare("capital", "=", "scope:target")
        a.events("tfe_stilicho.5")
    return d


def showdown_hooks(d):
    d.note("Every year Glory stands at 90 or more, a one-in-two chance that Honorius forces the question.")
    d.hook("yearly_country_pulse", "tfe_on_stilicho_yearly")
    with d.on_action("tfe_on_stilicho_yearly") as a:
        with a.trigger(CountryTrig) as t:
            t.tag("WRE")
            t.tfe_stilicho_serves_us()
            with t.not_() as n:
                n.has_global_variable("tfe_stilicho_showdown")
            glory_at_least(t, 90)
        with a.effect(CountryFx) as e, e.random(50) as r:
            r.trigger_event_non_silently("tfe_stilicho.2")
    d.note("Stilicho dies before the showdown (battle, age): the West loses him without the East's thanks. After he has\n"
           "risen, his own country goes on under Eucherius, and only the bar closes. At the showdown's own execution the\n"
           "showdown is already set, so only the bar closes (it already has).")
    d.hook("on_character_death", "tfe_on_stilicho_dies")
    with d.on_action("tfe_on_stilicho_dies") as a:
        with a.trigger(CountryTrig) as t:
            t.compare("scope:target", "=", "character:tfe_stilicho")
        with a.effect(CountryFx) as e:
            with e.if_() as i:
                with i.limit() as t:
                    t.tag("WRE")
                    with t.not_() as n:
                        n.has_global_variable("tfe_stilicho_showdown")
                i.set_global_variable("tfe_stilicho_showdown")
                i.tfe_the_west_loses_stilicho()
            with e.else_() as i, i.go_situation(DECLINE, op="?=") as s:
                s.remove_variable(GLORY)


def auto_modifiers():
    doc = Doc()
    doc.note("honorius-only: Olympius rules for Honorius, not for Stilicho (tools/test_western_rome.py)")
    doc.note("TFE: Stilicho's Glory. Each applies while Stilicho serves the country, so all of them move with him if he rises.")
    doc.note("his command: the army is his and the great houses follow him (was the 68-month tfe_stilicho_regency)")
    doc.modifier("tfe_stilicho_regency", potential=lambda t: t.tfe_stilicho_serves_us(),
                 land_morale_modifier=0.1, global_nobles_estate_power=0.2)
    for name, lo, hi, mods in TIERS:
        doc.modifier(name, potential=lambda t, lo=lo, hi=hi: glory_between(t, lo, hi), **mods)

    def olympius_rules(t):
        t.has_global_variable("tfe_stilicho_fell")
        t.tag("WRE")
        t.has_regent(True)
    doc.note("Olympius rules for Honorius after Stilicho's fall: no Glory, no command, and every estate angry")
    doc.modifier("tfe_olympius_regency", potential=olympius_rules,
                 global_nobles_estate_power=0.1, global_estate_target_satisfaction=-0.1)
    return doc


def biases():
    doc = Doc()
    doc.note("TFE: what the East thinks of how the West settles Stilicho (events/tfe_stilicho.txt)")
    doc.note("the West put Stilicho to death: the East never trusted him")
    doc.bias("tfe_stilicho_brought_down", 50, max=50, yearly_decay=5)
    doc.note("Honorius put to death: the East is appalled")
    doc.bias("tfe_honorius_executed", -75, min=-75, yearly_decay=3)
    return doc


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/scripted_triggers/tfe_stilicho.txt": triggers().text(),
            "in_game/common/scripted_effects/tfe_stilicho.txt": effects().text(),
            "in_game/common/on_action/tfe_stilicho.txt": on_actions().text(),
            "in_game/common/auto_modifiers/tfe_stilicho.txt": auto_modifiers().text(),
            "in_game/common/biases/tfe_stilicho.txt": biases().text()}
