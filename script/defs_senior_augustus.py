"""Seniority goes to the Augustus who has reigned longest (international_organization_special_statuses/tfe_roman_empire.txt)."""
import sys
from typing import Literal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import CountryFx, CountryTrig, InternationalOrganizationFx
from pdx.objects_defs import Defs

EMPIRE = "international_organization:tfe_roman_empire"
SENIOR = "special_status:tfe_senior_augustus"


def status(io: InternationalOrganizationFx, verb: Literal["add", "remove"], country: str):
    call = io.international_organization_add_special_status if verb == "add" else io.international_organization_remove_special_status
    call(type=SENIOR, country=country)


def on_actions():
    d = Defs()
    d.note("TFE: seniority goes to the Augustus who has reigned longest (international_organization_special_statuses/tfe_roman_empire.txt).")
    d.hook("on_game_start", "tfe_on_start_senior_augustus")
    d.note("Arcadius has been Augustus since 383, Honorius only since 393")
    with d.on_action("tfe_on_start_senior_augustus") as a:
        with a.effect(CountryFx) as e:
            with e.link(EMPIRE, InternationalOrganizationFx, op="?=") as io:
                status(io, "add", "c:EAR")
    d.hook("on_ruler_death", "tfe_on_ruler_death_seniority_passes")
    d.note("A new ruler has reigned shortest of all: the surviving Augustus becomes Senior")
    with d.on_action("tfe_on_ruler_death_seniority_passes") as a:
        with a.effect(CountryFx) as e:
            with e.if_() as i:
                with i.limit() as t:
                    t.has_special_status_in_international_organization(type=SENIOR, international_organization=EMPIRE)
                with i.link(EMPIRE, InternationalOrganizationFx) as io:
                    with io.random_international_organization_member() as m:
                        with m.limit() as t:
                            with t.not_() as n:
                                n.compare("this", "=", "root")
                        m.save_scope_as("tfe_new_senior")
                    with io.if_() as j:
                        with j.limit() as t:
                            t.exists("scope:tfe_new_senior")
                        status(j, "remove", "root")
                        status(j, "add", "scope:tfe_new_senior")
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/on_action/tfe_senior_augustus.txt": on_actions().text()}
