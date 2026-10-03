"""The Fall of the West decisions: a people beyond the rivers migrates into the East or the West, and Honorius's West
presses Stilicho's claim on Illyricum. Writes the category, the decisions and their localisation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryTrig, InternationalOrganizationFx
from pdx.objects import Doc

CATEGORY = "tfe_fall_of_the_west"
EXT = "gfx/interface/illustrations/event/backgrounds/exterior/"
HEADER = """TFE: the Fall of the West's decisions (written by script/decisions.py).
Migrate: a people of Germania or Dacia (tfe_is_migrator) may once give up its homeland, while the Decline of the West
runs, for a great host that costs nothing while it owns no land (auto_modifiers/tfe_migratory.txt). It cannot
replenish: landless, it has no manpower, so every warrior lost is gone until it wins land of its own. One decision per
empire: the host marches on the East or the West at once, and that Augustus may buy it off with land (Hospitalitas,
generic_actions/tfe_decline_rome.txt). The two differ only in the empire.
Stilicho's Claims: Honorius's West takes a casus belli on Eastern Illyricum, at a cost in Unity."""
WHERE = {"EAR": ("East", "south over the Danube"), "WRE": ("West", "west over the Rhine")}


def is_target(t: CountryTrig, tag):
    """the empire this decision marches on: the East, or any western Rome (Stilicho's West too)."""
    if tag == "WRE":
        t.tfe_is_western_rome()
    else:
        t.tag(tag)


def migrate(doc: Doc, name: str, tag: str):
    side, road = WHERE[tag]
    with doc.decision(name, category=CATEGORY, title=f"Migrate into the {side}",
                      desc=("We leave the lands of our fathers behind. Every warrior of our people joins the host on the "
                            f"road, {road}, to take by the sword a richer home within the Empire of the {side}."),
                      image=EXT + "soldiers/north_german_soldiers_exterior.dds") as d:
        with d.potential() as t:
            with t.go_situation("tfe_decline_of_the_west") as s:
                s.situation_is_active(True)
            t.tfe_is_migrator()
            with t.not_() as n:
                n.has_variable("tfe_migrating")
            if tag == "WRE":
                with t.any_country() as w:
                    w.tfe_is_western_rome()
            else:
                t.country_exists(f"c:{tag}")
        with d.allow() as t:
            with t.custom_tooltip_block("tfe_migration_not_yet_tt") as ct:
                ct.current_date("395.2.18", op=">=")
                ct.tail("a month after the game starts (defines' START_DATE)")
            t.is_subject(False)
            t.tail("no warband afield is fine: the host gathers at the capital")
            t.tfe_frontier_unmanned()
            t.tail("scripted_triggers/tfe_decline_rome.txt: a manned frontier holds them")
        d.note("Pace the chaos: one AI people on the road at a time. None moves within 4 years of the last host setting out\n"
               "(tfe_host_took_the_road), and then only when pushed: the Huns at the door or Rome divided.")
        with d.ai_will_do() as v:
            v.value(0)
            with v.if_() as i:
                with i.limit() as t:
                    with t.not_() as n:
                        n.has_global_variable("tfe_host_took_the_road")
                    t.at_war(False)
                i.add(5)
                with i.if_() as j:
                    with j.limit() as t, t.any_neighbor_country() as n:
                        n.tfe_is_under_the_yoke()
                    j.add(45)
                i.note("the empire across the river first")
                with i.if_() as j:
                    with j.limit() as t, t.any_neighbor_country() as n:
                        is_target(n, tag)
                    j.add(10)
                with i.if_() as j:
                    with j.limit() as t:
                        with t.go_international_organization_data("tfe_roman_empire", op="?=") as io:
                            io.var("tfe_unity", "<", 50)
                    j.add(25)
        with d.option("a", text="Take the road.") as o, o.effect() as e:
            e.custom_tooltip("tfe_start_migration_tt")
            e.custom_tooltip(f"tfe_migrate_{tag}_tt")
            with e.hidden_effect() as h:
                victim = f"c:{tag}"
                if tag == "WRE":
                    h.note("the western Rome the host borders, else the larger: Stilicho's West may stand beside Honorius's")
                    with h.random_neighbor_country() as n:
                        with n.limit() as t:
                            t.tfe_is_western_rome()
                        n.save_scope_as("tfe_victim")
                    with h.if_() as i:
                        with i.limit() as t, t.not_() as x:
                            x.exists("scope:tfe_victim")
                        with i.ordered_country(order_by="country_economical_base") as w:
                            with w.limit() as t:
                                t.tfe_is_western_rome()
                            w.save_scope_as("tfe_victim")
                    victim = "scope:tfe_victim"
                h.tfe_start_migration_effect()
                h.tail("scripted_effects/tfe_migratory.txt")
                h.declare_war_with_cb(target=victim, type="casus_belli:cb_tfe_migration")


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


def build():
    """(the category file, the decisions file); both share one localisation."""
    cats, doc = Doc(), Doc()
    doc.note("honorius-only: Stilicho's Claims is Honorius's (tools/test_western_rome.py)")
    cats.loc = doc.loc
    cats.note("TFE: the Fall of the West's decisions (decisions/tfe_fall_of_the_west.txt), near the top of the list.")
    cats.decision_category(CATEGORY, title="Fall of the West", sort_order=0)
    doc.note(HEADER)
    migrate(doc, "tfe_migrate_east", "EAR")
    migrate(doc, "tfe_migrate_west", "WRE")
    illyricum(doc)
    doc.loc.add("tfe_stilicho_serves_us_tt", "Stilicho lives and serves us")
    doc.loc.add("tfe_illyricum_claim_pressed_tt", "We have not pressed Stilicho's claim in the last ten years")
    return cats, doc


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    cats, doc = build()
    return {"in_game/common/decision_categories/tfe_decision_categories.txt": cats.text(),
            "in_game/common/decisions/tfe_fall_of_the_west.txt": doc.text(),
            "main_menu/localization/english/tfe_decisions_l_english.yml": doc.loc.text()}


if __name__ == "__main__":
    for rel, text in outputs().items():
        (Path(__file__).resolve().parent.parent / rel).write_text(text, encoding="utf-8-sig", newline="\n")
