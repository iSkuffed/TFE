# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow"]
# ///
"""TFE location templates: vanilla's, with what the land was good for in 395.

  uv run tools/location_templates.py     rewrite in_game/map_data/location_templates.txt from vanilla's

A template's `modifier` is the location's own: it shows as a badge on the goods marker in the raw-material map mode
and in the location panel (vanilla: Almaden's mercury, Skane's herring). Rerun after a patch changes vanilla's file.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borders as b

OUT = b.MOD / "in_game/map_data/location_templates.txt"

# Africa's grain filled the annona of Rome: Carthage, the Bagradas valley and the wheat towns of Byzacena.
# Vanilla's 1337 goods for five of them (dyes, sugar, olives, clay, legumes) were grain fields in 395.
GRANARIES = ("tunis", "mateur", "tebourba", "medjez_el_bab", "beja_TUN", "el_kef", "el_fahs", "tebessa", "sbiba",
             "kairouan", "gabes")
# Pannonia Prima, Valeria, Savia and Secunda: the legions' best recruits, and most of their emperors
PANNONIA = ("transdanubia_area", "slavonia_area")
# Rome ate African bread: a fifth of Italy's wheat land (9 of 44) had gone to the villas' vines and herds. All in
# Italia Suburbicaria, which the annona fed; the Po valley still grew grain for the court, and Sicily and Sardinia were
# granaries themselves. Lucania, Bruttium and Samnium sent Rome its pork dole; Apulia its wool.
ITALIAN_VILLAS = {
    "gaeta": "wine",           # Caecuban and Falernian
    "fermo": "wine",           # Picenum
    "viterbo": "wine",         # Etruria
    "grosseto": "livestock",   # the Maremma
    "campagna": "livestock",   # Lucania
    "benevento": "livestock",  # Samnium
    "cassano": "livestock",    # Bruttium
    "foggia": "wool",          # Apulia
    "larino": "wool",
}
# Italy's remaining wheat yields less, so African grain sells in Italian markets. Italia Annonaria (the north) paid
# its tax in grain to the court and army at Milan, so less reached the market: Annona Militaris. The rest of the
# mainland, fed by the dole, let its fields go: Latifundia. Sicily and Sardinia keep full yields.
ITALIA_ANNONARIA = ("lombardy_area", "piemonte_area", "veneto_area", "emilia_area", "liguria_area")
ITALIAN_ISLANDS = ("sicily_area", "sardinia_area")
# Britannia fed the Rhine army (Julian's 359 grain fleet), mined, potted and kept cattle; the great wool trade was
# medieval. Of vanilla's 33 English and Welsh wool towns only five flocks stay: the downs around Venta Belgarum, whose
# state weaving works made the birrus Britannicus, the Welsh hills, the Cumbrian fells and the Votadini's hills.
BRITANNIA = {
    "dunstable": "livestock", "aylesbury": "livestock", "wigmore": "livestock", "bosworth": "livestock",
    "retford": "livestock", "birmingham": "livestock", "bideford": "livestock", "fishguard": "livestock",
    "montgomery": "livestock",
    "hedingham": "livestock",   # Boreham's improved late-Roman cattle
    "walden": "wheat",          # Saffron Walden's crocus fields are 14th-century
    "thetford": "horses",       # the Iceni's horse country
    "abingdon": "wheat", "henley": "wheat", "banbury": "wheat", "shaftesbury": "wheat", "lavenham": "wheat",
    "lewes": "wheat",           # Sussex villas; the Weald's iron had collapsed by the late 3rd century
    "tonbridge": "lumber",      # the Weald, Anderida's forest
    "northampton": "wine",      # the Wollaston vineyard
    "portishead": "salt", "lynn": "salt",   # Somerset Levels and fenland salterns
    "oxford": "clay", "southampton": "clay", "huntingdon": "clay",   # Oxfordshire, New Forest, Nene Valley wares
    "kettering": "iron",        # Northamptonshire ironstone
    "hereford": "iron",         # Ariconium, beside the Forest of Dean
    "oswestry": "copper",       # Llanymynech
    "truro": "tin",             # Cornish tin replaced Spain's in the 3rd century
    "wells": "lead", "bath": "stone",   # Charterhouse on Mendip; Bath stone
    # the north was the army's: grain for the legion at York, cattle and hides for the Wall, cavalry horses
    "norton": "wheat", "pontefract": "wheat",   # East Riding villas, the Vale of York
    "skipton": "lead",          # Craven and Nidderdale
    "preston": "horses",        # Ribchester's Sarmatian veterans
    "durham": "livestock", "stockton": "livestock", "morpeth": "livestock",
    "whitby": "gems",           # jet, carved at York; the alum works came in 1600
    "scarborough": "fish",
    # coal burned only near its seams: the Wall forts, Bath's temple of Minerva (Solinus), South Wales
    "nottingham": "wheat", "manchester": "livestock", "blackburn": "livestock", "darlington": "livestock",
    "caerphilly": "livestock",
    "radnor": "livestock", "barnstaple": "livestock",   # no ancient remedies; Combe Martin's silver is medieval
}
# Gaul in 395: wine from Narbonensis to the Moselle, olives only in the south, grain, pottery, hams and cheese, and
# Belgica's woollen cloaks (in Diocletian's Price Edict, so its wool stays). Out go silk, saffron, the medieval woad
# trade, coal, mines opened in the Middle Ages, and wine beyond the Rhine, where Franks and Alamanni keep herds.
GAUL = {
    # Aquitania and Novempopulana
    "allegre": "livestock", "huriel": "livestock", "jaligny": "livestock", "bellac": "livestock",
    "montflanquin": "livestock", "limeuil": "livestock", "thouars": "livestock", "montmorillon": "livestock",
    "pau": "livestock", "orthez": "livestock", "saint_lizier": "livestock",   # Pyrenean herds, not medieval wool
    "rodez": "livestock", "millau": "livestock", "peyrusse": "livestock",     # the Ruteni's uplands
    "vodable": "iron", "villefranche": "silver",
    "lisle_jourdain": "wheat", "riberac": "wheat", "aulnay": "wheat",   # Melle's silver was Carolingian
    "dax": "medicaments",       # Aquae Tarbellicae, a spa Augustus visited
    "labrit": "lumber",         # the Landes pines
    "la_teste_de_buch": "fish",
    "cahors": "fiber_crops",    # Pliny: the Cadurci's linen
    # Narbonensis and Viennensis
    "pamiers": "livestock", "chalancon": "livestock", "le_puy": "livestock", "french_ales": "wild_game",
    "mende": "livestock", "florac": "livestock",   # the Gabali's cheese (Pliny); Cevennes silk is early modern
    "saint_pons": "iron",       # Montagne Noire
    "melgueil": "salt",
    "montpellier": "wine", "carcassonne": "wine", "fenouillet": "wine", "limoux": "wine", "avignon": "wine",
    "tournon": "wine", "vienne": "wine",   # the Allobroges' pitch-flavoured vinum picatum (Pliny)
    "die": "wine",              # the Vocontii's sweet wine
    "uzes": "olives", "marseille": "olives", "grasse": "olives",
    # the Lauragais grew grain; its woad trade is 15th-century
    "toulouse": "wheat", "castelnaudary": "wheat", "verdun_sur_garonne": "wheat", "lavaur": "legumes",
    "perreux": "livestock", "roanne": "livestock",
    "lyon": "clay",             # Lugdunum's potteries; its silk is 15th-century
    "tarascon": "livestock",    # the Crau's winter pastures
    "aix_en_provence": "medicaments", "digne": "medicaments",   # Aquae Sextiae; Digne's springs
    "frejus": "fish",           # Forum Julii's fish sauce (Pliny)
    "toulon": "fish",
    "castellane": "livestock", "sisteron": "livestock", "mevouillon": "livestock", "gap": "livestock",
    "briancon": "livestock", "faucigny": "livestock",
    "grenoble": "iron",
    # Lugdunensis and Belgica
    "corbeil": "wheat", "amiens": "wheat", "troyes": "wheat", "vesoul": "wheat", "bethune": "wheat",
    "donzy": "wheat", "meaux": "wheat",
    "chinon": "wine", "dijon": "wine", "chateau_thierry": "wine",
    "montmorency": "fruit", "cercy": "lumber", "darney": "lumber", "sable": "stone",
    "arras": "wool",            # the Atrebates' cloaks
    "saint_omer": "livestock",  # Menapian hams
    "louviers": "livestock",    # its cloth boom was 14th-century
    "clermont_en_argonne": "clay",   # Argonne ware, still made in the 4th century
    # the Rhine frontier, Roman side
    "geneve": "wine", "kreuznach": "wine", "oppenheim": "wine", "saarburg": "wine",   # Ausonius's Moselle country
    "liege": "iron", "diez": "iron", "lichtenberg_veldenz": "iron",
    "mayen": "stone",           # Mayen basalt millstones, sold across the Empire
    # the spas of Aquae Granni, Aquae Helveticae and Aquae Aureliae
    "aachen": "medicaments", "baden_im_aargau": "medicaments", "baden": "medicaments",
    "prum": "wild_game", "merzig": "lumber", "murbach": "lumber", "colmar": "fruit",
    "mons": "wheat", "bergheim": "wheat", "duren": "wheat", "bruchsal": "wheat",
    "bruges": "salt", "the_hague": "livestock",
    # free Germania: cattle, iron, forest; no vines
    "biberach": "fiber_crops", "eichstatt": "stone", "ellwangen": "wild_game", "kempten": "livestock",
    "freiburg": "lumber",       # Schauinsland's silver is 13th-century
    "bayreuth": "wool", "coburg": "lumber", "calw": "lumber", "essen": "lumber", "darmstadt": "wild_game",
    "aschaffenburg": "lumber", "bentheim": "stone", "dortmund": "wheat",
    "osnabruck": "iron", "korbach": "iron",   # the Chatti's iron (Tacitus)
    "urach": "fruit", "mullheim": "fruit", "heilbronn": "livestock", "hachberg": "lumber", "buchen": "lumber",
    "wurzburg": "wheat",
}
# Hispania in 395: Baetica's oil and garum, Tarraconensis wine, Saetabis linen, Celtiberian steel, Sisapo's cinnabar.
# Out go what the Arabs brought (sugar, rice, cotton, saffron, silk), saltpeter, coal, medieval alum and the Mesta's
# flocks; wool stays with the Celtiberians' and Lusitanians' black cloaks (Diodorus) and Baetica's fleeces.
HISPANIA = {
    # Baetica and Lusitania
    "moron": "livestock",       # Campina pastureland; cotton is Andalusi-era, not Roman
    "baza": "wheat",            # Hoya de Baza grain plain; saffron is Andalusi-era
    "mojacar": "lead",          # Sierra Almagrera lead-silver; alum unattested here
    "adra": "fish",             # Roman Abdera fish-salting port; sugar is Andalusi-era
    "guadix": "wheat",          # Roman Acci farmland; saffron is Andalusi-era
    "orgiva": "fruit",          # Alpujarra valley orchards; silk is Andalusi-era
    "malaga": "fish",           # Roman Malaca garum port; sugar is Andalusi-era
    "velez_malaga": "wine",     # Malaca coast Roman wine export; sugar is Andalusi-era
    "santa_eufemia": "lead",    # Alto Guadiato; Roman La Loba lead-silver mine nearby
    "niebla": "copper",         # Rio Tinto river port; no alum evidence, copper trade
    "belalcazar": "lead",       # Alto Guadiato mines, Roman remains; alum unattested
    "puebla_de_guzman": "copper",# Tharsis-La Zarza Roman copper mines in this district
    "tavira": "fish",           # Roman Balsa; Algarve fish-salting, no tin evidence
    "olvera": "olives",         # Roman Hippo Nova; no evidence of baths, Cadiz olive belt
    # Carthaginiensis, eastern Tarraconensis, the Balearics
    "alcaniz": "olives",        # Bajo Aragon oil region, groves since Roman era
    "montalban": "iron",        # Sierra Menera iron worked since Celtiberian/Roman times
    "sarinena": "wheat",        # Monegros cereal steppe; saffron is Arab-era
    "calatayud": "iron",        # Bilbilis: Martial praised its tempered steel
    "alfambra": "livestock",    # Teruel highland pasture; saffron is Arab-era
    "zaragoza": "wine",         # Caesaraugusta amid Ebro vineyards; saffron Arab-era
    "belchite": "livestock",    # Bajo Aragon steppe grazing; silk is Andalusi-era
    "tarazona": "iron",         # Turiaso: Pliny groups its iron fame with Bilbilis
    "monzon": "wheat",          # Cinca valley plain; Ilergetes land, not Celtiberia
    "huesca": "wheat",          # Osca's Hoya basin is a grain plain, not Celtiberia
    "jaca": "horses",           # Pyrenean pass town; Vascones land, not Celtiberia
    "sos": "livestock",         # Pyrenean foothill pasture; Vascones, not Celtiberia
    "almodovar_del_campo": "livestock",# Oretani grazing land, not Celtiberia
    "malagon": "legumes",       # Oretani plain; La Mancha pulses, not Celtiberia
    "tortosa": "fish",          # Dertosa: Ausonius praised its Ebro river fish
    "manresa": "wheat",         # Bages plain grain; saltpeter is gunpowder-era
    "montblanc": "stone",       # Conca de Barbera quarry; no ancient alum evidence
    "seu_durgell": "livestock", # Ceretani cheese pasture (Pliny NH 11.240)
    "vielha": "livestock",      # Val d'Aran alpine pasture, not Celtiberian
    "cartagena": "silver",      # Carthago Nova: Strabo/Polybius on its vast silver mines
    "murcia": "wheat",          # Segura valley grain; silk is Andalusi-era
    "lorca": "fiber_crops",     # Eliocroca esparto country; saltpeter is gunpowder-era
    "mula": "livestock",        # Interior Murcia pasture; Mazarron alum is 15th-c.
    "alcazar_de_san_juan": "wheat",# La Mancha grain plain; saltpeter is gunpowder-era
    "jativa": "fiber_crops",    # Saetabis linen: praised by Pliny, Catullus, Martial
    "gandia": "salt",           # Coastal saltpans; sugar is Arab-era
    "valencia": "fish",         # Valentia: Albufera lagoon fisheries; silk is Andalusi-era
    "bunol": "stone",           # Inland quarry stone; no ancient alum evidence
    # Gallaecia and the north
    "villablino": "lumber",     # Laciana valley forest; coal is anachronistic here
    "chaves": "medicaments",    # Aquae Flaviae, Iberia's largest Roman bath complex
    "ourense": "medicaments",   # As Burgas, Roman thermal sanctuary/bathhouse
    "ribadavia": "wine",        # Ribeiro's Roman-era winepresses (Strabo, 2nd c. BC)
    "villaviciosa": "fruit",    # Astures' apple orchards, Strabo 1st c. BC
    "carrion_de_los_condes": "wheat",# Vaccaei grain plain, Tierra de Campos
    "monzon_campos": "wheat",   # Vaccaei grain plain, Tierra de Campos
    "cuellar": "livestock",     # Arevaci highland cattle herders, not Mesta
    "fuentiduena": "livestock", # Arevaci highland cattle herders, not Mesta
    "valmaseda": "livestock",   # Basque mountain pastoralism, not Mesta wool
    "olite": "wine",            # Ribera Navarra, Ebro valley viticulture (cf. Tudela)
    "miranda_de_i_douro": "livestock",# Trás-os-Montes cattle country (Zoela)
    # Extremadura and the Alentejo were the Mesta's winter pastures; Baetica keeps its golden fleeces (Martial)
    "badajoz": "wheat", "escurial": "livestock", "valencia_de_alcantara": "livestock",
    "jerez_de_los_caballeros": "livestock",   # Iberian hams (Strabo)
    "portalegre": "horses",     # the Lusitanian mares
    "merida": "dyes",           # Emerita's kermes scarlet, the best (Pliny)
    "coimbra": "olives",        # the Mondego valley; its medicine came with the university
}
# Italy in 395, beyond its wheat: Sicily's and Apulia's Arab and Norman sugar, cotton, silk and saffron go back to
# olives and wine; Tolfa's alum (1460s) and Venice's glass go; Parma, Mutina and Patavium keep the fleeces Strabo and
# Martial praised; Populonia smelts Elban iron again.
ITALIA = {
    "aquila": "livestock",        # Amiternum highlands; Apennine pastoralism replaces saffron.
    "rotondo": "lumber",          # Garganum forest; medieval/early-modern alum removed.
    "lecce": "olives",            # Lupiae/Salentum; ancient olives replace medieval saffron.
    "francavilla": "olives",      # Salentum olives; local cotton belongs to later centuries.
    "catanzaro": "wine",          # Skylletion hinterland; Roman Calabria grew wine.
    "cotrone": "fish",            # Kroton coast; coastal fishing predates local cotton.
    "reggiocal": "olives",        # Rhegium; olives replace later cotton cultivation.
    "cosenza": "lumber",          # Consentia/Sila; ancient timber suits this upland site.
    "piedimonte": "lumber",       # Allifae/Matesian hills; timber replaces late alum works.
    "bologna": "livestock",       # Bononia hinterland; no ancient local silk production.
    "medicina": "livestock",      # Bononia plain; no ancient medicinal source is attested.
    "padova": "wool",             # Patavium; Roman textiles and wool are attested.
    "modena": "wool",             # Mutina: Strabo 5.1.12 names its soft wool.
    "parma": "wool",              # Parma: Martial 14.155 ranks its fleeces second.
    "genoa": "wool",              # Liguria: Strabo 5.1.12 attests local coarse wool.
    "civitavecchia": "fish",      # Centumcellae coast; Tolfa alum works postdate 395.
    "volterra": "stone",          # Volaterrae: Etruscan alabaster urns attest local stone.
    "messina": "wine",            # Messana: Pliny NH 14.8 names Mamertine wine.
    "lomello": "livestock",       # Laumellum: rice cultivation in Italy is medieval.
    "vercelli": "wool",           # Vercellae, Po basin; ancient wool predates rice farming.
    "tratalias": "lead",          # Sulcis/Metalla; Roman lead-silver mining is attested.
    "piazza": "stone",            # Henna hinterland; saltpeter belongs to gunpowder age.
    "mazara": "fish",             # Selinus/Mazara coast; ancient fishery, no saltpeter.
    "catania": "wine",            # Catana; Roman Sicilian viticulture, before silk farming.
    "bivona": "olives",           # Sicani hinterland; ancient olives replace Arab cotton.
    "palermo": "olives",          # Panormus; ancient olives replace Arab sugar cane.
    "syracuse": "wine",           # Syracusae; Roman Sicilian wine, before Arab sugar cane.
    "malta": "fish",              # Melite; ancient island fishery replaces later cotton.
    "modica": "olives",           # Hyblaean country; olives replace later sericulture.
    "terranovasic": "olives",     # Gela coast; olives replace Arab-era cotton.
    "florence": "olives",         # Florentia; Tuscan olive-growing predates silk industry.
    "massamar": "copper",         # Massa Marittima: Etruscan copper mining.
    "piombino": "iron",           # Populonia smelted Elban iron; Strabo 5.2.6.
    "lucca": "olives",            # Luca; ancient Tuscan olives replace later cotton.
    "pescia": "fruit",            # Valdinievole; local fruit replaces later cotton crop.
    "pisa": "fish",               # Pisae coast; ancient fishing replaces later silk.
    "salerno": "olives",          # Salernum: coastal olives, no ancient medical school.
}
# Africa in 395 was the Empire's oil press and granary: Byzacena and Tripolitania olives, Meninx's and Mogador's
# purple, the red-slip potteries of El Djem and Neapolis. Out go the Arabs' sugar, cotton and saffron and the Marinids'
# flocks; the Moors and Gaetulians beyond the frontier herd, and their oases grow dates.
AFRICA = {
    "mostaganem": "wheat",        # Caesariensis plain: Roman grain, not Arab cotton.
    "cherchell": "wheat",         # Caesarea Mauretaniae: wheat replaces Arab sugar.
    "algiers": "fish",            # Icosium coast: maritime catch, not a dye center.
    "bades": "livestock",         # Interior plateau: pastoral output over unsupported dyes.
    "tamazaghrane": "fish",       # Roman coast: maritime catch, not a dye center.
    "al_kadwa": "olives",         # Tripolitanian oil region: olives replace cotton.
    "ghariyan": "olives",         # Western Djebel: suited to Roman olive-growing.
    "tarhuna": "olives",          # Tarhuna plateau: numerous Roman olive presses.
    "amergo": "wheat",            # Tingitana frontier: cereals replace Arab cotton.
    "meskiana": "millet",         # Numidian upland: millet replaces Arab cotton.
    "madas": "millet",            # Roman Africa: millet replaces Arab-era cotton.
    "chebba": "olives",           # Byzacena coast: olives replace Arab sugar.
    "ajim": "dyes",               # Meninx on Djerba: Pliny ranks its purple highly.
    "medenine": "dyes",           # Gigthis district: south Gulf purple/murex trade.
    "tangier": "fish",            # Tingi/Cotta coast: Roman fish-salting industry.
    "nabeul": "clay",             # Neapolis kilns remained active into the early 6th c.
    "el_jem": "clay",             # Central Tunisian ARS kiln zone: pottery clay.
    "bejaia": "lumber",           # Saldae/Kabylie: Mauretanian timber is regional evidence.
    "tozeur": "fruit",            # Tusuros oasis: dates replace Arab saffron.
    "oujda": "livestock",         # Fringe pastoralism replaces a wool economy.
    "brezina": "livestock",       # Fringe pastoralism replaces Arab-era cotton.
    "el_abiodh_sidi_cheikh": "livestock",# Fringe herding replaces wool trade.
    "medrissa": "livestock",      # Fringe herding replaces wool trade.
    "messaad": "livestock",       # Fringe herding replaces wool trade.
    "djelfa": "wild_game",        # Plateau game replaces an unsupported alum work.
    "abalessa": "wild_game",      # Saharan game replaces a nonlocal sand good.
    "sinawin": "livestock",       # Fringe pastoralism replaces a sand good.
    "tazirbu": "fruit",           # Tazirbu oasis: dates replace medieval wool.
    "zella": "fruit",             # Zella oasis: dates replace medieval wool.
    "sabha": "fruit",             # Fezzan oasis: dates replace medieval wool.
    "ain_salah": "fruit",         # Saharan oasis: dates replace a sand good.
    "ghardaia": "fruit",          # M'zab oasis: dates replace Arab saffron.
    "berriane": "livestock",      # Fringe herding replaces wool trade.
    "ouargla": "fruit",           # Ouargla oasis: dates replace a dye trade.
    "ngoussa": "fruit",           # Saharan oasis: dates replace Arab cotton.
    "taghit": "fruit",            # Taghit oasis: dates replace medieval wool.
    "tamacine": "fruit",          # Saharan oasis: dates replace Arab saffron.
    "ksar_el_kebir": "livestock", # BAQ fringe: pastoral output replaces sugar.
    "ouezzane": "livestock",      # BAQ fringe: herding replaces wool trade.
    "miatbir": "livestock",       # Unowned fringe: herding replaces wool trade.
    "al_mazamma": "livestock",    # BAQ fringe: herding replaces Arab cotton.
    "fez": "livestock",           # BAQ fringe: pastoral output replaces dye works.
    "azrou": "wild_game",         # Atlas woodland game replaces a dye trade.
    "baht": "livestock",          # BAQ fringe: herding replaces a cloth economy.
    "sefrou": "livestock",        # BAQ fringe: herding replaces wool trade.
    "tabarida": "livestock",      # BAQ fringe: herding replaces wool trade.
    "terrest": "livestock",       # BAQ fringe: herding replaces a later mine.
    "tezerghe": "livestock",      # BAQ fringe: herding replaces an unsupported mine.
    "chichaoua": "livestock",     # Unowned fringe: herding replaces Arab cotton.
    "marrakesh": "livestock",     # Unowned fringe: herding replaces later wine.
    "naffis": "livestock",        # Unowned fringe: herding replaces an unsupported mine.
    "tamdegost": "livestock",     # Unowned fringe: pastoral output replaces sugar.
    "tinmel": "wild_game",        # Atlas game replaces medieval wool trade.
    "bzou": "livestock",          # Unowned fringe: pastoral output replaces sugar.
    "demnate": "wild_game",       # Atlas game replaces medieval wool trade.
    "azemmour": "livestock",      # BAQ fringe: herding replaces Arab cotton.
    "settat": "livestock",        # BAQ fringe: pastoral output replaces later wine.
    "tamdoult": "livestock",      # Unowned fringe: herding replaces a later mine.
    "beni_sabih": "livestock",    # Unowned fringe: pastoral output replaces dyes.
    "tizounine": "livestock",     # Unowned fringe: herding replaces an unsupported mine.
    "agdez": "fruit",             # Draa oasis: dates replace medieval wool.
    "ait_benhaddou": "livestock", # Unowned fringe: herding replaces wool trade.
    "taroudant": "fruit",         # Sus/Souss oasis: dates replace Arab cotton.
    "noul_lamta": "livestock",    # Unowned fringe: herding replaces wool trade.
    "tafraout": "wild_game",      # Anti-Atlas game replaces an unsupported mine.
    "tidsi": "livestock",         # Unowned fringe: pastoral output replaces sugar.
    "sijilmasa": "fruit",         # Sijilmasa oasis: dates replace later alum works.
    "boumalne_dades": "fruit",    # Dades oasis: dates replace stone.
    "ksar_es_souk": "fruit",      # Tafilalt oasis: dates replace an unsupported mine.
    "tazzarine": "fruit",         # Draa oasis: dates replace an unsupported mine.
    "todgha": "fruit",            # Todgha oasis: dates replace uncertain Saharan gold.
    "smara": "livestock",         # Unowned Saharan fringe: pastoral output.
    "tindouf": "livestock",       # Unowned Saharan fringe: pastoral output.
    "aousserd": "livestock",      # Unowned Saharan fringe: pastoral output.
    "mogador": "dyes",            # Iles Purpuraires: Juba II's Gaetulian purple works
    "tetouan": "olives",          # Tamuda in the Martil valley: sugar is Andalusi-era.
    "tissemsilt": "wheat",        # The Sersou plateau, Mauretanian grain land: cotton is Arab-era.
}
# Raetia and Noricum: alpine herds, Noric iron from the Hüttenberg, the baths of Aquae (Baden). Tirolese and
# Bohemian silver, Hall's salt and the Styrian Erzberg are medieval; the Alamanni and Marcomanni farm and herd.
RAETIA_NORICUM = {
    "garmisch": "livestock",      # Partanum: alpine pasture; no ancient alum works
    "traunstein": "livestock",    # No Roman spa or medicinal spring is attested here
    "kyburg": "livestock",        # No Roman spa source; Kyburg is medieval
    "roding": "livestock",        # No Roman spa source; outside the imperial frontier
    "monthey": "livestock",       # Bex saltworks begin in 1475; no Roman extraction
    "innsbruck": "livestock",     # Oeni Pons by Hall; salt first recorded in 1232
    "sterzing": "livestock",      # Wibitina: Schneeberg silver attested from 1237
    "bludenz": "lumber",          # Montafon silver first recorded in 1319
    "konstanz": "fish",           # Bodensee: Raetian wine is sourced near Verona
    "zabern": "wheat",            # Tabernae: Alsace local viticulture is late or uncertain
    "belfort": "livestock",       # No Roman-period local wine production evidence
    "augsburg": "wheat",          # Augusta Vindelicorum: fustian/cotton trade is medieval
    "ulm": "wheat",               # ALM frontier: no local Roman fiber-crop evidence
    "stockach": "livestock",      # Alamannic frontier: pastoral output suits the period
    "riedlingen": "livestock",    # Alamannic frontier: pastoral output suits the period
    "villingen": "livestock",     # Alamannic frontier: pastoral output suits the period
    "waldshut": "livestock",      # Alamannic frontier: pastoral output suits the period
    "welzheim": "lumber",         # ALM frontier: glass sand is a specialized industry
    "austria_baden": "medicaments",# Aquae: Roman sulfur-water baths
    "friesach": "iron",           # Hüttenberg nearby: Roman ferrum Noricum
    "korneuburg": "wheat",        # Quadi shore: beyond the limes, no Roman wine source
    "krumlov": "wild_game",       # Boiohaemum: no Roman spa source for medicaments
    "loket": "lumber",            # Loket coal extraction is post-Roman
    "tepla": "lumber",            # West Bohemian silver working is medieval
    "kutna_hora": "wheat",        # Mons Cuthna: silver boom starts in the 13th c
    "cheb": "wild_game",          # Eger tin panning is attested from the 10th c
    "litomerice": "wheat",        # Beyond the limes: no Roman wine source
    "nachod": "wild_game",        # No Roman spa evidence for medicaments
    "brno": "wheat",              # Quadi territory: no Roman vineyard evidence
    "mittersill": "livestock",    # Habachtal emerald mining lacks ancient proof
    "tamsweg": "livestock",       # No ancient tin mining evidence in the Lungau
    "voitsberg": "lumber",        # West Styrian coal extraction is post-Roman
    "leoben": "livestock",        # Styrian Erzberg iron mining is medieval or later
    "schladming": "lumber",       # No Roman-period iron mine evidence here
    "weiz": "lumber",             # Arzberg silver first recorded in 1242
    "jihlava": "livestock",       # Iglau silver boom starts in the 13th c
}
# Picts and Irish counted wealth in cattle: out go medieval linen, monastic wool and Bronze Age mines.
CALEDONIA_HIBERNIA = {
    "lewis": "fish",              # Bostadh Iron Age settlement yielded fish remains.
    "islay": "fish",              # Hebridean Iron Age fish remains support coastal fishing.
    "mann": "fish",               # Manx copper was mined in the Bronze Age or from the 13th c.
    "lochaber": "livestock",      # No ancient alum works are attested here.
    "stirling": "livestock",      # ScARF finds mixed herds; avoid widespread wool output.
    "kirkcudbright": "livestock", # ScARF finds mixed herds; avoid widespread wool output.
    "kenmure": "livestock",       # ScARF finds mixed herds; avoid widespread wool output.
    "glasgow": "livestock",       # ScARF finds mixed herds; avoid widespread wool output.
    "paisley": "livestock",       # ScARF finds mixed herds; avoid widespread wool output.
    "dumbarton": "livestock",     # ScARF finds mixed herds; avoid widespread wool output.
    "duns": "livestock",          # ScARF finds mixed herds; avoid widespread wool output.
    "forfar": "livestock",        # ScARF finds mixed herds; avoid widespread wool output.
    "arbroath": "fish",           # Coastal fishing suits this Iron Age location.
    "dumfries": "livestock",      # Scottish flax and linen are too late for 395.
    "dunfermline": "livestock",   # Scottish flax and linen are too late for 395.
    "athenry": "livestock",       # Earliest cited Irish flax cultivation is 11th c.
    "castlereagh": "livestock",   # Earliest cited Irish flax cultivation is 11th c.
    "cullahill": "livestock",     # Earliest cited Irish flax cultivation is 11th c.
    "killmallock": "livestock",   # Earliest cited Irish flax cultivation is 11th c.
    "ennis": "livestock",         # Earliest cited Irish flax cultivation is 11th c.
    "roscrea": "livestock",       # Earliest cited Irish flax cultivation is 11th c.
    "clogher": "livestock",       # Earliest cited Irish flax cultivation is 11th c.
    "magherafelt": "livestock",   # Earliest cited Irish flax cultivation is 11th c.
    "kinsale": "fish",            # Irish wool exports grew after the Norman conquest.
    "youghal": "fish",            # Irish wool exports grew after the Norman conquest.
    "dingle": "fish",             # Irish wool exports grew after the Norman conquest.
    "cashel": "livestock",        # Irish cattle dominated wealth and pastoral farming.
    "dungarvan": "fish",          # Irish wool exports grew after the Norman conquest.
    "carbery": "fish",            # West Cork copper mines date to the Bronze Age.
    "glendalough": "wild_game",   # Wicklow lead mining evidence is medieval or later.
    "tipperary": "livestock",     # Silvermines production is documented from 1298.
    "nenagh": "livestock",        # Nearby Silvermines extraction is medieval.
    "iveagh": "livestock",        # Ireland had no tin mines; tin was imported.
    "carrickmacross": "livestock",# No ancient source for this medicaments output.
}
# Illyricum: Dalmatian gold and the metalla of Domavia and Dardania; Novo Brdo's Saxon silver and Idrija's
# mercury (1490) are medieval.
ILLYRICUM = {
    "vrhbosna": "goods_gold",     # Vranica-Zeljeznica: Dalmatian gold (Pliny, Florus)
    "borac": "livestock",         # Bosnia: no ancient medicinal source attested at Borac
    "zenica": "iron",             # Bistua Nova: central-Bosnian Roman iron district; coal is modern
    "olovo": "livestock",         # Olovo lead workings are medieval; Roman mining unconfirmed
    "kljuc": "iron",              # Sana valley ferrariae were Roman iron districts
    "bihac": "iron",              # Una valley has Roman iron sites; local silver lacks evidence
    "krupanj": "livestock",       # Krupanj's silver mining is medieval; copper unsupported
    "pag": "fish",                # Caska was a Roman harbor on Pag; Adriatic fish is plausible
    "tolmin": "lumber",           # Idrija mercury was first found in 1490; Alpine timber fits
    "kucevo": "goods_gold",       # Kraku Lu Jordan near Kucevo: late Roman gold washing
    "novo_brdo": "livestock",     # Novo Brdo's major mine dates to medieval Serbia
    "pristina": "lead",           # Ulpiana near Pristina: Roman Dardanian lead-silver mining
    "sabac": "wheat",             # Sava-Macva plain; no Roman coal industry
    "valjevo": "livestock",       # Gradac: no ancient spa source for Valjevo medicaments
    "brskovo": "livestock",       # Brskovo mining begins with the 13th-c. Saxon boom
    "uzice": "livestock",         # No Roman tin district is attested around Uzice
    "belgrad": "lead",            # Singidunum: nearby Kosmaj was a Roman lead-silver district
    "kotor": "fish",              # Acruvium: no medicinal spring attested; Adriatic fish fits
    "gyor": "wheat",              # Arrabona was Roman Pannonian town, not an attested spa
    "kleisoura_epirus": "livestock",# Epirus Nova: no named Roman medicinal spring
}
# Greece and Thrace: Kytheran and Hermionian purple, Lemnian earth, Amorgine linen, island wines. No silk before
# the monks smuggled the silkworm in c. 552.
GRAECIA_THRACIA = {
    "veria": "wine",              # Beroea, Macedonian wine country; cotton is Ottoman-era
    "servia": "livestock",        # Servia, Macedon hills; saffron unattested, pastoral land
    "grevena": "lumber",          # Grevena forested highlands; no ancient alum evidence
    "thebes": "wheat",            # Boeotian grain plain; silk industry is Byzantine (12th c)
    "tripolitsa": "livestock",    # Arcadian highlands pastoral; silk is medieval Morea trade
    "pontikokastro": "olives",    # Messenian coast olives; silk is medieval Morea trade
    "karytaina": "lumber",        # Arcadian mountain forest; saltpeter is gunpowder-era
    "leuktron": "olives",         # Messenian/Laconian olives; silk is medieval Morea trade
    "mystras": "livestock",       # Laconia has no tin ore; pastoral hinterland instead
    "ermioni": "dyes",            # Hermione's murex purple dye, famed since antiquity
    "kythira": "dyes",            # Kythera = ancient "Porphyrousa", murex purple (Aristotle)
    "candia": "wine",             # Cretan wine exported since antiquity; cotton is later
    "hagios_pavlos": "olives",    # Cretan olive oil, ancient staple; sugar is Arab-era
    "rethymno": "fruit",          # Cretan orchards; saffron treated as anachronistic here
    "gergeri": "wine",            # Cretan hill vineyards; no ancient Cretan tin source
    "lemnos": "medicaments",      # Lemnian earth, medicinal clay per Dioscorides/Galen/Pliny
    "amorgos": "fiber_crops",     # Amorgos flax, the prized "amorgina" cloth (Aristophanes)
    "rodos": "wine",              # Rhodian wine, widely traded amphorae; saffron is anach.
    "constantinople": "fish",     # Byzantium's famed fisheries (Strabo); silk is post-552
    "xanthia": "wine",            # Thracian wine country (Maroneia); cotton is Ottoman-era
    "haskovo": "livestock",       # Inland Thracian pasture; cotton is Ottoman-era
    "komotini": "wool",           # Thracian hinterland pasture; alum unattested here
    "kiyikoy": "fish",            # Salmydessus, Thracian Black Sea coast fishery
    "oryahovo": "livestock",      # Danubian Moesia pasture (VIS); cotton is Ottoman-era
    "lyaskovets": "wheat",        # Danube plain grain (VIS); cotton is Ottoman-era
    "zemlungrad": "lumber",       # Balkan mountain forest; coal is an industrial-era good
    "kleisoura": "livestock",     # Upper Macedonian pasture: cotton is later
}
# The Carpathian barbaricum: Huns, Gepids, Sarmatians and Quadi herd and farm; Dacia's gold left with Rome in 271
# and the Slovak mining towns are medieval. Turda's salt was worked all along.
BARBARICUM = {
    "bihar": "wheat",             # No c.395 wine source; the plain suits grain.
    "abrahamtelke": "wheat",      # Saltpeter is a gunpowder-era good.
    "baia_mare": "lumber",        # Maramureș mining is documented from the 13th c.
    "csanad": "livestock",        # No ancient spa source; steppe stock fits.
    "syvlyush": "livestock",      # Transcarpathian wine is a later specialty.
    "balassagyarmat": "livestock",# No ancient spa source; pasture fits.
    "arad": "wheat",              # Hungarian-period wine; Mureș plain grain fits.
    "ineu": "livestock",          # No c.395 wine source; pasture suits foothills.
    "krupina": "lumber",          # Upper Hungarian viticulture is later.
    "prievidza": "lumber",        # Saffron is medieval here; forests fit.
    "trnava": "wheat",            # No c.395 wine source; fertile lowland suits grain.
    "levoca": "lumber",           # Spiš mining is documented from the late 13th c.
    "gonc": "lumber",             # Nearby Telkibánya gold boom is documented in 1270.
    "liptovsky_mikulas": "lumber",# Magurka gold mining dates to 1238.
    "kremnica": "lumber",         # No evidence for its gold workings by 395.
    "lubica": "lumber",           # Alum working is medieval/early modern.
    "medias": "wheat",            # Saxon-era wine economy postdates 395.
    "covasna": "livestock",       # No ancient alum production evidence.
    "satoraljaujhely": "fruit",   # Tokaj wine is a later regional industry.
    "gheorgheni": "lumber",       # Gyergyó baths are documented only in 1638.
    "plenita": "wheat",           # Cotton is anachronistic here.
    "stramba": "lumber",          # Strâmba spa use is documented only in modern times.
}
# Anatolia: Docimian and Proconnesian marble, Milesian and Lycaonian wool, Cappadocian studs, the Asclepieion of
# Pergamon; saffron only at Corycus (Pliny), the best in the world.
ANATOLIA = {
    "ladik_pontus": "wheat",      # Pontic plateau grain; rice is medieval
    "dinek_keskin": "wool",       # steppe flocks; saffron kept to Korykos
    "bor_tur": "wheat",           # Cappadocian plain; saltpeter is gunpowder-era
    "sivas": "livestock",         # Sebasteia grazing; silk is post-552
    "zile": "wheat",              # Zela plain; saffron kept to Korykos
    "kayseri": "horses",          # Caesarea Mazaca, Cappadocia's imperial studs
    "aksaray": "wheat",           # Cappadocian plain; no ancient alum here
    "karahisar_i_sahib": "marble",# Docimium/Synnada pavonazzetto, near Afyon
    "konya": "wool",              # Lycaonia's huge flocks (Strabo 12.6.1)
    "kizilca": "clay",            # interior Phrygia; alum belt is Phocaea/Gediz
    "ayas": "fish",               # Cilician port; cotton is a later import
    "larnaca": "salt",            # Cyprus salt lake, ancient salt pans
    "limassol": "wine",           # Cyprus vine country; sugar is Arab-era
    "morphou": "olives",          # Cyprus groves; cotton is anachronistic
    "mut": "lumber",              # Cilicia Trachea timber; cotton anachronistic
    "anavarza": "fiber_crops",    # Cilicia Campestris flax, not Korykos saffron
    "hargan": "iron",             # Taurus ore; no ancient Cilician tin
    "tarsus": "livestock",        # goat-hair cilicium cloth, not Byzantine silk
    "corycus": "saffron",         # Pliny/Strabo: best crocus from Mt Corycus
    "bandirma": "marble",         # opposite Proconnesus (Marmara I.), not alum
    "lapseki": "wine",            # Lampsacus wine, noted by ancient authors
    "bursa": "lumber",            # Mysian Olympus forest; silk is Ottoman-era
    "balikesir": "wool",          # inland Mysian sheep country, not cotton
    "bergama": "medicaments",     # Pergamon's Asclepeion, Galen's healing shrine
    "nalli": "legumes",           # upper Sakarya valley; rice anachronistic
    "sogut": "lumber",            # Phrygian/Bithynian hill forest, no attested spa
    "akyazi": "lumber",           # Sakarya valley Bithynian forest, not silk
    "eregli": "lumber",           # Heraclea Pontica timber port; coal is C19
    "giresun": "fruit",           # ancient Cerasus, cherries (Pliny NH 15.102)
    "safranbolu": "livestock",    # Paphlagonian upland; saffron kept to Korykos
    "trebizond": "beeswax",       # Trapezus "mad honey" country (Xen. Anab. 4.8)
    "khupati": "fur",             # eastern Pontic forest frontier, not cotton
    "alasehir": "wine",           # Philadelphia's vineyards, not Byzantine silk
    "balat": "wool",              # ancient Miletus, prized Milesian wool
    "nazilli": "fruit",           # Maeander valley orchards; cotton is modern
    "isparta": "wool",            # Pisidian highland flocks, not cotton
    "tavas": "wool",              # Lycus valley sheep country, not Korykos saffron
    "manisa": "olives",           # Mt Sipylus groves; cotton is modern-era
    "smyrna": "fruit",            # the famed Smyrna fig, not Korykos-only saffron
    "ayasuluk": "wine",           # Ephesian wine (named good), not silk
}
# Egypt: the annona of Constantinople, Delta linen and papyrus, Wadi Natrun's natron, Aswan granite, Alexandrian
# glass; cotton only in the oases (the Kellis texts) and Nubia. Rice and sugar came with the Arabs.
AEGYPTUS = {
    "alexandria": "sand",         # Alexandrian glass, famed export ware (Strabo, Martial)
    "wadi_el_natrun": "salt",     # Wadi Natrun natron, embalming/glass salt since Pharaonic era
    "dakahla": "wheat",           # Delta annona grain; rice is Arab-era, not 4th c.
    "al_mima": "wheat",           # Delta annona grain; rice anachronistic
    "menouf": "fiber_crops",      # Delta flax/linen; rice anachronistic
    "giza": "stone",              # Tura limestone quarries fed Roman-era building; no sugar yet
    "bilbeis": "wheat",           # Sharqia Delta grain; cotton not a Delta crop in 395
    "el_mahalla": "fiber_crops",  # Delta flax/linen weaving town; cotton anachronistic here
    "fuwa": "fish",               # On Rosetta branch/Burullus lagoon; sugar anachronistic
    "mansoura": "wheat",          # Delta grain; sugar cane arrives with Arab conquest
    "el_buwit": "wheat",          # Nile valley grain village; sugar anachronistic
    "akhmim": "fiber_crops",      # Panopolis, ancient flax/linen weaving center
    "el_bahnasa": "fiber_crops",  # Oxyrhynchus, papyrus/flax; famed papyri finds
    "aswan": "stone",             # Aswan granite quarries (obelisks, Pompey's Pillar), not iron
    "esna": "wheat",              # Nile valley grain; sugarcane is medieval Egypt
    "hiw": "wheat",               # Diospolis Parva, Nile grain; sugar anachronistic
    "el_qoseir": "incense",       # Myos Hormos-area Red Sea port, incense/spice trade (Periplus)
    "kharga": "cotton",           # Kellis texts attest 4th c. cotton in Kharga oasis
    "baris": "fruit",             # Kharga oasis dates; sugar anachronistic
    "el_qasr": "cotton",          # Dakhla oasis, near Kellis; 4th c. cotton attested
}
# The Orient and Mesopotamia: Tyrian and Sidonian purple, Belus glass sand, Gaza wine, the olive boom of the Dead
# Cities, Hit's bitumen; rice stays in southern Iraq, where the Sasanians grew it.
ORIENS = {
    "antioch": "wheat",           # Amuk plain grain; no sericulture in Syria before c.552
    "arsuz": "fish",              # Cilician-Syrian coast; no ancient cotton here
    "idlib": "olives",            # heart of the Limestone Massif oil-press boom (Dead Cities)
    "acre": "sand",               # Belus/Na'aman sand, Pliny's glass-sand source, by Ptolemais
    "gaza": "wine",               # Gaza jars (LRA4) shipped Gaza wine across the Mediterranean
    "aleppo": "olives",           # edge of Limestone Massif olive-oil region, no ancient cotton
    "dabiq": "wheat",             # Aleppo grain plain, no ancient cotton
    "marrat": "olives",           # Ma'arrat al-Numan, core of the Dead Cities oil region
    "maskanah": "wheat",          # Euphrates grain plain, no ancient sugar
    "zardana": "olives",          # Jabal Barisha, Dead Cities oil-press zone
    "bosra": "wheat",             # Bostra, Hauran "granary of Rome", no ancient cotton
    "suwayda": "wine",            # Jabal al-Druze, ancient Hauran wine-press remains
    "latakia": "wine",            # Laodicea's wine, attested by Strabo and exported
    "deir_qamar": "lumber",       # Mount Lebanon cedar country; no sericulture pre-552
    "sidon": "dyes",              # Sidonian murex purple, attested since Homer/Pliny
    "sughar": "fruit",            # Zoara, Dead Sea palm oasis, dates
    "tadmur": "fruit",            # Palmyra = "palm city", oasis date groves
    "taybah": "wheat",            # Syria-Euphrates grain, no ancient cotton
    "urfa": "wheat",              # Edessa plain grain; no sericulture before c.552
    "siverek": "wheat",           # upper Mesopotamia grain; saffron is an Arab-era crop here
    "ergani": "copper",           # Ergani Maden, copper worked since antiquity
    "haditha": "fruit",           # middle-Euphrates palm groves, no ancient sugar
    "rahba": "fruit",             # Euphrates oasis dates, no ancient sugar
    "hasankeyf": "wheat",         # Tigris valley grain, no ancient cotton
    "tunanir": "wheat",           # Khabur valley grain, no ancient cotton
    "viransehir": "livestock",    # Tektek steppe pasture, no ancient cotton
    "qayyarah": "medicaments",    # ancient naphtha/bitumen seeps near Nineveh
    "baghdad": "wheat",           # Mesopotamian alluvium grain, no ancient cotton
    "balad_ruz": "wheat",         # Diyala grain plain, no ancient cotton
    "dayr_aqul": "wheat",         # central-Iraq grain; sugar cane is 6th-c. Khuzestan
    "basra": "rice",              # southern-Iraq marsh rice (Sasanian); sugar is later
    "samawa": "rice",             # southern Iraq/Euphrates, rice attested in Sasanian era
    "ilam": "wheat",              # Zagros foothill valley farmland, no glass-sand source
    "hit": "medicaments",         # Is/Hit bitumen springs, Herodotus, Babylon's walls
    "kirkuk": "medicaments",      # Baba Gurgur naphtha fires, Herodotus and Plutarch
    "erbil": "wheat",             # Arbela grain plain, no ancient cotton
    "samarra": "wheat",           # Tigris grain plain, no ancient cotton
    "wasit": "rice",              # southern-central Iraq, rice attested in Sasanian era
    "ayn_tamr": "fruit",          # "spring of dates", ancient palm oasis
}
# The Caucasus: Svaneti's fleece-washed gold, Armenian karmir red, Kakhetian wine, Armenia's tribute horses;
# Shirvan's silk is medieval.
CAUCASUS = {
    "ushguli": "goods_gold",      # Soanes/Svaneti: Strabo 11.2.19 gold washing
    "surmali": "dyes",            # Ararat plain: Armenian scale-insect red in antiquity
    "ahlat": "wool",              # Armenian highlands: local silk sericulture postdates 395
    "gremi": "wine",              # Kakheti: ancient wine; Georgian silk is later
    "shamakhi": "wheat",          # Shirvan: Caspian silk trade is medieval
    "pertek": "livestock",        # Pertek: no demonstrated Roman-era spa supports medicaments
    "varsan": "wheat",            # Arran: no ancient spa source supports medicaments
    "niyazabad": "fish",          # Caspian coast: fish; no ancient medicinal source
    "qobustan": "livestock",      # Qobustan uplands: grazing fits better than cotton
    "sotk": "livestock",          # Sotk highlands: grazing fits better than cotton
    "kars": "horses",             # Armenia: Strabo 11.14.9 records foal tribute
}
# Medieval industries, and Sicily's sulfur mines, whose bonus is to gunpowder saltpeter
MEDIEVAL_MODIFIERS = ("england_wool_base", "yorkshire_cloth_base", "flanders_fine_cloth_base",
                      "toledo_weaponry_base", "milan_weaponry_base", "tuscany_fine_cloth_base", "venice_glass_base",
                      "kutna_hora_silver_mines_base", "sicily_sulfur_mines", "idrija_base", "kremnica_gold_mines",
                      "nile_delta_rice_base", "nile_delta_sugar_base", "nile_delta_cotton_base")


# Flavour text: the goods marker's tooltip shows a location's own description (<location>_desc) under its modifier.
# Every location with one of our modifiers gets its modifier's text; the cities vanilla had described for 1337 get
# their own for 395. Written to localization/english/replace/, since it replaces vanilla's where those exist.
FLAVOR_OUT = b.MOD / "main_menu/localization/english/replace/tfe_location_flavor_l_english.yml"
FLAVOR = {
    "tfe_granary_of_rome": "The wheat fields of the Bagradas valley and Byzacena are among the richest in the "
                           "Mediterranean. Their grain is paid as tax and shipped from Carthage to feed Rome.",
    "tfe_pannonian_recruiting_grounds": "Pannonia gave the legions their hardest recruits and the Empire its "
                                        "soldier-emperors, from Probus of Sirmium to Valentinian of Cibalae. Its "
                                        "villages still send their sons to the army.",
    "tfe_latifundia": "The senators' villas swallowed the small farms long ago. Their fields are given over to vines, "
                      "olives and herds worked by coloni, and the bread the city eats comes by sea from Africa.",
    "tfe_annona_militaris": "The Po plain is good grain land, but its land tax is paid in kind. Carts of wheat go "
                            "to the state granaries for the court and the armies of the Alpine frontier, and much of "
                            "the harvest never reaches the market.",
}
CITY_FLAVOR = {
    "tunis": "Carthage, capital of Africa Proconsularis and the greatest city of the West after Rome. In every "
             "sailing season the grain fleet leaves its harbours for Portus, carrying the bread of Rome.",
    "rome": "The Eternal City no longer houses an emperor, but it is still the seat of the Senate and the Bishop of "
            "Rome. Its people eat free bread baked from African wheat, landed at Portus and carried up the Tiber, "
            "while the fields of the Campagna have gone to villas and pasture.",
    "milano": "Mediolanum, seat of the western court since Diocletian and city of the bishop Ambrose. The court, the "
              "palace guard and the field army eat the grain of the plain around it, collected as tax.",
    "pavia": "Ticinum on the Ticino, a garrison town on the road from Milan to the Alps. Its granaries hold the tax "
             "grain of the plain for the army.",
    "cremona": "Cremona on the Po, a Roman colony since 218 BC. The grain of its fields goes downriver to the state "
               "granaries.",
    "mantova": "Mantua, Virgil's birthplace, among the marshes of the Mincio. Its farmers pay their tax in grain.",
    "ferrara": "The marshes of the lower Po, thinly farmed. What grain they grow is gathered for the annona.",
}


def overrides(anc, topo, unownable, raw, mods):
    out = {l: {"raw_material": "wheat", "modifier": "tfe_granary_of_rome"} for l in GRANARIES}
    out |= {l: {"raw_material": g} for l, g in ITALIAN_VILLAS.items()}
    out |= {l: {"modifier": None} for l, m in mods.items() if m in MEDIEVAL_MODIFIERS}
    roman_world = (BRITANNIA | GAUL | HISPANIA | ITALIA | AFRICA | RAETIA_NORICUM | CALEDONIA_HIBERNIA | ILLYRICUM
                   | GRAECIA_THRACIA | BARBARICUM | ANATOLIA | AEGYPTUS | ORIENS | CAUCASUS)
    out |= {l: out.get(l, {}) | {"raw_material": g} for l, g in roman_world.items()}
    for l, path in anc.items():
        if len(path) > 3 and path[3] in PANNONIA and topo.get(l) in b.LAND_TOPO and l not in unownable:
            out[l] = out.get(l, {}) | {"modifier": "tfe_pannonian_recruiting_grounds"}
        elif (len(path) > 3 and path[2] == "italy_region" and path[3] not in ITALIAN_ISLANDS
              and raw.get(l) == "wheat" and l not in ITALIAN_VILLAS):
            out[l] = {"modifier": "tfe_annona_militaris" if path[3] in ITALIA_ANNONARIA else "tfe_latifundia"}
    return out


def apply(text, changes):
    seen = set()
    def one(m):
        name, body = m.group(1), m.group(2)
        if name not in changes:
            return m.group(0)
        seen.add(name)
        for k, v in changes[name].items():
            if v is None:
                body = re.sub(rf" {k} = \w+", "", body)
            elif re.search(rf"\b{k} = \w+", body):
                body = re.sub(rf"\b{k} = \w+", f"{k} = {v}", body)
            else:
                body = f" {k} = {v}" + body
        return f"{name} = {{{body}}}"
    text = re.sub(r"^(\w+) = \{([^{}\n]*)\}", one, text, flags=re.M)
    missing = set(changes) - seen
    assert not missing, sorted(missing)
    return text


def vanilla_and_changes():
    vanilla = (b.MAP / "location_templates.txt").read_text(encoding="utf-8-sig")
    raw = dict(re.findall(r"^(\w+) = \{[^\n]*\braw_material = (\w+)", vanilla, re.M))
    mods = dict(re.findall(r"^(\w+) = \{ modifier = (\w+)", vanilla, re.M))
    return vanilla, overrides(b.load_hierarchy(), b.load_topography(), b.load_unownable(), raw, mods)


def build():
    vanilla, changes = vanilla_and_changes()
    return "# GENERATED by tools/location_templates.py from vanilla's - do not edit\n" + apply(vanilla, changes)


def flavor():
    _, changes = vanilla_and_changes()
    lines = [f' {l}_desc: "{CITY_FLAVOR.get(l, FLAVOR[c["modifier"]])}"'
             for l, c in sorted(changes.items()) if c.get("modifier")]
    return "l_english:\n" + "\n".join(lines) + "\n"


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8-sig")
    FLAVOR_OUT.write_text(flavor(), encoding="utf-8-sig")
    print(f"wrote {OUT} and {FLAVOR_OUT}")
