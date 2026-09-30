"""tfe_hunnic_storm events: the phases of the Hunnic Storm reach everyone who sees them. Writes the event script; its localisation file also holds other keys, so it stays hand-written."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pdx.api import CountryFx, CountryTrig, SituationTrig
from pdx.objects import Doc

IMG = "gfx/interface/illustrations/situation/tfe_hunnic_storm.dds"


def subsidy(t: CountryTrig):
    with t.link("situation:tfe_hunnic_storm", SituationTrig) as s:
        s.has_variable("tfe_storm_by_subsidy")



def build():
    doc = Doc()
    doc.namespace("tfe_hunnic_storm")
    doc.note("The Scourge: phase 2 of the Hunnic Storm has opened (situations/tfe_hunnic_storm.txt), for everyone who sees it")
    with doc.event(1, type="country_event", category="situation_event", title='The Scourge Rises', outcome="negative", image=IMG,
                   desc=[(subsidy, "subsidy", 'Eight peoples pay the Huns tribute, and now a Roman emperor has joined the Yoke and pays them too. Gold buys the Empire a little peace and buys the Huns a great deal of war. Soon a ruler of the Huns may take the title Scourge of God.'),
                         (None, "time", 'A generation has passed since the Huns crossed the Don, and their Yoke has only grown. Soon a ruler of the Huns may take the title Scourge of God.')]) as e:
        with e.option("a", text='The world will learn our name.') as o:
            with o.trigger() as t:
                t.tag("HNS")
            o.add_prestige(10)
        with e.option("b", text='Look to the frontier.') as o:
            with o.trigger() as t, t.not_() as n:
                n.tag("HNS")

    doc.note("The Huns press on the Germanic hosts: take to the road, or stay and risk the Yoke")
    with doc.event(2, type="country_event", category="situation_event", title='The Huns Are Coming', outcome="neutral", image=IMG,
                   desc='Riders from the east have reached our pastures. Those who stayed in their path now pay the Huns tribute. You can gather the whole people and take to the road west, or stay and hold your land.') as e:
        with e.trigger() as t:
            t.tfe_is_migrator(True)
            t.tail("scripted_triggers/tfe_decline_of_the_west.txt")
            with t.not_() as n:
                n.has_variable("tfe_migrating")
            t.is_subject(False)
            t.tfe_frontier_unmanned(True)
            t.tail("scripted_triggers/tfe_decline_rome.txt")
        e.note("the road west (the Decline of the West's Migrate, generic_actions/tfe_migratory.txt)")
        with e.option("a", text='We take to the road.', historical=True) as o:
            o.custom_tooltip("tfe_start_migration_tt")
            with o.hidden_effect() as h:
                h.tfe_start_migration_effect(True)
                h.tail("scripted_effects/tfe_migratory.txt")
            with o.ai_chance_block(3) as a:
                with a.modifier(0) as t:
                    t.has_global_variable("tfe_host_took_the_road")
                a.tail("pace the chaos: one host on the road every 4 years")  # ponytail: lands after the modifier, not inside it (comments are not compared)
        with e.option("b", text='This land is ours. We stay.') as o:
            o.add_prestige(5)
            o.ai_chance(1)

    doc.note("The Reckoning: the Scourge is dead, and every people under the Yoke may rise now")
    with doc.event(3, type="country_event", category="situation_event", title='The Reckoning', outcome="positive", image=IMG,
                   desc='The Scourge is dead and the heirs quarrel over the herds. Every people under the Yoke is asking the same question: if not now, when?') as e:
        with e.trigger() as t:
            t.tfe_is_under_the_yoke(True)
            with t.not_() as n:
                n.tag("HNS")
            t.country_exists("c:HNS")
        e.note("rise with the others")
        with e.option("a", text='Rise! Break the Yoke!') as o:
            with o.trigger() as t:
                with t.or_() as x:
                    x.is_subject(False)
                    x.is_subject_type("tributary")
                with t.not_() as n:
                    n.is_at_war_with("c:HNS")
            o.note("a tributary of the Huns just stops paying; a free member goes to war")
            with o.custom_tooltip_block("tfe_break_the_yoke_tt") as c, c.trigger() as t:
                t.is_subject(False)
            with o.custom_tooltip_block("tfe_cast_off_the_tribute_tt") as c, c.trigger() as t:
                t.is_subject_type("tributary")
            with o.hidden_effect() as h:
                with h.if_() as f:
                    with f.limit() as t:
                        t.is_subject_type("tributary")
                    with f.link("c:HNS", CountryFx) as hns:
                        hns.cancel_subject("root")
                with h.else_() as f:
                    f.leave_all_wars_with("c:HNS")
                    f.declare_war_with_cb(target="c:HNS", type="casus_belli:cb_tfe_break_the_yoke")
            with o.ai_chance_block(1) as a:
                a.note("the Huns are weak: no grown heir to hold the Yoke, or a smaller army than ours")
                with a.modifier(3) as t, t.link("c:HNS", CountryTrig) as hns, hns.not_() as n, n.go_heir(op="?=") as heir:
                    heir.is_adult(True)
                with a.modifier(5) as t, t.link("c:HNS", CountryTrig) as hns:
                    hns.military_strength("root.military_strength", op="<")
                a.note("Feast the Subject Kings and Demand Greater Tribute (generic_actions/tfe_hunnic_storm.txt)")
                with a.modifier(0.3) as t:
                    t.has_variable("tfe_feasted_by_the_huns")
                with a.modifier(2) as t:
                    t.has_variable("tfe_bled_by_the_huns")
        e.note("stay loyal")
        with e.option("b", text='Better the Huns we know.') as o:
            o.ai_chance(2)

    doc.note("The Yoke is broken: Nedao")
    with doc.event(4, type="country_event", category="situation_event", title='The Yoke Is Broken', outcome="positive", image=IMG,
                   desc='By the river Nedao the subject peoples met the Huns and cut them down. The tribute empire is gone, and the steppe belongs to whoever can hold it.') as e:
        with e.option("a", text='The Storm has passed.') as o, o.trigger() as t, t.not_() as n:
            n.tag("HNS")
        with e.option("b", text='We have lost the Yoke.') as o, o.trigger() as t:
            t.tag("HNS")

    doc.note("The Huns endure: the Yoke outlived the Reckoning")
    with doc.event(5, type="country_event", category="situation_event", title='The Huns Endure', outcome="neutral", image=IMG,
                   desc='The Scourge is dead, but the heirs kept their grip. For ten years the subject peoples tested the Huns, and the Yoke held.') as e:
        with e.option("a", text='The Yoke is ours still.') as o:
            with o.trigger() as t:
                t.tag("HNS")
            o.custom_tooltip("tfe_huns_endure_tt")
        with e.option("b", text='The Huns are not finished.') as o, o.trigger() as t, t.not_() as n:
            n.tag("HNS")
    return doc


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/events/tfe_hunnic_storm.txt": build().text()}


if __name__ == "__main__":
    for rel, text in outputs().items():
        (ROOT / rel).write_text(text, encoding="utf-8-sig", newline="\n")
