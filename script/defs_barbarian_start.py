"""The peoples beyond the limes open hungry: every migrator holds the tribal privileges, the Huns lean on decentralisation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx, CountryFx
from pdx.objects_defs import Defs

# vanilla in_game/common/estate_privileges/: the warband's keys, one or two per estate
PRIVILEGES = [
    "peasants_allowed_weapons_privilege", "peasants_in_administration", "peasants_free_peasantry",
    "tribes_tribal_registry", "tribes_tribal_levies", "tribes_allow_gatherings",
    "auxilium_et_consilium", "nobles_offensive_military_doctrine", "nobles_land_rights",
    "formal_guilds", "market_fairs",
    "clergy_in_administration", "expansionist_zealotry", "clergy_land_rights",
]
HORDE_DECENTRALISATION = 80   # positive is Decentralization on the centralization_vs_decentralization axis


def on_actions():
    d = Defs()
    d.note("TFE: a barbarian state in 395 is a host with every estate already armed and privileged, not a village waiting on reforms.\n"
           "Each privilege is tested first, so one a state already holds is not granted twice. The Hunnic Horde opens decentralised.")
    d.hook("on_game_start", "tfe_on_start_barbarians")
    with d.on_action("tfe_on_start_barbarians") as a:
        with a.effect(AnyFx) as e:
            with e.every_country() as c:
                with c.limit() as t:
                    t.tfe_is_migrator(True)
                for p in PRIVILEGES:
                    with c.if_() as i:
                        with i.limit() as t, t.not_() as n:
                            n.has_estate_privilege(f"estate_privilege:{p}")
                        i.grant_estate_privilege(f"estate_privilege:{p}")
            with e.link("c:HNS", CountryFx, op="?=") as h:
                h.set_societal_value(type="centralization_vs_decentralization", value=HORDE_DECENTRALISATION)
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/on_action/tfe_barbarian_start.txt": on_actions().text()}
