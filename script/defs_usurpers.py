"""Usurpers who carve a country out of the West's land: Constantine III in Britain (tfe_opening.5, and when Stilicho
rises) and the diocese of Africa (when Stilicho rises and Gildo's kingdom is gone). Scope: WRE; root names the West."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryFx, LocationFx, RebelsFx
from pdx.objects_defs import Defs


def crown(c: CountryFx, tag, name, color, rank, rank_note, **ruler):
    """this country becomes a usurper's: its tag, name, flag, rank, ruler and gold; at war with nobody yet."""
    c.define_unique_country_tag(tag)
    c.change_country_name(name)
    c.change_country_adjective(f"{name}_ADJ")
    c.change_country_color(color)
    c.change_country_flag(name)
    c.set_country_rank(f"country_rank:{rank}")
    c.tail(rank_note)
    c.change_government_type("government_type:monarchy")
    c.add_gold(200)
    c.create_character(culture="culture:roman_culture", religion="religion:orthodox",
                       estate="estate_type:nobles_estate", **ruler, save_scope_as="tfe_usurper_ruler")
    c.set_new_ruler("scope:tfe_usurper_ruler")
    c.set_variable(name="tfe_usurper_against", value="root", years=10)
    c.save_scope_as("tfe_usurper")


def new_country(loc: LocationFx, tag, name, color, rank, rank_note, **ruler):
    """a usurper's country out of this location, at war with nobody yet; its flag is named like its name key."""
    with loc.create_country_from_location() as c:
        crown(c, tag, name, color, rank, rank_note, **ruler)


def region_goes_to_the_usurper(e: CountryFx, region):
    with e.every_owned_location() as loc:
        with loc.limit() as t:
            t.compare("region", "=", f"region:{region}")
        loc.change_location_owner("scope:tfe_usurper")


def crown_constantine(i: CountryFx):
    """tfe_opening.9's immediate (root: the West): the revolt's revolter becomes Constantine's empire and takes Britain."""
    i.note("marked by tfe_constantine_rises the moment the revolt started: it may come out landless")
    with i.random_country() as c:
        with c.limit() as t:
            t.has_variable("tfe_constantine_revolter")
        c.save_scope_as("tfe_usurper")
    with i.link("scope:tfe_usurper", CountryFx, op="?=") as u:
        crown(u, "CONST", "TFE_CONSTANTINE", "map_lombard", "rank_empire", "an Augustus, whatever Ravenna says",
              first_name="name_constantine", age=40, mil=55)
        u.remove_variable("tfe_constantine_revolter")
        u.note("a neighbour backing the revolt would lead the rebel side, and Annex Revolter then only offers a white peace:\n"
               "send the backers home")
        with u.every_current_war() as war:
            war.limit(lambda t: t.is_in_war("root"))
            war.save_scope_as("tfe_constantine_war")
            with war.every_war_participant() as p:
                with p.limit() as t:
                    t.is_at_war_with("root")
                    t.not_(lambda n: n.compare("this", "=", "scope:tfe_usurper"))
                    t.note("only backers, which hold land beyond Britain: sending home another rebel country the revolt\n"
                           "split off ends the whole war (Gildo's, user in game)")
                    with t.any_owned_location() as o, o.not_() as n:
                        n.compare("region", "=", "region:great_britain_region")
                p.leave_war(war="scope:tfe_constantine_war", actor="root")
        u.note("the revolt system makes the revolter a Secessionist subject of any backer: he is his own master")
        with u.if_() as f:
            f.limit(lambda t: t.is_subject(True))
            with f.go_overlord() as lord:
                lord.cancel_subject("prev")
    with i.if_() as f:
        f.limit(lambda t: t.exists("scope:tfe_usurper"))
        region_goes_to_the_usurper(f, "great_britain_region")
        f.link("scope:tfe_usurper", CountryFx, lambda u: u.set_capital("location:london"))
        f.set_variable(name="tfe_usurper", value="scope:tfe_usurper", years=10)


def effects():
    d = Defs()
    d.note("TFE: Britain's army crowns a common soldier for his name (early 407, tfe_opening.5; or when Stilicho rises).\n"
           "A revolt, not a gift of land, as Gildo's was: the West is at war with the revolter at once, and the war screen's\n"
           "Annex Revolter takes Britain back. tfe_opening.9 makes the revolter Constantine's empire in the same moment.")
    with d.effect("tfe_constantine_rises", CountryFx) as e:
        e.create_rebel(category="nationalist", name="tfe_constantine_rebels", culture="culture:roman_culture",
                       religion="religion:orthodox", save_scope_as="tfe_constantine_rebels")
        with e.every_owned_location() as loc:
            with loc.limit() as t:
                t.compare("region", "=", "region:great_britain_region")
            with loc.every_pop() as p:
                p.change_pop_allegiance("scope:tfe_constantine_rebels")
        e.note("the wars we are in already (a host, Gildo, Stilicho's revolt) are not his: mark them, then find the new one")
        with e.every_country() as c:
            with c.limit() as t:
                t.is_at_war_with("root")
            c.set_variable("tfe_old_enemy")
        e.link("scope:tfe_constantine_rebels", RebelsFx, lambda r: r.start_revolt(True), op="?=")
        with e.random_country() as c:
            with c.limit() as t:
                t.is_at_war_with("root")
                t.not_(lambda n: n.has_variable("tfe_old_enemy"))
                t.note("no backer: the revolter holds nothing beyond Britain, or nothing at all")
                with t.not_() as n, n.any_owned_location() as o, o.not_() as m:
                    m.compare("region", "=", "region:great_britain_region")
            c.set_variable("tfe_constantine_revolter")
        with e.every_country() as c:
            with c.limit() as t:
                t.has_variable("tfe_old_enemy")
            c.remove_variable("tfe_old_enemy")
        e.trigger_event_silently("tfe_opening.9")
    d.note("the diocese of Africa goes its own way under a Roman count, when Stilicho rises and Gildo's kingdom is gone")
    with d.effect("tfe_africa_breaks_away", CountryFx) as e:
        with e.random_owned_location() as loc:
            with loc.limit() as t:
                t.compare("region", "=", "region:maghreb_region")
            new_country(loc, "AFRIC", "TFE_AFRICA", "map_kado", "rank_kingdom", "a count of Africa, not an Augustus",
                        age=50, adm=50, mil=45)
        region_goes_to_the_usurper(e, "maghreb_region")
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/scripted_effects/tfe_usurpers.txt": effects().text()}
