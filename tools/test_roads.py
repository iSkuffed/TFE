"""Roads: only lands that built roads in 395 have them, and the great Roman trunk roads are joined up."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

ROADS = b.MOD / "main_menu/setup/395/09_roads.txt"


def network():
    return re.findall(r"^\t(\w+) = (\w+)$", ROADS.read_text(encoding="utf-8"), re.M)


def component(edges, start):
    graph = {}
    for a, z in edges:
        graph.setdefault(a, set()).add(z)
        graph.setdefault(z, set()).add(a)
    seen, todo = {start}, [start]
    while todo:
        for n in graph.get(todo.pop(), ()):
            if n not in seen:
                seen.add(n)
                todo.append(n)
    return seen


def test_no_road_leaves_the_road_building_lands():
    owner = b.compute()["owner"]
    edges = network()
    assert len(edges) > 1000
    stray = [(a, z) for a, z in edges if not {owner.get(a), owner.get(z)} <= b.ROAD_BUILDERS]
    assert not stray, stray[:10]


def test_free_germania_scandinavia_ireland_and_the_steppe_have_no_roads():
    anc = b.load_hierarchy()
    regions = {"scandinavian_region", "ireland_region", "baltic_region", "russian_region", "ruthenia_region",
               "steppes_region"}
    inside = [(a, z) for a, z in network() if regions & {*anc[a], *anc[z]}]
    assert not inside, inside[:10]


def test_the_trunk_roads_of_the_empire_run_end_to_end():
    edges = network()
    adjacency = b.load_adjacency()
    ferries = {("constantinople", "izmit")}
    assert [(a, z) for a, z in edges if z not in adjacency[a] and (a, z) not in ferries] == []
    for a, z in ferries:
        assert (a, z) in edges
    west = component(edges, "rome")
    assert {"brindisi", "milano", "genoa", "arles", "lyon", "reims", "tarragona", "cordoba", "aquileia"} <= west
    balkans = component(edges, "durres")   # the Via Egnatia to the New Rome, then the Anatolian road on to Syria
    assert {"thessaloniki", "edirne", "constantinople", "izmit", "ankara", "tarsus", "antioch", "aleppo"} <= balkans
    assert {"belgrad", "nis", "sredets", "plovdiv"} <= balkans
    assert {"london", "york", "lincoln", "exeter"} <= component(edges, "london")
    assert {"damascus", "gaza", "cairo", "alexandria"} <= component(edges, "antioch") | component(edges, "cairo")
