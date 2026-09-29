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
MEDIEVAL_MODIFIERS = ("england_wool_base", "yorkshire_cloth_base", "flanders_fine_cloth_base",
                      "toledo_weaponry_base")


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
    out |= {l: out.get(l, {}) | {"raw_material": g} for l, g in (BRITANNIA | GAUL | HISPANIA).items()}
    for l, path in anc.items():
        if len(path) > 3 and path[3] in PANNONIA and topo.get(l) in b.LAND_TOPO and l not in unownable:
            out[l] = {"modifier": "tfe_pannonian_recruiting_grounds"}
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
