"""The hosts become kingdoms: a settled host's people spread over the land it won, it may reform into a monarchy and
accept its subjects' tongue and take their faith, and the Salian Franks raid over the Rhine instead of migrating."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from decisions import CATEGORY, EXT
from defs_migratory import create_units
from pdx.api import CountryFx, CountryTrig, LocationFx
from pdx.objects import Doc
from pdx.objects_defs import Defs

HOST = ((24, "a_footmen"), (8, "a_tribal_cavalry"))   # the great host a migration or a raid over the Rhine raises
FULL_AT = 5       # a host that settles this many locations plants all the people who followed it
MAX_SHARE = 2     # and never more than twice them, however much land it takes
RHINE_CB = "cb_tfe_cross_the_rhine"
RHINE_WAR = "tfe_rhine_war"   # set while the Franks' raid over the Rhine runs: its host is free, Roman towns feed it
RHINE_YEARS = 10
LORDS_CAPACITY = 4     # culture capacity for the land's own culture, accepted once: a small people over millions overruns it
SETTLED_INTEGRATION = 1.0   # +100% integration speed where the host's people settled
LORDS = "tfe_lords_of_the_land"
SETTLED = "tfe_settled_by_the_host"


def muster():
    d = Defs()
    d.note("TFE: a people's great host gathers (scope: the country). Shared by a migration (tfe_start_migration_effect,\n"
           "scripted_effects/tfe_migratory.txt) and the Franks' Cross the Rhine (decisions/tfe_barbarian_kingdoms.txt).")
    with d.effect("tfe_muster_the_host_effect", CountryFx) as e:
        e.save_scope_as("tfe_muster_owner")
        with e.random_army() as a, a.go_unit_location() as loc:
            loc.save_scope_as("tfe_muster")
        with e.if_() as i:
            i.limit(lambda t: t.not_(lambda n: n.exists("scope:tfe_muster")))
            i.tail("no warband afield: the host gathers at the capital")
            with i.go_capital(op="?=") as cap:
                cap.save_scope_as("tfe_muster")
        with e.link("scope:tfe_muster", LocationFx, op="?=") as m:
            create_units(m, "scope:tfe_muster_owner", "scope:tfe_muster", HOST)
    return d


def settle_event(doc: Doc):
    doc.namespace("tfe_barbarian_kingdoms")
    doc.note(f"A host has settled (on_action/tfe_migratory.txt fires this a day later, once the whole peace or Hospitalitas\n"
             f"has handed it its land). Its people (tfe_host_people) spread evenly over every location it owns, and their\n"
             f"number grows with the land: all of them on {FULL_AT} locations, a share on fewer, and up to {MAX_SHARE}x on\n"
             f"{FULL_AT * MAX_SHARE} or more. So each location gets people / {FULL_AT}, or people x {MAX_SHARE} / locations past that.")
    with doc.event(1, type="country_event", title="The Host Settles", hidden=True) as e:
        with e.trigger() as t:
            t.has_variable("tfe_host_people")
        with e.immediate() as i:
            i.set_variable(name="tfe_host_share", value="var:tfe_host_people")
            with i.if_() as f:
                f.limit(lambda t: t.num_locations(FULL_AT * MAX_SHARE, op=">="))
                f.change_variable(name="tfe_host_share", multiply=MAX_SHARE)
                f.change_variable(name="tfe_host_share", divide="num_locations")
            with i.else_() as f:
                f.change_variable(name="tfe_host_share", divide=FULL_AT)
            with i.every_owned_location() as loc:
                loc.add_pop(culture="root.culture", religion="root.religion", type="pop_type:peasants",
                            size="root.var:tfe_host_share")
                loc.note("land the host's own people settled is quick to integrate: no clock to race, conquests after the\n"
                         "migration ends integrate at vanilla's pace")
                loc.add_location_modifier(modifier=SETTLED)
            i.remove_variable("tfe_host_people")
            i.remove_variable("tfe_host_share")


def crowned_event(doc: Doc):
    doc.note("A host has reformed into a monarchy (tfe_reform_into_a_monarchy, a day before): its nobles get the Auxilium et\n"
             "Consilium the start grant could not give a people that was no monarchy. Vanilla's privilege also needs the\n"
             "Knights advance, rechecked whenever the faith changes, so the crown brings feudalism and knights with it.")
    with doc.event(2, type="country_event", title="The Crown's Privileges", hidden=True) as e:
        with e.immediate() as i:
            for adv in ("feudalism_advance", "noble_knights"):
                with i.if_() as f:
                    f.limit(lambda t, adv=adv: t.not_(lambda n: n.has_advance(adv)))
                    f.research_advance(f"advance_type:{adv}")
            with i.if_() as f:
                f.limit(lambda t: t.not_(lambda n: n.has_estate_privilege("estate_privilege:auxilium_et_consilium")))
                f.grant_estate_privilege("estate_privilege:auxilium_et_consilium")


def reform(doc: Doc):
    with doc.decision("tfe_reform_into_a_monarchy", category=CATEGORY, title="Reform into a Monarchy",
                      desc=("Our warriors have land now, and land needs a king who stays. The war-leader's hall becomes a "
                            "court, his companions become counts who owe him aid and counsel, and the law of the host becomes the law of the realm."),
                      image=EXT + "soldiers/north_german_soldiers_exterior.dds") as d:
        with d.potential() as t:
            t.has_variable("tfe_settled")
            t.tail("on_action/tfe_migratory.txt: a host that has taken land")
            t.not_(lambda n: n.has_variable("tfe_host_kingdom"))
        with d.ai_will_do() as v:
            v.value(100)
        with d.option("a", text="Long live the king.") as o, o.effect() as e:
            e.custom_tooltip("tfe_host_kingdom_tt")
            e.change_government_type("government_type:monarchy")
            e.set_variable("tfe_host_kingdom")
            e.tail("never migrates again (decisions/tfe_fall_of_the_west.txt)")
            e.trigger_event_silently(id="tfe_barbarian_kingdoms.2", days=1)
            e.tail("the new monarchy only counts from the next day")


def majority_culture(doc: Doc):
    with doc.decision("tfe_accept_majority_culture", category=CATEGORY, title="Honour the Tongue of the Land",
                      desc=("Our children already speak the language of the fields and the market. Let the court honour it "
                            "too: the people of the land stand beside our own, and our own tongue keeps its place."),
                      image=EXT + "byz_soldiers_exterior.dds", only_once=True) as d:
        with d.potential() as t:
            t.has_variable("tfe_host_kingdom")
            t.exists("dominant_culture")
            t.not_(lambda n: n.compare("dominant_culture", "=", "root.culture"))
            t.not_(lambda n: n.has_accepted_culture("dominant_culture"))
        with d.ai_will_do() as v:
            v.value(10)
        with d.option("a", text="They are our people too.") as o, o.effect() as e:
            with e.go_dominant_culture() as c:
                c.save_scope_as("tfe_new_culture")
            e.add_accepted_culture("scope:tfe_new_culture")
            e.note("a few thousand warriors accepting millions of subjects would overrun culture capacity at once; the grant\n"
                   "covers it then, and every further conquest of that people eats into it again")
            e.add_country_modifier(modifier=LORDS)


def majority_religion(doc: Doc):
    with doc.decision("tfe_convert_to_majority_religion", category=CATEGORY, title="Kneel at the People's Altars",
                      desc=("Our priests and our subjects' priests do not share a table, and our subjects notice. The king "
                            "and his house will worship as the land worships."),
                      image=EXT + "byz_soldiers_exterior.dds", only_once=True) as d:
        with d.potential() as t:
            t.has_variable("tfe_host_kingdom")
            t.exists("dominant_religion")
            t.not_(lambda n: n.compare("dominant_religion", "=", "root.religion"))
        with d.ai_will_do() as v:
            v.value(25)
        with d.option("a", text="One faith for king and people.") as o, o.effect() as e:
            with e.go_dominant_religion() as r:
                r.save_scope_as("tfe_new_religion")
            e.change_religion("scope:tfe_new_religion")
            e.change_religion_for_ruler_and_family(country="root", religion="scope:tfe_new_religion")


def western_rome_next_door(t: CountryTrig):
    with t.any_neighbor_country() as n:
        n.tfe_is_western_rome()


def cross_the_rhine(doc: Doc):
    with doc.decision("tfe_cross_the_rhine", category=CATEGORY, title="Cross the Rhine",
                      desc=("We will not leave the land of our fathers, but the land across the river is rich and its "
                            "garrisons are thin. Every warrior of the Salians joins the host for one great raid into Roman "
                            "Gaul, and the towns we take will send us men."),
                      image=EXT + "soldiers/north_german_soldiers_exterior.dds") as d:
        with d.potential() as t:
            t.tag("SLF")
            t.tail("the Salians never migrate (decisions/tfe_fall_of_the_west.txt)")
            with t.go_situation("tfe_decline_of_the_west") as s:
                s.situation_is_active(True)
        with d.allow() as t:
            t.at_war(False)
            t.is_subject(False)
            with t.custom_tooltip_block("tfe_rhine_crossed_tt") as ct:
                ct.not_(lambda n: n.has_variable("tfe_crossed_the_rhine"))
            western_rome_next_door(t)
        d.note("a raid now and then, the more when Rome is weak or already busy elsewhere")
        with d.ai_will_do() as v:
            v.value(5)
            with v.if_() as i:
                with i.limit() as t, t.go_international_organization_data("tfe_roman_empire", op="?=") as io:
                    io.var("tfe_unity", "<", 50)
                i.add(20)
            with v.if_() as i:
                with i.limit() as t, t.any_neighbor_country() as n:
                    n.tfe_is_western_rome()
                    n.at_war(True)
                i.add(20)
        with d.option("a", text="Over the river!") as o, o.effect() as e:
            e.custom_tooltip("tfe_cross_the_rhine_tt")
            with e.hidden_effect() as h:
                h.set_variable(name="tfe_crossed_the_rhine", years=RHINE_YEARS)
                h.set_variable(RHINE_WAR)
                h.tail("auto_modifiers/tfe_migratory.txt, on_action/tfe_defectors.txt; gone when the war ends")
                with h.random_neighbor_country() as n:
                    n.limit(lambda t: t.tfe_is_western_rome())
                    n.save_scope_as("tfe_victim")
                h.tfe_muster_the_host_effect(True)
                h.add_casus_belli(target="scope:tfe_victim", type=f"casus_belli:{RHINE_CB}")
                h.declare_war_with_cb(target="scope:tfe_victim", type=f"casus_belli:{RHINE_CB}")


def casus_belli(cb: Doc):
    cb.note("TFE: the Salian Franks' raid over the Rhine (decisions/tfe_barbarian_kingdoms.txt). A landed people cannot use the\n"
            "landless host's Migration, so this is its twin: the same war goal, only while the raid is on.")
    with cb.entry(RHINE_CB) as c:
        with c.triggers("create_visible", CountryTrig) as t:
            t.has_variable(RHINE_WAR)
        with c.triggers("create_enabled", CountryTrig) as t, t.link("scope:target", CountryTrig) as x:
            x.tfe_is_western_rome()
        c.field("speed", 100)
        c.field("war_goal_type", "superiority_tfe_migration")
    cb.loc.add(RHINE_CB, "Raid over the Rhine")
    cb.loc.add(f"{RHINE_CB}_desc", "The whole people has crossed the river, and it will not go home empty-handed.")


def on_actions():
    d = Defs()
    d.note("TFE: the raid over the Rhine is over when its war ends: the host costs upkeep again.")
    d.hook("on_ending_war", "tfe_on_rhine_war_ended")
    # ponytail: any war of the Franks ending ends it; check the war's enemy if they ever fight two at once
    with d.on_action("tfe_on_rhine_war_ended") as a:
        with a.trigger(CountryTrig) as t:
            t.has_variable(RHINE_WAR)
        with a.effect(CountryFx) as e:
            e.remove_variable(RHINE_WAR)
    return d


def build():
    """(decisions, events, casus belli, static modifiers); one localisation, decisions.loc."""
    doc, events, cb = Doc(), Doc(), Doc()
    events.loc = cb.loc = doc.loc
    doc.note("TFE: the hosts become kingdoms (written by script/barbarian_kingdoms.py). A settled host may Reform into a\n"
             "Monarchy, after which it never migrates again, and then accept its subjects' tongue and take their faith. The Salian Franks\n"
             "never migrate: they raid over the Rhine instead.")
    reform(doc)
    majority_culture(doc)
    majority_religion(doc)
    cross_the_rhine(doc)
    settle_event(events)
    crowned_event(events)
    casus_belli(cb)
    mods = Doc()
    mods.loc = doc.loc
    mods.note("TFE: the hosts become kingdoms (written by script/barbarian_kingdoms.py)")
    mods.modifier(LORDS, category="country", cultures_capacity=LORDS_CAPACITY)
    mods.modifier(SETTLED, category="location", local_integration_speed_modifier=SETTLED_INTEGRATION)
    doc.loc.add(f"STATIC_MODIFIER_NAME_{LORDS}", "Lords of the Land")
    doc.loc.add(f"STATIC_MODIFIER_DESC_{LORDS}", "We rule a people far greater than our own, and we have taken its tongue "
                "beside ours. Our kings speak to their subjects in words they understand.")
    doc.loc.add(f"STATIC_MODIFIER_NAME_{SETTLED}", "Settled by the Host")
    doc.loc.add(f"STATIC_MODIFIER_DESC_{SETTLED}", "Our own people took up farms here when the host came to rest. Their "
                "headmen know the land, and the land is quick to answer to us.")
    doc.loc.add("tfe_host_kingdom_tt", "#R We can never take the road again.#!\nOur nobles are granted "
                "#Y Auxilium et Consilium#!, and we learn #Y Feudalism#! and #Y Knights#!.")
    doc.loc.add("tfe_rhine_crossed_tt", "We have not crossed the Rhine in the last ten years")
    doc.loc.add("tfe_cross_the_rhine_tt",
                "#R We declare war on the Western Roman Empire across the river.#!\nTwenty-four regiments of footmen and eight of "
                "tribal cavalry join our host. Until the war ends our [army|e] costs nothing to maintain, and every Roman "
                "town we take sends it men.")
    doc.loc.add("AUTO_MODIFIER_NAME_tfe_rhine_host", "Raid over the Rhine")
    return doc, events, cb, mods


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    doc, events, cb, mods = build()
    return {"in_game/common/scripted_effects/tfe_barbarian_kingdoms.txt": muster().text(),
            "in_game/common/decisions/tfe_barbarian_kingdoms.txt": doc.text(),
            "in_game/events/tfe_barbarian_kingdoms.txt": events.text(),
            "in_game/common/casus_belli/tfe_cross_the_rhine.txt": cb.text(),
            "in_game/common/on_action/tfe_barbarian_kingdoms.txt": on_actions().text(),
            "main_menu/common/static_modifiers/tfe_barbarian_kingdoms.txt": mods.text(),
            "main_menu/localization/english/tfe_barbarian_kingdoms_l_english.yml": doc.loc.text()}
