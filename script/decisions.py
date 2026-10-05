"""The Fall of the West's Native Decisions: a people beyond the rivers migrates into a Roman state of its choosing, and
Honorius's West presses Stilicho's claim on Illyricum. Writes the category, the decisions, the migration's generic action
(shown in the decisions tab) and their localisation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx, CountryFx, CountryTrig, InternationalOrganizationFx, ValueFx
from pdx.objects import Doc

from decline_rome_actions import ACTOR, select

CATEGORY = "tfe_fall_of_the_west"
EXT = "gfx/interface/illustrations/event/backgrounds/exterior/"
HEADER = """TFE: the Fall of the West's Native Decisions (written by script/decisions.py). Migrate into Rome
(generic_actions/tfe_fall_of_the_west.txt, shown in the decisions tab): a people of Germania or Dacia (tfe_is_migrator) may
give up its homeland, while the Decline of the West runs, for a great host that costs nothing while it owns no land
(auto_modifiers/tfe_migratory.txt). It cannot replenish: landless, it has no manpower, so every warrior lost is gone until
it wins land of its own. The host marches at once on the Roman state it chooses, and that ruler may buy it off with land
(Hospitalitas, generic_actions/tfe_decline_rome.txt). A settled host may take the road again until it reforms into a
monarchy (decisions/tfe_barbarian_kingdoms.txt). The Salian Franks never migrate: they Cross the Rhine.
Stilicho's Claims: Honorius's West takes a casus belli on Eastern Illyricum, at a cost in Unity."""
ROME = "scope:target_rome"


def roman_states(i: AnyFx):
    with i.every_country() as c:
        with c.limit() as t:
            t.tfe_is_roman_state()
        c.add_to_list("source")


def migrate(acts: Doc, loc):
    """Migrate into Rome: a Native Decision (a generic action shown in the decisions tab) whose picker lists every Roman
    state there is, so the choices grow and shrink as successors rise and fall."""
    with acts.generic_action("tfe_migrate") as a:
        a.field("type", "owncountry")
        a.field("show_in_decision_panel", True)
        a.field("decision_category", CATEGORY)
        with a.triggers("potential") as t:
            with t.go_situation("tfe_decline_of_the_west") as s:
                s.situation_is_active(True)
            with t.link(ACTOR, CountryTrig) as c:
                c.tfe_is_migrator()
                c.not_(lambda n: n.tag("SLF"))
                c.tail("the Salians raid over the Rhine instead (decisions/tfe_barbarian_kingdoms.txt)")
                with c.or_() as o:
                    o.not_(lambda n: n.has_variable("tfe_migrating"))
                    o.has_variable("tfe_settled")
                    o.tail("a settled host may take the road again")
                c.not_(lambda n: n.has_variable("tfe_host_kingdom"))
                c.tail("until it reforms into a monarchy (decisions/tfe_barbarian_kingdoms.txt)")
            with t.any_country() as r:
                r.tfe_is_roman_state()
        with a.triggers("allow") as t, t.link(ACTOR, CountryTrig) as c:
            with c.custom_tooltip_block("tfe_migration_not_yet_tt") as ct:
                ct.current_date("395.2.18", op=">=")
                ct.tail("a month after the game starts (defines' START_DATE)")
            c.is_subject(False)
            c.tail("no warband afield is fine: the host gathers at the capital")
            c.tfe_frontier_unmanned()
            c.tail("scripted_triggers/tfe_decline_rome.txt: a manned frontier holds them")
        a.field("ai_tick", "monthly")
        a.field("ai_tick_frequency", 1)
        a.field("automation_tick", "never")
        a.field("automation_tick_frequency", 12)
        a.note("the Roman state to march on: either Empire, Stilicho's West, or a successor born of a revolt against one\n"
               "(scripted_triggers/tfe_western_rome.txt); one that holds land, for the war to have a goal")
        with select(a, "country", CountryTrig, source=roman_states, flag="target_rome",
                    name="tfe_migrate_choose_rome", none="tfe_migrate_no_rome") as t:
            t.tfe_is_roman_state()
            with t.any_owned_location() as o:
                o.always(True)
        with a.effects("effect") as e:
            e.custom_tooltip("tfe_start_migration_tt")
            e.custom_tooltip("tfe_migrate_tt")
            with e.hidden_effect() as h, h.link(ACTOR, CountryFx) as host:
                host.tfe_start_migration_effect()
                host.tail("scripted_effects/tfe_migratory.txt")
                host.declare_war_with_cb(target=ROME, type="casus_belli:cb_tfe_migration")
        a.note("Pace the chaos: one AI people on the road at a time. None moves within a year of the last host setting out\n"
               "(tfe_host_took_the_road), and then only when pushed: the Huns at the door or Rome divided. A settled AI host\n"
               "stays settled. Of the Roman states, the one across the river first; a long trek only by chance.")
        with a.effects("ai_will_do", ValueFx) as v:
            v.value(0)
            with v.if_() as i:
                with i.limit() as t:
                    with t.not_() as n:
                        n.has_global_variable("tfe_host_took_the_road")
                    with t.link(ACTOR, CountryTrig) as c:
                        c.at_war(False)
                        c.not_(lambda n: n.has_variable("tfe_settled"))
                i.add(5)
                with i.if_() as j:
                    with j.limit() as t, t.link(ACTOR, CountryTrig) as c, c.any_neighbor_country() as n:
                        n.tfe_is_under_the_yoke()
                    j.add(45)
                with i.if_() as j:
                    with j.limit() as t, t.link(ACTOR, CountryTrig) as c, c.any_neighbor_country() as n:
                        n.compare("this", "=", ROME)
                    j.add(10)
                with i.if_() as j:
                    with j.limit() as t:
                        with t.go_international_organization_data("tfe_roman_empire", op="?=") as io:
                            io.var("tfe_unity", "<", 50)
                    j.add(25)
    loc.add("tfe_migrate", "Migrate into Rome")
    loc.add("tfe_migrate_desc", "We leave the lands of our fathers behind. Every warrior of our people joins the host on the "
            "road, to take by the sword a richer home within the lands of Rome: the Empire across the river, or one far "
            "away, or a province that has thrown off its emperor.")
    loc.add("tfe_migrate_choose_rome", "Choose the Rome to march on")
    loc.add("tfe_migrate_no_rome", "@trigger_no! No Roman state holds any land")
    loc.add("tfe_migrate_tt", "#R We declare war at once on the Roman state we choose.#! Its ruler may offer us land for "
            "our fealty.")


def illyricum(doc: Doc):
    with doc.decision("tfe_illyricum_claims", category=CATEGORY, title="Support Stilicho's Claims",
                      desc=("Stilicho holds that Theodosius meant all Illyricum for the West. Press the claim on Docleatae, "
                            "the Dardanian Mines, the Margus Valley, Singidunum, Viminacium, Naissus, Dardania and "
                            "Praevalitana: a casus belli against the East for ten years, bought with the Empire's unity."),
                      image=EXT + "byz_soldiers_exterior.dds") as d:
        with d.potential() as t:
            t.exists("international_organization:tfe_roman_empire")
            t.tag("WRE")
            t.country_exists("c:EAR")
        with d.allow() as t:
            with t.custom_tooltip_block("tfe_stilicho_serves_us_tt") as ct:
                ct.tfe_stilicho_serves_us()
            t.note("ten years between claims; no Unity floor: driving Unity down is the point")
            with t.custom_tooltip_block("tfe_illyricum_claim_pressed_tt") as ct, ct.not_() as n:
                n.has_variable("tfe_illyricum_claim")
        with d.ai_will_do() as v:
            v.note("the player's choice: the AI West never picks a quarrel with the East this way")
            v.value(-1)
        with d.option("a", text="Illyricum is the West's.") as o, o.effect() as e:
            e.set_variable(name="tfe_illyricum_claim", years=10)
            e.add_casus_belli(target="c:EAR", type="casus_belli:cb_tfe_illyrian_claim", years=10)
            e.custom_tooltip("tfe_unity_down_10_tt")
            with e.hidden_effect() as h:
                with h.link("international_organization:tfe_roman_empire", InternationalOrganizationFx, op="?=") as io:
                    io.change_variable(name="tfe_unity", add=-10)


def debug_glory(doc: Doc):
    doc.note("debug mode only (vanilla's test_decisions.txt): Glory to 100, which brings on the showdown at once")
    with doc.decision("tfe_debug_stilicho_glory", category=CATEGORY, title="(Debug) Stilicho's Glory to 100",
                      desc="Testing only: raises Stilicho's Glory to 100, and Honorius forces the showdown.",
                      image=EXT + "byz_soldiers_exterior.dds") as d:
        with d.potential() as t:
            t.debug_only(True)
            t.tfe_stilicho_serves_us()
        with d.ai_will_do() as v:
            v.value(0)
        with d.option("a", text="Glory to 100") as o, o.effect() as e:
            e.tfe_add_stilicho_glory(amount=100)


def build():
    """(the category file, the decisions file, the migration's generic action); all share one localisation."""
    cats, doc, acts = Doc(), Doc(), Doc()
    doc.note("honorius-only: Stilicho's Claims is Honorius's (tools/test_western_rome.py)")
    cats.loc = acts.loc = doc.loc
    acts.note("TFE: Migrate into Rome, a Native Decision shown in the decisions tab (written by script/decisions.py)")
    migrate(acts, doc.loc)
    cats.note("TFE: the Fall of the West's decisions (decisions/tfe_fall_of_the_west.txt), near the top of the list.")
    cats.decision_category(CATEGORY, title="Fall of the West", sort_order=0)
    doc.note(HEADER)
    illyricum(doc)
    debug_glory(doc)
    doc.loc.add("tfe_stilicho_serves_us_tt", "Stilicho lives and serves us")
    doc.loc.add("tfe_illyricum_claim_pressed_tt", "We have not pressed Stilicho's claim in the last ten years")
    return cats, doc, acts


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    cats, doc, acts = build()
    return {"in_game/common/decision_categories/tfe_decision_categories.txt": cats.text(),
            "in_game/common/decisions/tfe_fall_of_the_west.txt": doc.text(),
            "in_game/common/generic_actions/tfe_fall_of_the_west.txt": acts.text(),
            "main_menu/localization/english/tfe_decisions_l_english.yml": doc.loc.text()}


if __name__ == "__main__":
    for rel, text in outputs().items():
        (Path(__file__).resolve().parent.parent / rel).write_text(text, encoding="utf-8-sig", newline="\n")
