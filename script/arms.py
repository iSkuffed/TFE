"""Arms of antiquity: no gunpowder in 395-895.

Units that bought firearms buy weaponry instead (both cost 3, summed one for one, so nothing gets dearer), cannons are
Siege Equipment, every out-of-period unit takes a late-antique name (stats and models untouched), and the top road
keeps its numbers but wears the stone road's look as the Via Publica. Vanilla is read each run, so an EU5 patch is one
`python script/run.py`. The firearms buildings are cut in script/advances.py (see the Part 2 block there).
"""
import functools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import borders as b  # noqa: E402  (b.GAME: vanilla's game folder)
from lint_script import parse  # noqa: E402
from pdx.core import Node, from_entries, render  # noqa: E402

DEMANDS = "in_game/common/goods_demand"
METHODS = "in_game/common/production_methods"  # standalone inputs (barracks, garrisons...)
BUILDINGS = "in_game/common/building_types"    # inline inputs (armory, forts...): the whole building is replaced
FOLDERS = (DEMANDS, METHODS, BUILDINGS)
ROAD_TYPES = "in_game/common/road_types"
GOODS = "in_game/common/goods"
# Goods no road can use in 395-895 (steel needs a steel mill, which is a ruler of the 800s at the earliest), and what pays for
# them instead: each good takes its share of the value at vanilla prices, so a road costs the same in gold-equivalent.
LATE_GOODS: dict[str, dict[str, float]] = {"steel": {"stone": 0.4, "iron": 0.6}}
SKIP_DEMANDS = {"from_events.txt"}  # 1337 events that never fire
OUT_ROADS = "in_game/common/road_types/tfe_roads.txt"
LOC = "main_menu/localization/english/replace/tfe_arms_l_english.yml"

# name, description. Keys are vanilla unit types; stats and models stay. Levy and base variants that read `$parent$`
# follow their parent and are not listed. Units whose name already fits the period (Footmen, Archers, Legionaries,
# elephants, camel tiers 1-3 and 5, African, steppe and American units...) are left alone.
UNITS: dict[str, tuple[str, str]] = {
    # --- foot: the gunpowder line
    "a_handgonners": ("Plumbatarii", "Foot soldiers who hurl weighted darts in a storm before the lines meet, as the legions of Illyricum did."),
    "a_early_arquebusiers": ("Sagittarii", "Archers drawn up behind a screen of spearmen, who loose volley after volley over their heads."),
    "a_arquebusiers": ("Heavy Sagittarii", "A drilled corps of archers sheltered by a wall of armoured spearmen: a formidable body that cannot be easily countered."),
    "a_musketeers": ("Scutati", "Shield-bearers in close order, who hold the line with spear and sword and break the enemy's charge."),
    "a_fusiliers": ("Heavy Scutati", "Veteran shield-bearers in mail, trained to march and strike as one body."),
    "a_grenadiers": ("Plumbatarii Veterani", "Picked men who throw their darts furthest and hardest, and lead the assault on a breach."),
    "a_hunters": ("Exculcatores", "Skirmishers who scout ahead of the army and harass the enemy from cover."),
    "a_sharpshooters": ("Heavy Exculcatores", "Skirmishers chosen for their eye, who pick off officers and gunners, slingers and archers at a distance."),
    "a_men_at_arms": ("Armoured Foot", "Heavy infantry in mail and helmet who stand in the line with spear and sword."),
    "a_halberdiers": ("Axemen", "Infantry with long-hafted axes, who cut through shields and armour and drag riders from the saddle."),
    "a_pikemen": ("Lanciarii", "Foot soldiers with long spears who stand against cavalry in a dense, bristling line."),
    "a_matchlock_levy": ("Javelin Levy", "Levies armed with javelins and little else, who hurl them at the enemy and run."),
    "a_flintlock_levy": ("Heavy Levy", "Levies with spear and shield, drilled enough to stand in a battle line."),
    "a_conscripts": ("Tirones", "Recruits levied by law, who serve for the campaign under the standards of the army."),
    # --- horse
    "a_pistoleers": ("Cataphracti", "Horsemen in scale armour on armoured horses, who charge with lance and mace."),
    "a_cuirassiers": ("Clibanarii", "The heaviest horse: riders and mounts sheathed in iron, who ride down infantry."),
    "a_light_dragoons": ("Equites Sagittarii", "Light horse who shoot from the saddle and fall back, and ride down a broken enemy."),
    "a_hussars": ("Illyriciani", "Light horse raised in Illyricum, quick to scout and to raid."),
    "a_gallop_cavalry": ("Equites Mauri", "Moorish riders who gallop at the enemy with javelins and swing away."),
    "a_gendarmerie": ("Scholae", "Household horsemen of the palace, picked from the best families and paid to stand before the emperor."),
    "a_late_cavaliers": ("Late Equites", "Mounted gentlemen in good armour, who fight as the army's horse."),
    "a_cavaliers": ("Equites", "Mounted gentlemen who serve with their own horses and arms."),
    "a_plated_knights": ("Plated Horse", "Heavy horse in plate over mail, the strongest charge the age knows."),
    "a_mailed_knights": ("Mailed Horse", "Horse in mail and helmet, who fight with lance and sword."),
    "a_order_knights": ("Sacred Horse", "Horsemen sworn to defend the faith and its shrines, who fight with a zeal that others lack."),
    "a_order_knights_2": ("Holy Horse", "A sworn brotherhood of heavy horse, who answer to their master and to the Church."),
    "a_winged_hussars": ("Winged Cataphracts", "Heavy lancers with wings of feathers on their backs, who thunder through the enemy line."),
    "a_late_winged_hussars": ("Late Winged Cataphracts", "Heavy lancers, now better armed and drilled, whose charge breaks any line."),
    "a_banner_cavalry": ("Vexillation Cavalry", "Horse of the standing detachments, who ride under their own banners."),
    "a_hungarian_hussars": ("Pannonian Light Horse", "Light horse of the Pannonian plain, wheeling and skirmishing from a distance."),
    "a_serbian_hussars": ("Balkan Light Horse", "Light horse of the Balkan hills, quick on any ground."),
    "a_austrian_grenzhussar": ("Border Light Horse", "Light horse raised from the border colonists, who patrol the frontier and raid beyond it."),
    "a_hakkapelitta": ("Northern Horse", "Horsemen of the north, who charge fast and hit hard with the sword."),
    "a_lanzas_de_castilla": ("Iberian Lancers", "Lancers of the Iberian plateau, who fight with lance and javelin."),
    "a_akinji": ("Border Raiders", "Irregular horse who raid ahead of the army and burn the enemy's fields."),
    "a_muslim_riders_vijay": ("Armoured Riders", "Mounted spearmen and swordsmen in mail, who serve the rulers of the south."),
    "a_light_jurchen_cavalry": ("Light Steppe Cavalry", "Light horse of the northern steppe, who shoot from the saddle."),
    "a_iron_pagoda_cavalry": ("Iron Cavalry", "Heavy horse in iron armour from head to hoof."),
    "a_light_camelry_4": ("Camel Skirmishers", "Riders on camels who throw javelins and wheel away across the sand."),
    "a_light_camelry_6": ("Dromedarii", "Camel-borne troops, as the Roman army has long raised on the desert frontier."),
    "a_heavy_camelry_6": ("Camel Cataphracts", "Armoured riders on armoured camels, who charge through the enemy line."),
    # --- siege engines
    "a_houfnice": ("Onagri", "Torsion catapults that hurl stones at walls and massed ranks."),
    "a_chambered_cannon": ("Ballistae", "Great bolt-throwers that shoot heavy bolts to break men and walls."),
    "a_falconet": ("Carroballistae", "Light bolt-throwers on carts, which move with the army and shoot on the march."),
    "a_royal_mortar": ("Heavy Onagri", "The largest catapults, which throw great stones high over the walls."),
    "a_flying_battery": ("Mobile Ballistae", "Bolt-throwers on light carts that follow the army and are set up in a moment."),
    "a_red_cannon": ("Great Onager", "A huge engine of a famous founder, which brings down towers with a single stone."),
    "a_cetbang_cannon": ("Scorpiones", "Small bolt-throwers carried by the army, which pick off men on the walls."),
    "a_byz_helepolis_cannon_unit": ("Helepolis", "A great tower of timber on wheels, from which engines and archers command the wall."),
    "a_hwacha": ("Polybolos", "A repeating bolt-thrower that shoots a rain of bolts one after another."),
    # --- uniques of the later ages and of other lands
    "a_feudal_levy": ("Provincial Levies", "Farmers and herders raised by the local lord, who bring what weapons they have."),
    "a_crusader_knights": ("Holy Spearmen", "Spearmen sworn to the defence of the faith, who stand in the line beside the horse."),
    "a_late_crusader_knights": ("Veteran Holy Spearmen", "Seasoned spearmen of a sworn brotherhood, who have stood in many a battle."),
    "a_schiltron": ("Spear Circle", "Spearmen in a tight ring, spears levelled outward, who hold against any charge."),
    "a_almogavars": ("Hill Skirmishers", "Hardy highlanders who fight with javelins and short swords and fear no horse."),
    "a_late_almogavars": ("Veteran Hill Skirmishers", "Highlanders grown into a corps, whose assault wins battles."),
    "a_catalan_crossbowmen": ("Western Crossbowmen", "Crossbowmen of the western coasts, who shoot from behind their shields."),
    "a_navarrese_crossbowmen": ("Pyrenean Crossbowmen", "Crossbowmen of the Pyrenean valleys, who ambush from the passes."),
    "a_genoese_crossbowmen": ("Italian Crossbowmen", "Professional crossbowmen of the Italian ports, hired by every prince."),
    "a_early_longbowmen": ("War Archers", "Archers with heavy bows, who shoot down charging horse at long range."),
    "a_longbowmen": ("Heavy War Archers", "Archers with the great bow, whose arrows pierce even mail."),
    "a_late_longbowmen": ("Veteran War Archers", "Seasoned archers, who loose volleys that darken the sky."),
    "a_hobelars": ("Light Horse", "Light horsemen on small nimble ponies, used to scout and to raid."),
    "a_gallowglass": ("Axe Warriors", "Heavy axe-bearing mercenaries, who fight in mail and hold the line."),
    "a_reformed_gallowglass": ("Veteran Axe Warriors", "Axe-bearing warriors, drilled into a standing body."),
    "a_late_gallowglass": ("Elite Axe Warriors", "The pick of the axe-bearers, who break shield-walls and break them again."),
    "a_wagenburg": ("Carrago", "A ring of wagons, behind which archers and spearmen shelter, as the peoples of the steppe have long done."),
    "a_byzantine_cataphracts": ("Roman Cataphracts", "Heavily armoured horsemen of the eastern army, who charge in a wedge behind their lances."),
    "a_byzantine_cataphracts_2": ("Late Roman Cataphracts", "Armoured horsemen with lance and bow, the shock troops of the eastern army."),
    "a_varangians": ("Excubitors", "Guards of the palace, chosen for their size and loyalty."),
    "a_varangians_2": ("Veteran Excubitors", "Palace guards who have seen the emperor's wars."),
    "a_varangians_3": ("Axe-Bearing Excubitors", "Palace guards who carry the heavy axe, to cut through any line."),
    "a_varangians_4": ("Heavy Excubitors", "Guards in mail and helmet, who fight beside the emperor."),
    "a_varangians_5": ("Imperial Excubitors", "The emperor's own guard, drilled to a fine edge."),
    "a_varangians_6": ("Imperial Excubitor Guard", "The finest guard in the world, armed and paid beyond all others."),
    "a_hafsid_ghulam": ("Ifriqiyan Ghulam", "Slave-soldiers of the African governors, loyal to their master alone."),
    "a_zayyanid_ghulam": ("Maghribi Ghulam", "Slave-soldiers of the western governors, bought young and trained for the household."),
    "a_the_black_army": ("Pannonian Veterans", "A standing army of professionals, paid by the crown and kept at arms."),
    "a_landsknechte": ("Germanic Foot", "Mercenary foot from the German forests, with long spears and a taste for plunder."),
    "a_reislaufer": ("Alpine Spearmen", "Spearmen of the high valleys, hired out to any prince who pays."),
    "a_florentine_citizen_militia": ("Citizen Militia", "Townsmen who take up arms to defend their walls."),
    "a_andalusi_arquebusiers": ("Andalusi Skirmishers", "Skirmishers of the southern Iberian cities, who harass the enemy with javelins and bows."),
    "a_algiers_ojaq_janissaries": ("Garrison Guards", "A corps of professional garrison troops in the coastal cities."),
    "a_iron_helmet_musketeers": ("Iron-Helmet Spearmen", "Spearmen in iron helmets, who stand in a drilled line."),
    "a_pontifical_swiss_guard": ("Papal Guard", "The pope's own guard, in the bishop's service for life."),
    "a_tercio": ("Mixed Phalanx", "A great square of spearmen and archers, which fights in every direction."),
    "a_saxon_defensioner": ("Frontier Defenders", "Peasant-soldiers who hold the frontier forts against raiders."),
    "a_hesse_jager": ("Chattian Skirmishers", "Skirmishers of the Chatti forests, who hunt men as they hunt game."),
    "a_gebirgsschutzen_infantry": ("Mountain Skirmishers", "Skirmishers of the high passes, who strike from above and vanish."),
    "a_subsaharan_musketeer_corps": ("Sub-Saharan Spearmen", "Spearmen of the savanna kingdoms, who fight in drilled bands."),
    "a_caroleans": ("Northern Guard", "A king's guard of the north, drilled to fight as one."),
    "a_scottish_highlander": ("Highland Warriors", "Warriors of the northern hills, who charge screaming with sword and shield."),
    "a_tofangchi": ("Persian Archers", "Archers of the Persian king's army, who shoot in volleys from behind the front."),
    "a_tupchi": ("Persian Engineers", "Engineers who tend the king's siege engines and serve them in battle."),
    "a_prussian_grenadiers": ("Frontier Plumbatarii", "Tall dart-throwers of the northern marches, drilled to the highest standard."),
    "a_bavarian_jager": ("Bavarian Skirmishers", "Skirmishers of the Bavarian forests, in loose order and quick on foot."),
    "a_hajduk": ("Balkan Raiders", "Outlaw bands of the Balkan hills, who serve whoever pays."),
    "a_redcoats": ("Island Spearmen", "Spearmen of the far island, drilled and disciplined above all others."),
    "a_experimental_riflemen": ("Veteran Skirmishers", "Skirmishers trained in new ways of fighting, and trusted to act alone."),
    "a_cacadores": ("Lusitanian Skirmishers", "Light infantry of the Atlantic coast, who fight in open order."),
    "a_gurkha": ("Hill Warriors", "Hardy hillmen who fight with the heavy knife and the spear."),
    "a_jazayerchi": ("Persian Spearmen", "Spearmen of the Persian king's guard, in drilled ranks."),
    "a_pandur": ("Balkan Foot", "Irregular infantry of the Balkan villages, raised for a campaign."),
    "a_austrian_grenzer": ("Border Infantry", "Infantry settled along the frontier in return for service, who guard it for the crown."),
    "a_renaissance_conquistadors": ("Adventurers", "Armoured fortune-seekers who march into unknown lands for gold."),
    "a_discovery_conquistadors": ("Veteran Adventurers", "Hardened adventurers who have won lands and wealth by the sword."),
    "a_a_urughs": ("Camp Guards", "Warriors who guard the chief's camp and its herds."),
    "a_logistics_corps": ("Annona Corps", "Officers and wagoners of the grain supply, who keep an army fed on the march."),
    "a_discovery_cawa": ("Ç̌äwa Archers", "Ç̌äwa warriors who fight with the bow."),
    "a_reformation_cawa": ("Ç̌äwa Spearmen", "Ç̌äwa warriors who fight with spear and shield."),
    "a_absolutism_cawa": ("Ç̌äwa Shieldmen", "Ç̌äwa warriors drilled to hold a wall of shields."),
    "a_revolutions_cawa": ("Ç̌äwa Veterans", "Ç̌äwa warriors hardened by a century of war."),
    "a_renaissance_janissaries": ("Household Guards", "Slave-soldiers raised in the ruler's household, loyal to him alone."),
    "a_discovery_janissaries": ("Household Archers", "Household soldiers trained as archers, who shoot in volleys."),
    "a_reformation_janissaries": ("Household Spearmen", "Household soldiers with spear and shield, who hold the line."),
    "a_absolutism_janissaries": ("Household Shieldmen", "Household soldiers drilled in a wall of shields."),
    "a_revolutions_janissaries": ("Household Veterans", "Household soldiers who have fought a hundred battles."),
    "a_discovery_qizilbash": ("Persian Skirmishers", "Light horse of the Persian tribes, who skirmish and harass."),
    "a_reformation_qizilbash": ("Persian Cavalry", "Horse of the Persian tribes, the backbone of the king's army."),
    # --- ships
    "n_cog": ("Corbita", "A broad merchant ship with a deep hold, the workhorse of every harbour."),
    "n_early_carrack": ("Round Ship", "A beamy sailing ship built to carry cargo and little else."),
    "n_carrack": ("Navis Oneraria", "A large sailing ship that carries grain and soldiers over long voyages."),
    "n_hulk": ("Heavy Corbita", "A heavy merchant ship with a wide hull, which carries a great cargo."),
    "n_galleon": ("Great Dromon", "The largest oared and sailed warship, with several banks of oars and a crew of fighters."),
    "n_war_galleon": ("Ousiakos", "A big warship of the fleets, with a crew of marines and a siphon for fire."),
    "n_twodecker": ("Bireme", "A warship with two banks of oars."),
    "n_threedecker": ("Trireme", "A warship with three banks of oars, the pride of any fleet."),
    "n_ship_of_the_line": ("Pamphylos", "The largest warship of the fleet, with hundreds of oarsmen and a fighting platform."),
    "n_barque": ("Lusoria", "A light, quick river and coastal patrol boat."),
    "n_caravel": ("Dromon", "A fast oared and sailed warship, the main ship of the fleets."),
    "n_pinnace": ("Scapha", "A small oared boat used as a scout and a tender."),
    "n_frigate": ("Liburna", "A light, fast warship with a single bank of oars, built for scouting and pursuit."),
    "n_heavy_frigate": ("Heavy Liburna", "A larger liburna, with more oars and a stronger ram."),
    "n_flute": ("Chelandion", "A large oared ship with a ramp, which carries horses and men to war."),
    "n_brig": ("Lembus", "A small, fast ship used for carrying messages and cargo."),
    "n_merchantman": ("Navis Mercatoria", "A merchant ship built to carry a hold of goods across the sea."),
    "n_eastindiaman": ("Grain Ship", "A giant merchant ship that carries the grain of Egypt to the capital."),
    "n_galleass": ("Heavy Galley", "A large galley with heavy fighting platforms and many oars."),
    "n_xebec": ("Hemiolia", "A fast light galley with a pair of sails and a bank and a half of oars."),
    "n_catalan_galley": ("Western Galley", "A galley of the western Mediterranean, built for raiding and trade."),
    "n_early_iberian_caravel": ("Atlantic Lusoria", "A light ship built for the Atlantic swell."),
    "n_iberian_caravel": ("Atlantic Dromon", "A fast ship that sails closer to the wind than any other."),
    "n_square_rigged_caravel": ("Square-Rigged Lusoria", "A light ship with square sails, quick before the wind."),
    "n_early_iberian_galleon": ("Atlantic Oneraria", "A broad ship built to carry cargo through the Atlantic swell."),
    "n_iberian_galleon": ("Atlantic Great Dromon", "A large warship with a high deck, built to ride out the ocean."),
    "n_genoese_galley": ("Ligurian Galley", "A galley of the Ligurian coast, built for trade and war."),
    "n_hanseatic_cog": ("Northern Cargo Ship", "A tubby northern ship that carries bulk goods along the coast."),
    "n_barbary_fusta": ("Moorish Galley", "A fast galley of the African coast, used by raiders and traders alike."),
    "n_early_turtle_ship": ("Armoured Galley", "A galley with a roof of iron plates, hard to board."),
    "n_turtle_ship": ("Great Armoured Galley", "A large armoured galley, with a spiked roof and many oars."),
    "n_panokseon": ("Heavy Warship", "A tall oared warship with fighting decks."),
    "n_atakebune": ("Armoured Barge", "A big barge with armoured sides that carries archers and soldiers."),
    "n_sekibune": ("Fast Galley", "A fast galley with a single bank of oars, built to raid."),
    "n_baochuan": ("Great Junk", "A giant junk with many masts and decks."),
    "n_cakradonya": ("Heavy Prau", "A big prau with a fighting deck, used by the sea-raiders."),
    "n_galiot": ("Light Galley", "A small galley with a single bank of oars, quick and handy."),
    "n_maghrebi_galiot": ("Maghrebi Light Galley", "A light galley of the African coast, quick and handy."),
    "n_maghrebi_xebec": ("Maghrebi Hemiolia", "A fast African galley with a pair of sails and a bank and a half of oars."),
    "n_baghlah": ("Great Dhow", "A large dhow of the Arabian coast, which carries cargo and soldiers across the sea."),
    "n_bomb_ketch": ("Fireship", "A ship fitted with siphons and pots of fire, to burn the enemy's fleet."),
    "n_archipelago_frigate": ("Island Liburna", "A light warship built for the narrow island channels."),
}

ROADS = {
    "gravel_road": ("Track", "The [road|e] is a beaten track of gravel and earth. Better than mud."),
    "paved_road": ("Paved Road", "The [road|e] has a solid paved surface which is much better for travel."),
    "modern_road": ("Military Road", "The [road|e] is a cambered road of laid stone, built for the march of armies."),
    "railroad": ("Via Publica", "The [road|e] is a great stone highway with kerbs, drains and milestones, massively increasing travel speed and logistics."),
}

CANNON_LOC = {
    "cannons": ("Siege Equipment", "Siege weapons have existed since antiquity: onagri, ballistae and rams. The ability to throw bigger projectiles at greater speed and distances will make all but the sturdiest of fortifications fall before them, and they can also be turned on armies in the field."),
    "cannon_maker": ("Siege Workshop", "A guild specialized in building and assembling siege engines. These powerful weapons are essential for sieges and defense."),
    "cannon_workshop": ("Siege Engineers", "The ever-increasing demand of engines for our armies requires us to increase the capabilities of the $cannons$ production."),
    "cannon_foundry": ("Siege Foundry", "In a $cannon_foundry$ the metal fittings of siege engines are cast and assembled from molten metal. Key for equipping armies with engines, enhancing a state's military capabilities."),
    "cannons_factory": ("Arsenal", "A large state workshop where siege engines are built in bulk. Its expanded production capacity is a great way to facilitate the growing needs of our military forces."),
}


def _kids(node: Node) -> list[Node]:
    return node.val if isinstance(node.val, list) else []


def _num(node: Node) -> float:
    return float(str(node.val))


def _holds_firearms(node: Node) -> bool:
    """a block that buys firearms: a `firearms = <amount>` anywhere inside (`produced = firearms` is an output and is not one)."""
    return any(k.key == "firearms" and not isinstance(k.val, list) or _holds_firearms(k) for k in _kids(node))


@functools.lru_cache(maxsize=None)
def vanilla_firearms_blocks() -> dict[str, dict[str, Node]]:
    """{folder: {top-level entry: node}} for every entry that buys firearms, in vanilla's file order."""
    out: dict[str, dict[str, Node]] = {}
    for folder in FOLDERS:
        out[folder] = {}
        for p in sorted((b.GAME / folder).glob("*.txt")):
            if p.name in SKIP_DEMANDS and folder == DEMANDS:
                continue
            for node in from_entries(parse(p.read_text(encoding="utf-8-sig"))):
                if node.key and isinstance(node.val, list) and _holds_firearms(node):
                    out[folder][node.key] = node
    return out


def vanilla_firearms_entries() -> dict[str, tuple[float, float]]:
    """{goods demand: (firearms, weaponry)} as vanilla has it."""
    out = {}
    for key, node in vanilla_firearms_blocks()[DEMANDS].items():
        amounts = {k.key: _num(k) for k in _kids(node) if k.key in ("firearms", "weaponry")}
        out[key] = (amounts["firearms"], amounts.get("weaponry", 0.0))
    return out


@functools.lru_cache(maxsize=None)
def vanilla_unit_keys() -> frozenset[str]:
    keys = set()
    for p in (b.GAME / "in_game/common/unit_types").glob("*.txt"):
        if p.name != "readme.txt":
            keys |= {n.key for n in from_entries(parse(p.read_text(encoding="utf-8-sig"))) if n.key and isinstance(n.val, list)}
    return frozenset(keys)


def _fold(node: Node) -> Node:
    """the same block with firearms folded into weaponry (summed, in the place of the first of the two), all the way down."""
    kids = _kids(node)
    if not isinstance(node.val, list):
        return node
    total = sum(_num(k) for k in kids if k.key in ("firearms", "weaponry") and not isinstance(k.val, list))
    amount = str(round(total, 6)).removesuffix(".0")
    out, placed = [], False
    for k in kids:
        if k.key not in ("firearms", "weaponry") or isinstance(k.val, list):
            out.append(_fold(k))
        elif not placed:
            out.append(Node("weaponry", "=", amount))
            placed = True
    return Node(node.key, node.op, out)


def goods_price(good: str) -> float:
    """vanilla's default_market_price of a good (1 when it names none)."""
    for p in sorted((b.GAME / GOODS).glob("*.txt")):
        for node in from_entries(parse(p.read_text(encoding="utf-8-sig"))):
            if node.key == good and isinstance(node.val, list):
                return next((_num(k) for k in node.val if k.key == "default_market_price"), 1.0)
    raise KeyError(good)


def _vanilla_roads() -> list[Node]:
    out = []
    for p in sorted((b.GAME / ROAD_TYPES).glob("*.txt")):
        out += [n for n in from_entries(parse(p.read_text(encoding="utf-8-sig"))) if n.key and isinstance(n.val, list)]
    return out


def road_demand_names() -> list[str]:
    """every construction and maintenance demand of every road type, from vanilla's road types."""
    return [str(k.val) for road in _vanilla_roads() for k in _kids(road) if k.key in ("construction_demand", "maintenance_demand")]


def _swap_late(node: Node) -> Node:
    """a goods demand with each late good paid in period goods of the same total value."""
    out: list[Node] = []
    for k in _kids(node):
        if k.key not in LATE_GOODS:
            out.append(k)
            continue
        value = _num(k) * goods_price(k.key)
        for good, share in LATE_GOODS[k.key].items():
            amount = round(value * share / goods_price(good), 6)
            mine = next((o for o in out if o.key == good), None)
            if mine:
                mine.val = str(round(_num(mine) + amount, 6))
            else:
                out.append(Node(good, "=", str(amount).removesuffix(".0")))
    return Node(node.key, node.op, out)


@functools.lru_cache(maxsize=None)
def vanilla_road_demands() -> dict[str, Node]:
    """{demand: node} of the road demands that ask for a late good, in vanilla's file order."""
    names, out = set(road_demand_names()), {}
    for p in sorted((b.GAME / DEMANDS).glob("*.txt")):
        for node in from_entries(parse(p.read_text(encoding="utf-8-sig"))):
            if node.key in names and any(k.key in LATE_GOODS for k in _kids(node)):
                out[node.key] = node
    return out


def _merged(node: Node) -> Node:
    out = _fold(node)
    out.key = "REPLACE:" + node.key
    return out


def road_block() -> list[Node]:
    """vanilla's railroad with the stone road's look (spline 2, its colour); the numbers stay vanilla's."""
    for p in (b.GAME / "in_game/common/road_types").glob("*.txt"):
        for node in from_entries(parse(p.read_text(encoding="utf-8-sig"))):
            if node.key == "railroad":
                swap = {"spline_style_id": "2", "color": "map_modern_road"}
                return [Node(k.key, k.op, swap.get(k.key, k.val)) for k in _kids(node)]
    raise KeyError("railroad")


def outputs():
    out = {}
    for folder, nodes in vanilla_firearms_blocks().items():
        blocks = [_merged(n) for n in nodes.values()]
        if folder == DEMANDS:
            blocks += [Node("REPLACE:" + k, "=", _swap_late(n).val) for k, n in vanilla_road_demands().items()]
        blocks[0].lead = ["TFE: no gunpowder in 395-895, so every arm is bought as weaponry, summed one for one (both cost 3); written by script/arms.py"]
        if folder == DEMANDS:
            blocks[-1].lead = ["TFE: no road asks for steel (no steel before the steel mill): its share is paid in stone and iron at vanilla prices"]
        out[f"{folder}/tfe_arms.txt"] = render(blocks)
    roads = [Node("REPLACE:railroad", "=", road_block())]
    roads[0].lead = ["TFE: the top road keeps vanilla's numbers but looks like the stone road; named the Via Publica (written by script/arms.py)"]
    names = {**{k: v for k, v in CANNON_LOC.items()}, **UNITS, **ROADS}
    loc = ["l_english:"] + [f' {k}: "{n}"\n {k}_desc: "{d}"' for k, (n, d) in names.items()]
    return {**out, OUT_ROADS: render(roads), LOC: "\n".join(loc) + "\n"}
