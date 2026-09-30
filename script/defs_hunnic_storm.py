"""The Hunnic Storm: two scripted triggers and the on_actions that start it and call its Reckoning."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx, AnyTrig, CountryFx, CountryTrig, InternationalOrganizationFx
from pdx.objects_defs import Defs


def triggers():
    d = Defs()
    d.note("TFE: the Hunnic Storm is over (situations/tfe_hunnic_storm.txt, in its scope). can_end alone is checked too\n"
           "rarely, so the situation's on_monthly also ends it by this.")
    with d.trigger("tfe_hunnic_storm_is_over", AnyTrig) as t:
        with t.or_() as o:
            with o.custom_tooltip_block("tfe_storm_resolved_tt") as c:
                c.has_variable("tfe_storm_resolved")
            with o.not_() as n:
                n.country_exists("c:HNS")
            o.current_date("480.1.1", op=">=")
            o.note("the Yoke fell apart before the Reckoning: nothing is left to break (in the Reckoning on_monthly resolves it)")
            with o.custom_tooltip_block("tfe_storm_yoke_gone_tt") as c:
                c.var("tfe_storm_phase", "<", 3)
                with c.not_() as n:
                    n.exists("international_organization:tfe_hunnic_yoke")
    d.note("A people under the Huns' hand (scope: country): a member of the Yoke, or a tributary of the Huns themselves.\n"
           "The starting tribes are tributaries, not members: the Yoke's tribute is only for those the Huns beat into it.")
    with d.trigger("tfe_is_under_the_yoke", CountryTrig) as t:
        with t.or_() as o:
            o.is_member_of_international_organization("international_organization:tfe_hunnic_yoke")
            with o.and_() as a:
                a.is_subject_type("tributary")
                with a.go_top_overlord(op="?=") as top:
                    top.tag("HNS")
    return d


def on_actions():
    d = Defs()
    d.note("TFE: the Hunnic Storm (situations/tfe_hunnic_storm.txt) begins on day one, with the Huns at the head of their Yoke.")
    d.hook("on_game_start", "tfe_on_start_hunnic_storm")
    with d.on_action("tfe_on_start_hunnic_storm") as a:
        with a.effect(AnyFx) as e:
            with e.link("international_organization:tfe_hunnic_yoke", InternationalOrganizationFx, op="?=") as io:
                io.set_leader_country("c:HNS")
            with e.if_() as i:
                with i.limit() as t:
                    t.country_exists("c:HNS")
                i.activate_situation("situation:tfe_hunnic_storm")
    d.hook("on_ruler_death", "tfe_on_ruler_death_reckoning_due")
    d.note("The fallback Reckoning: any Hunnic ruler's death after 10 years of the Scourge phase (the situation opens it monthly)")
    with d.on_action("tfe_on_ruler_death_reckoning_due") as a:
        with a.trigger(CountryTrig) as t:
            t.tag("HNS")
            with t.go_situation("tfe_hunnic_storm") as s:
                s.situation_is_active(True)
                s.var("tfe_storm_phase", "=", 2)
                with s.not_() as n:
                    n.has_variable("tfe_scourge_clock")
        with a.effect(CountryFx) as e:
            with e.go_situation("tfe_hunnic_storm") as s:
                s.set_variable(name="tfe_reckoning_due", value=True)
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/scripted_triggers/tfe_hunnic_storm.txt": triggers().text(),
            "in_game/common/on_action/tfe_hunnic_storm.txt": on_actions().text()}
