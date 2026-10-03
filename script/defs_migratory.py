"""tfe_migratory scripted effects and on_actions: a host takes to the road, is counted, and settles the land it wins."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx, CountryFx, CountryTrig, LocationFx, LocationTrig
from pdx.objects_defs import Defs

MIGRATION_CB = "casus_belli:cb_tfe_migration"
ROAD_LOCK_YEARS = 1   # pace the chaos: no AI host takes the road within this long of the last one


def create_units(loc, owner, origin, units):
    """`while = { count = n create_sub_unit_with_owner = {...} }` per (count, type) on loc."""
    for count, unit in units:
        with loc.while_(count=count) as w:
            w.create_sub_unit_with_owner(type=unit, owner=owner, origin=origin)


def raise_host(d: Defs):
    with d.effect("tfe_start_migration_effect", CountryFx) as e:
        e.save_scope_as("tfe_host")
        e.set_variable("tfe_migrating")
        e.note("pace the chaos: the AI's next host waits a year (the decisions' ai_will_do)")
        e.set_global_variable(name="tfe_host_took_the_road", value=True, years=ROAD_LOCK_YEARS)
        e.note("only the Vandals start army-based; a landed people would be gone with its last location (vanilla CHB, OIR)")
        with e.if_() as i:
            with i.limit() as t:
                with t.not_() as n:
                    n.country_type("army")
            i.change_country_type("army")
        e.tfe_muster_the_host_effect(True)
        e.tail("scripted_effects/tfe_barbarian_kingdoms.txt: 24 footmen and 8 tribal cavalry")
        e.note("a fifth of our people take the road; the rest stay under the new lords. Counted by pop_size, whatever its unit.")
        e.set_variable(name="tfe_host_people", value=0)
        e.tail("change_variable fails on an unset variable")
        with e.every_owned_location() as loc:
            with loc.every_pop() as p:
                with p.limit() as t:
                    t.compare("culture", "=", "scope:tfe_host.culture")  # a pop's culture is an event target, not a documented trigger
                p.save_temporary_scope_as("tfe_leaver")
                with p.link("scope:tfe_host", CountryFx) as host:
                    host.change_variable(name="tfe_host_people", add=dict(value="scope:tfe_leaver.pop_size", multiply=0.2))
                p.add_pop_size(value="pop_size", multiply=-0.2)
        e.note("the homeland is given up for good: the host keeps no core on it, nor on any land it won before")
        with e.every_core_location() as loc:
            loc.remove_core("scope:tfe_host")
        e.note("those who stayed make a country of the homeland, a tribe of the majority culture at the old capital, in the\n"
               "host's faith, holding every location the host leaves; no neighbour gets it. A host that owns no capital leaves\n"
               "nothing to hold: the land is abandoned. The remnant takes its name from the game's default for a new country.")
        with e.if_() as i:
            with i.limit() as t, t.go_capital(op="?=") as cap:
                cap.compare("owner", "=", "scope:tfe_host")
            with i.go_capital() as cap:
                cap.save_scope_as("tfe_old_capital")
                with cap.create_country_from_location() as c:
                    c.change_government_type("government_type:tribe")
                    c.tail("only counts after the effect block ends")
                    c.change_culture("scope:tfe_old_capital.dominant_culture")
                    c.change_religion("scope:tfe_host.religion")
                    c.set_variable(name="tfe_remnant_of", value="scope:tfe_host")
                    c.save_scope_as("tfe_remnant")
            with i.every_owned_location() as loc:
                loc.change_location_owner("scope:tfe_remnant")
                loc.add_core("scope:tfe_remnant")
        with e.else_() as i:
            with i.every_owned_location() as loc:
                with loc.link("scope:tfe_host", CountryFx) as host:
                    host.abandon_location("prev")
        with e.if_() as i:
            with i.limit() as t:
                t.country_exists("c:EAR")
            i.add_casus_belli(target="c:EAR", type=MIGRATION_CB)
        e.note("and on every western Rome: Stilicho's West too, once he rises")
        with e.every_country() as w:
            with w.limit() as t:
                t.tfe_is_western_rome()
            with w.link("scope:tfe_host", CountryFx) as host:
                host.add_casus_belli(target="prev", type=MIGRATION_CB)
        e.note("a settled host taking the road again is on the road once more: free, fed by Roman towns, settling anew")
        with e.if_() as i:
            i.limit(lambda t: t.has_variable("tfe_settled"))
            i.remove_variable("tfe_settled")
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
    d.note("TFE: a host takes to the road (the Migrate decisions, decisions/tfe_fall_of_the_west.txt; the Huns push\n"
           "the Germanic peoples west in events/tfe_hunnic_storm.txt). Scope: the migrating country. It becomes an army-based\n"
           "country, musters a great host, abandons its homeland and gets a casus belli on the Roman empires: a landless host\n"
           "has no neighbours for the game to offer one against. A fifth of its people go with it, to settle the land it wins\n"
           "(on_action/tfe_migratory.txt). Its passage over the land it leaves is Barbaricum's (international_organizations/).")
    raise_host(d)
    list_migrators(d)
    return d


def on_actions():
    d = Defs()
    d.note("TFE: the first land a migrating host (decisions/tfe_fall_of_the_west.txt) wins ends the migration. It becomes a\n"
           "landed country again, that land is its capital, and the great host disbands back to the warband it started with\n"
           "there; its free upkeep (auto_modifiers/tfe_migratory.txt) ends until it takes the road again. Its people settle\n"
           "the land it won.")
    d.hook("on_location_changed_owner", "tfe_on_host_settles")
    with d.on_action("tfe_on_host_settles") as a:
        with a.trigger(LocationTrig) as t:
            t.exists("scope:winner")
            with t.link("scope:winner", CountryTrig) as w:
                w.has_variable("tfe_migrating")
                with w.not_() as n:
                    n.has_variable("tfe_settled")
        with a.effect(LocationFx) as e:
            e.save_scope_as("tfe_homeland")
            with e.link("scope:winner", CountryFx) as w:
                w.set_variable("tfe_settled")
                w.tfe_list_the_migrators(True)
                w.tail("the Decline of the West's panel moves it to \"settled\" now, not next month")
                w.note("user: a settled host could not disband its troops. An army-based country lives by its armies, so the game\n"
                       "keeps them; vanilla's settling pirates and Timurids become landed countries (change_country_type).\n"
                       "User: in a peace deal its people settled anywhere but by the capital. The first land is both.")
                w.change_country_type("location")
                w.set_capital("scope:tfe_homeland")
                w.note("the host breaks up and its old warband (setup/395/27_armies.txt) re-forms at home, raised from it.\n"
                       "Whole armies go: destroying sub-units one by one crashed the game a tick later.")
                with w.every_army() as army:
                    army.destroy_unit(True)
            create_units(e, "scope:winner", "scope:tfe_homeland", ((4, "a_footmen"), (2, "a_tribal_cavalry")))
            e.note("the people who followed the host (tfe_host_people, counted by tfe_start_migration_effect) settle a day later,\n"
                   "once the whole peace or Hospitalitas has handed over its land, spread over all of it (events/tfe_barbarian_kingdoms.txt)")
            with e.link("scope:winner", CountryFx) as w:
                w.trigger_event_silently(id="tfe_barbarian_kingdoms.1", days=1)
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/scripted_effects/tfe_migratory.txt": effects().text(),
            "in_game/common/on_action/tfe_migratory.txt": on_actions().text()}
