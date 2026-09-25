"""Frontier facts for 395 AD. Each row: location, expected owner, why."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

WEST = [
    ("trier", "WRE", "Augusta Treverorum, left bank of the Rhine"),
    ("cologne", "WRE", "Colonia Agrippina, left bank"),
    ("dusseldorf", "FRK", "right bank opposite Cologne: Franks"),
    ("heidelberg", "ALM", "right bank of the upper Rhine: Alamanni"),
    ("mainz", "WRE", "Moguntiacum"),
    ("augsburg", "WRE", "Augusta Vindelicum, Raetia II"),
    ("ulm", "ALM", "north of the Danube-Iller-Rhine limes"),
    ("regensburg", "WRE", "Castra Regina, south bank"),
    ("vienna", "WRE", "Vindobona"),
    ("krems", "QAD", "north bank of the Danube: Marcomanni/Quadi"),
    ("antwerp", "SLF", "Toxandria, Salian foederati since 358"),
    ("newcastle", "WRE", "Pons Aelius on Hadrian's Wall"),
    ("alnwick", "VOT", "north of the Wall: Votadini"),
    ("edinburgh", "VOT", "Votadini (Din Eidyn)"),
    ("perth", "PKT", "Picts"),
    ("navan", "LAI", "Leinster area (Tara is beside Navan; game tara is Siberian); Uí Néill claims deferred"),
    ("sremska_mitrovica", "WRE", "Sirmium, Pannonia II"),
    ("belgrad", "EAR", "Singidunum, Moesia I (diocese of Dacia)"),
    ("shkoder", "EAR", "Scodra, Praevalitana"),
    ("split", "WRE", "Salona, Dalmatia"),
    ("tangier", "WRE", "Tingis, Mauretania Tingitana"),
    ("rabat", "WRE", "Sala, held to the 5th c."),
    ("fez", "BAQ", "interior beyond the reduced Tingitana"),
    ("cherchell", "WRE", "Caesarea, Mauretania Caesariensis"),
    ("setif", "WRE", "Sitifis"),
    ("tripoli", "WRE", "Oea, Tripolitania"),
    ("murzuk", "GMT", "Garamantes, Fezzan"),
    ("uppsala", "SVE", "Svear"),
]


@pytest.fixture(scope="module")
def state():
    return b.compute()


@pytest.mark.parametrize("loc,tag,why", WEST)
def test_west(state, loc, tag, why):
    assert state["owner"].get(loc) == tag, f"{loc}: {why}; trail {state['trail'].get(loc)}"


def test_no_errors(state):
    assert state["errors"] == []
