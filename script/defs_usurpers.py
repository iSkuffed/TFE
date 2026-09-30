"""Usurpers who carve a country out of the West's land: Constantine III in Britain (tfe_opening.5, and when Stilicho
rises) and the diocese of Africa (when Stilicho rises and Gildo's kingdom is gone). Scope: WRE; root names the West."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryFx, LocationFx
from pdx.objects_defs import Defs


def new_country(loc: LocationFx, tag, name, color, rank, rank_note, **ruler):
    """a usurper's country out of this location, at war with nobody yet; its flag is named like its name key."""
    with loc.create_country_from_location() as c:
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


def region_goes_to_the_usurper(e: CountryFx, region):
    with e.every_owned_location() as loc:
        with loc.limit() as t:
            t.compare("region", "=", f"region:{region}")
        loc.change_location_owner("scope:tfe_usurper")


def effects():
    d = Defs()
    d.note("TFE: Britain's army crowns a common soldier for his name (early 407, tfe_opening.5; or when Stilicho rises)")
    with d.effect("tfe_constantine_rises", CountryFx) as e:
        with e.link("location:london", LocationFx) as loc:
            new_country(loc, "CONST", "TFE_CONSTANTINE", "map_lombard", "rank_empire", "an Augustus, whatever Ravenna says",
                        first_name="name_constantine", age=40, mil=55)
        region_goes_to_the_usurper(e, "great_britain_region")
        e.set_variable(name="tfe_usurper", value="scope:tfe_usurper", years=10)
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
