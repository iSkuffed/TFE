"""tfe_migratory scripted effects and on_actions: a host takes to the road, is counted, and settles on its first land."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx, CountryFx, CountryTrig, LocationFx, LocationTrig
from pdx.objects_defs import Defs

MIGRATION_CB = "casus_belli:cb_tfe_migration"


def create_units(loc, owner, origin, units):
    """`while = { count = n create_sub_unit_with_owner = {...} }` per (count, type) on loc."""
    for count, unit in units:
        with loc.while_(count=count) as w:
            w.create_sub_unit_with_owner(type=unit, owner=owner, origin=origin)


def raise_host(d: Defs):
    with d.effect("tfe_start_migration_effect", CountryFx) as e:
        e.save_scope_as("tfe_host")
        e.set_variable("tfe_migrating")
        e.note("pace the chaos: the AI's next host waits 4 years (the action's ai_will_do)")
        e.set_global_variable(name="tfe_host_took_the_road", value=True, years=4)
        e.note("only the Vandals start army-based; a landed people would be gone with its last location (vanilla CHB, OIR)")
        with e.if_() as i:
            with i.limit() as t:
                with t.not_() as n:
                    n.country_type("army")
            i.change_country_type("army")
        with e.random_army() as a:
            with a.go_unit_location() as loc:
                loc.save_scope_as("tfe_muster")
        with e.if_() as i:
            with i.limit() as t:
                with t.not_() as n:
                    n.exists("scope:tfe_muster")
            i.tail("no warband afield: the host gathers at the capital")
            with i.go_capital(op="?=") as cap:
                cap.save_scope_as("tfe_muster")
        with e.link("scope:tfe_muster", LocationFx, op="?=") as muster:
            create_units(muster, "scope:tfe_host", "scope:tfe_muster", ((24, "a_footmen"), (8, "a_tribal_cavalry")))
        e.note("a fifth of our people take the road; the rest stay under the new lords. Counted by pop_size, whatever its unit.")
        e.set_variable(name="tfe_host_people", value=0)
        e.set_variable(name="tfe_host_plantings", value=0)
        e.tail("change_variable fails on an unset variable")
        with e.every_owned_location() as loc:
            with loc.every_pop() as p:
                with p.limit() as t:
                    t.compare("culture", "=", "scope:tfe_host.culture")  # a pop's culture is an event target, not a documented trigger
                p.save_temporary_scope_as("tfe_leaver")
                with p.link("scope:tfe_host", CountryFx) as host:
                    host.change_variable(name="tfe_host_people", add=dict(value="scope:tfe_leaver.pop_size", multiply=0.2))
                p.add_pop_size(value="pop_size", multiply=-0.2)
        e.note("a neighbouring people moves into the homeland, so it is not left empty; its pops stay, under new lords. Only with\n"
               "no such neighbour is it abandoned.")
        with e.random_neighbor_country() as n:
            with n.limit() as t:
                for tag in ("WRE", "EAR"):
                    with t.not_() as x:
                        x.tag(tag)
                with t.not_() as x:
                    x.has_variable("tfe_migrating")
            n.save_scope_as("tfe_heir_to_the_land")
        with e.if_() as i:
            with i.limit() as t:
                t.exists("scope:tfe_heir_to_the_land")
            with i.every_owned_location() as loc:
                loc.change_location_owner("scope:tfe_heir_to_the_land")
        with e.else_() as i:
            with i.every_owned_location() as loc:
                with loc.link("scope:tfe_host", CountryFx) as host:
                    host.abandon_location("prev")
        for tag in ("WRE", "EAR"):
            with e.if_() as i:
                with i.limit() as t:
                    t.country_exists(f"c:{tag}")
                i.add_casus_belli(target=f"c:{tag}", type=MIGRATION_CB)
        e.tfe_list_the_migrators(True)


def list_migrators(d: Defs):
    d.note("The Decline of the West's panel (gui/panels/situation/tfe_decline_of_the_west.gui) lists the migrators by state:\n"
           "at home, on the road (tfe_migrating), settled (tfe_settled). Any scope; the situation refreshes it monthly.")
    with d.effect("tfe_list_the_migrators", AnyFx) as e:
        with e.go_situation("tfe_decline_of_the_west") as s:
            for state in ("at_home", "on_the_road", "settled"):
                with s.if_() as i:
                    with i.limit() as t:
                        t.has_variable_list(f"tfe_migrators_{state}")
                    i.clear_variable_list(f"tfe_migrators_{state}")
        with e.every_country() as c:
            with c.limit() as t:
                t.tfe_is_migrator(True)
            c.save_scope_as("tfe_migrator")
            with c.go_situation("tfe_decline_of_the_west") as s:
                for branch, flag, state in ((s.if_, "tfe_settled", "settled"), (s.else_if, "tfe_migrating", "on_the_road")):
                    with branch() as i:
                        with i.limit() as t:
                            with t.link("scope:tfe_migrator", CountryTrig) as m:
                                m.has_variable(flag)
                        i.add_to_variable_list(name=f"tfe_migrators_{state}", target="scope:tfe_migrator")
                with s.else_() as i:
                    i.add_to_variable_list(name="tfe_migrators_at_home", target="scope:tfe_migrator")


def effects():
    d = Defs()
    d.note("TFE: a host takes to the road (generic_actions/tfe_migratory.txt, on the Decline of the West's panel; the Huns push\n"
           "the Germanic peoples west in events/tfe_hunnic_storm.txt). Scope: the migrating country. It becomes an army-based\n"
           "country, musters a great host, abandons its homeland and gets a casus belli on the Roman empires: a landless host\n"
           "has no neighbours for the game to offer one against. A fifth of its people go with it, to settle the land it wins\n"
           "(on_action/tfe_migratory.txt). Its passage over the land it leaves is Barbaricum's (international_organizations/).")
    raise_host(d)
    list_migrators(d)
    return d


def on_actions():
    d = Defs()
    d.note("TFE: the first land a migrating host (generic_actions/tfe_migratory.txt) wins ends the migration. The great host\n"
           "disbands back to the warband it started with; its free upkeep (auto_modifiers/tfe_migratory.txt) ends for good.\n"
           "Its people settle the land it wins, beside the locals (tfe_on_host_plants_its_people).")
    d.hook("on_location_changed_owner", "tfe_on_host_settles", "tfe_on_host_plants_its_people")
    with d.on_action("tfe_on_host_settles") as a:
        with a.trigger(LocationTrig) as t:
            t.exists("scope:winner")
            with t.link("scope:winner", CountryTrig) as w:
                w.has_variable("tfe_migrating")
                with w.not_() as n:
                    n.has_variable("tfe_settled")
        with a.effect(LocationFx) as e:
            with e.link("scope:winner", CountryFx) as w:
                w.set_variable("tfe_settled")
                w.tfe_list_the_migrators(True)
                w.tail("the Decline of the West's panel moves it to \"settled\" now, not next month")
                w.note("the host breaks up and its old warband (setup/start/27_armies.txt) re-forms where it stood. Whole armies\n"
                       "go: destroying sub-units one by one crashed the game a tick later.")
                with w.random_army() as army:
                    with army.go_unit_location() as loc:
                        loc.save_scope_as("tfe_warband_site")
                with w.every_army() as army:
                    army.destroy_unit(True)
                with w.link("scope:tfe_warband_site", LocationFx) as site:
                    create_units(site, "scope:winner", "scope:tfe_warband_site", ((4, "a_footmen"), (2, "a_tribal_cavalry")))
    d.note("The people who followed the host (tfe_host_people, counted by tfe_start_migration_effect) settle the first four\n"
           "locations it wins, a quarter in each, as peasants of its culture and faith. The same settlers are a majority in a\n"
           "thinly peopled countryside and a minority in a great city: the shift follows how many already live there.")
    with d.on_action("tfe_on_host_plants_its_people") as a:
        with a.trigger(LocationTrig) as t:
            t.exists("scope:winner")
            with t.link("scope:winner", CountryTrig) as w:
                w.has_variable("tfe_host_people")
        with a.effect(LocationFx) as e:
            e.add_pop(culture="scope:winner.culture", religion="scope:winner.religion", type="pop_type:peasants",
                    size=dict(value="scope:winner.var:tfe_host_people", multiply=0.25))
            with e.link("scope:winner", CountryFx) as w:
                w.change_variable(name="tfe_host_plantings", add=1)
                with w.if_() as i:
                    with i.limit() as t:
                        t.var("tfe_host_plantings", ">=", 4)
                    i.remove_variable("tfe_host_people")
                    i.remove_variable("tfe_host_plantings")
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/scripted_effects/tfe_migratory.txt": effects().text(),
            "in_game/common/on_action/tfe_migratory.txt": on_actions().text()}
