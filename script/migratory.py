"""tfe_migratory generic actions: one button per empire, and the two differ only in the empire."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryFx, CountryTrig, ValueFx
from pdx.objects import Doc

ACTOR = "scope:actor"
HEADER = """TFE: migratory peoples. A people of Germania or Dacia (tfe_is_migrator) may once give up its homeland, from the
Decline of the West's panel (situations/tfe_decline_of_the_west.txt), for a great host that costs nothing while it
owns no land (auto_modifiers/tfe_migratory.txt). It cannot replenish: landless, it has no manpower, so every warrior
lost is gone until it wins land of its own. One button per empire: the host marches on the East or the West at once,
and that Augustus may buy it off with land (Hospitalitas, generic_actions/tfe_decline_rome.txt). The two differ only
in the empire."""


def migrate(doc, name, tag):
    with doc.entry(name) as a:
        a.field("type", "situation")
        a.field("icon", "migrate_pop_based_country")
        with a.triggers("potential") as t:
            with t.go_situation("tfe_decline_of_the_west") as s:
                s.situation_is_active(True)
            with t.link(ACTOR, CountryTrig) as c:
                c.tfe_is_migrator()
                with c.not_() as n:
                    n.has_variable("tfe_migrating")
            t.country_exists(f"c:{tag}")
        with a.triggers("allow") as t:
            with t.custom_tooltip_block("tfe_migration_not_yet_tt") as ct:
                ct.current_date("395.2.18", op=">=")
                ct.tail("a month after the game starts (defines' START_DATE)")
            with t.link(ACTOR, CountryTrig) as c:
                c.is_subject(False)
                c.tail("no warband afield is fine: the host gathers at the capital")
                c.tfe_frontier_unmanned()
                c.tail("scripted_triggers/tfe_decline_rome.txt: a manned frontier holds them")
        a.field("ai_tick", "monthly")
        a.field("ai_tick_frequency", 12)
        a.field("automation_tick", "never")
        a.field("automation_tick_frequency", 12)
        # only raw block: its schema (looking_for_a, columns, source lists) belongs to an objects.py GenericAction builder
        a.raw("""select_trigger = {
            looking_for_a = situation
            interaction_source_list = { situation:tfe_decline_of_the_west = { add_to_list = source } }
            target_flag = recipient
            name = "choose_situation"
            column = { data = name }
            visible = { situation:tfe_decline_of_the_west = this situation_is_active = yes }
        }""")
        with a.effects("effect") as e:
            e.custom_tooltip("tfe_start_migration_tt")
            e.custom_tooltip(f"tfe_migrate_{tag}_tt")
            with e.hidden_effect() as h:
                with h.link(ACTOR, CountryFx) as c:
                    c.tfe_start_migration_effect()
                    c.tail("scripted_effects/tfe_migratory.txt")
                    c.declare_war_with_cb(target=f"c:{tag}", type="casus_belli:cb_tfe_migration")
        a.note("Pace the chaos: one AI people on the road at a time. None moves within 4 years of the last host setting out\n"
               "(tfe_host_took_the_road), and then only when pushed: the Huns at the door or Rome divided.")
        with a.effects("ai_will_do", ValueFx) as v:
            v.value(0)
            with v.if_() as i:
                with i.limit() as t:
                    with t.not_() as n:
                        n.has_global_variable("tfe_host_took_the_road")
                    with t.link(ACTOR, CountryTrig) as c:
                        c.at_war(False)
                i.add(5)
                with i.if_() as j:
                    with j.limit() as t:
                        with t.link(ACTOR, CountryTrig) as c:
                            with c.any_neighbor_country() as n:
                                n.tfe_is_under_the_yoke()
                    j.add(45)
                i.note("the empire across the river first")
                with i.if_() as j:
                    with j.limit() as t:
                        with t.link(ACTOR, CountryTrig) as c:
                            with c.any_neighbor_country() as n:
                                n.tag(tag)
                    j.add(10)
                with i.if_() as j:
                    with j.limit() as t:
                        with t.go_international_organization_data("tfe_roman_empire", op="?=") as io:
                            io.var("tfe_unity", "<", 50)
                    j.add(25)


def build():
    doc = Doc()
    doc.note(HEADER)
    migrate(doc, "tfe_migrate_east", "EAR")
    migrate(doc, "tfe_migrate_west", "WRE")
    return doc


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/generic_actions/tfe_migratory.txt": build().text()}


if __name__ == "__main__":
    for rel, text in outputs().items():
        (Path(__file__).resolve().parent.parent / rel).write_text(text, encoding="utf-8-sig", newline="\n")
