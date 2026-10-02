"""The West starts with its two Italian fleets: 30 transports and 5 galleys."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from pdx.api import AnyFx, CountryTrig, LocationFx
from pdx.objects_defs import Defs

# Notitia Dignitatum Occ. 42: the classis Ravennas and the classis Misenatium, the praetorian fleets of Italy. In 395
# they carry armies rather than fight: Mascezel sails against Gildo in 398 in their transports.
# {port: (transports, galleys)}, vanilla's age-1 types (unit_types/navy_transport.txt, navy_galley.txt)
FLEETS = {"ravenna": (18, 3), "naples": (12, 2)}   # Misenum is on the bay of Naples


def on_actions():
    d = Defs()
    d.note("TFE: the West's fleets of Ravenna and Misenum: 30 transports and 5 galleys on day one.")
    d.hook("on_game_start", "tfe_on_start_western_fleet")
    with d.on_action("tfe_on_start_western_fleet") as a:
        with a.effect(AnyFx) as e:
            e.note("create_sub_unit one at a time: create_num_sub_unit = { count type } silently makes nothing. The ships\n"
                   "made at one port gather into one fleet there, for its owner, beside the 13 the game gives the West at Rome.")
            for port, (transports, galleys) in FLEETS.items():
                with e.link(f"location:{port}", LocationFx) as loc, loc.if_() as f:
                    with f.limit() as t, t.link("owner", CountryTrig, op="?=") as o:
                        o.tfe_is_western_rome(True)
                    for n, kind in ((transports, "n_cog"), (galleys, "n_traditional_galley")):
                        with f.while_(count=n) as w:
                            w.create_sub_unit(f"unit_type:{kind}")
    return d


def outputs():
    """{repo-relative path: text}; write each with encoding="utf-8-sig" (the BOM is the writer's job)."""
    return {"in_game/common/on_action/tfe_western_fleet.txt": on_actions().text()}
