"""Vanilla's advances in 395-895: the ones we move, cut, re-root or re-gate, and the names of the ones we rename.

Writes REPLACE: copies of only the advances we change, read from vanilla each run, so a patch is one rerun.
Data source for the tables: docs/advance-audit.md. Keys never change; only age, requires, potential, fields and loc.

The engine wants every `requires` to name an advance of the same age, and a cut advance (potential `always = no`) locks
everything that requires it. So a moved or cut advance's dependents are re-rooted by `requires()`: each takes the
nearest ancestor that is still live and in its own age (REQUIRES overrides that for a hand-picked parent). A moved
advance starts a root in its new age unless REQUIRES gives it a parent there.
"""
import functools
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import borders as b  # noqa: E402  (b.GAME: vanilla's game folder)
from lint_script import parse  # noqa: E402
from pdx.core import Node, from_entries, render  # noqa: E402

FOLDER = "in_game/common/advances"
OUT = "in_game/common/advances/tfe_vanilla_advances.txt"
LOC = "main_menu/localization/english/replace/tfe_advances_l_english.yml"

# Rule B (agreed 2026-10-03): to the age where it happened. Each starts a root there; REQUIRES may give it a parent.
MOVE: dict[str, str] = {
    "geo_georgian_script": "age_2_renaissance",
    "irish_monastacism_advance": "age_2_renaissance",
    "pest_house_advance": "age_3_discovery",
    "the_pentarchy": "age_3_discovery",
    "anagignoskomena": "age_3_discovery",
    "salic_law_advance": "age_3_discovery",
    "semi_salic_law_advance": "age_3_discovery",
    "partition_inheritance_advance": "age_3_discovery",
    "peasants_rights_laws_advance": "age_3_discovery",  # audit: "move earlier"; Justinian's laws on the coloni
    "windmills_advance": "age_4_reformation",
    "onmyodo": "age_4_reformation",
    "copperworking": "age_4_reformation",
    "porcelain_kiln_advance": "age_4_reformation",
    "hachiman_worship": "age_5_absolutism",
    "filioque_issue": "age_6_revolutions",
    "heian_kyo": "age_6_revolutions",
    "matsuri": "age_6_revolutions",
    "ira_shahnameh": "age_6_revolutions",
    "marcher_lords": "age_6_revolutions",
    "christianization_of_the_slavs": "age_6_revolutions",
    "cyril_and_methodius": "age_6_revolutions",
    "fortress_church_advance": "age_6_revolutions",
    # Slavery laws open with Rome (see RENAME).
    "slave_trade_act_advance": "age_1_traditions",
}

CUT: set[str] = {
    # Rule D: no period equivalent.
    "pan_amalgamation_advance", "patio_process_advance", "opera_house_advance", "stock_exchange_advance",
    "central_bank_advance", "nation_state_advance", "route_to_the_indies_advance",
    # Rule A, age 1
    "unlock_crusader_knights_advance", "greek_group_the_spirit_of_resistance_advance", "italy_great_families",
    "wallachian_tradition", "netherlandish_protoindustry", "flemish_cloth_making", "scottish_morale",
    "peel_towers_advance", "scandinavian_bergslag_privileges_advance", "scandinavian_tar_privileges_advance",
    "paik_system_advance",
    # age 2
    "unlock_reformed_crusader_knights_advance", "iberian_caravel", "hispano_moresque_style", "saiger_process",
    "swiss_mercenaries", "the_swiss_confederation", "polders_advance", "bng_habshi_generals", "bng_rupees",
    "federal_constitution", "wake_of_the_mongol_horde",
    # age 3
    "rmn_the_byzantine_heirs", "romanian_the_letter_of_neacsu", "landsknechte", "military_traditions", "comets",
    "modernized_royal_scots_navy", "unlock_late_gallowglass_advance", "arm_melikdom_organization",
    "judaism_court_patronage_banking", "gozan_jissetsu", "jap_ashigaru", "jap_wandering_ronin", "paik_regiments_advance",
    "mhr_tradition_of_military_service", "dai_giao_chi_arquebus", "rais_of_the_navy", "maghrebi_galiots",
    "andalusi_arquebusiers", "spa_viceroyalties",
    # age 4
    "spanish_square", "copper_bottoms", "tercio", "iberian_galleon", "maghrebi_xebec", "subsaharan_musketeer_corps",
    "greek_group_the_phanariote_network_advance", "romanian_the_postelnic_bureaucracy", "netherlandish_ship_building",
    "saxon_defensioner", "gebirgsschutzen_infantry", "swiss_religious_refuge", "geo_dasturlamali",
    "geo_sadrosho_districts", "bng_artillery_corps", "mhr_ashta_pradhan_advance", "mhr_office_of_the_peshwa",
    "raj_expanded_artillery_arm", "raj_the_purbias", "the_eight_banners", "jap_jokamachi", "photduang",
    "neo_confucianism",
    # age 5
    "balkan_hajduks", "pun_strength_of_the_misls", "mhr_forts_of_maharashtra", "jap_terakoya",
    "judaism_religious_emancipation", "judaism_reform_movement", "deliberative_council", "manchu_script",
    "romanian_the_romanian_renaissance", "danka_system", "jisha_bugyou",
    # age 6
    "rmn_the_pandur_militias", "romanian_the_scoala_ardeleana", "nav_royal_basque_society",
    "albanian_the_albanian_alphabet_commission", "npl_the_divya_upadesh", "npl_gurkhas", "pun_reforming_the_punjabi_army",
    "a_new_dawn", "manchu_reborn", "swiss_ambition", "swiss_banking", "kokugaku", "fukko_shinto", "cro_pandurs_recruitment",
}

# A hand-picked parent (same age, not cut) instead of the one requires() would walk up to.
REQUIRES: dict[str, list[str]] = {
    "ira_sasanian_heritage": ["cultural_traditions_law_advance"],  # was feudalism_advance (the feudalism institution)
    "slave_center_advance": ["standardized_coins"],                # was gun_smith_advance
    "road_advance_2": ["construction_speed_revolutions"],          # was the_gold_standard
    "medical_school_advance": ["sanitation_advance"],              # was newspapers_advance (the printing press)
}

# Rule E: vanilla's Roman and Byzantine advances are gated on ROM/BYZ, which TFE's Rome never is.
ROMAN = "tfe_is_roman_empire = yes"
POTENTIAL: dict[str, str] = {
    "aqueduct_system": ROMAN,
    "expanded_aqueduct_system": ROMAN,
    "unlock_legionaries_1_advance": ROMAN,
    "unlock_legionaries_2_advance": ROMAN,
    "rom_restore_the_legions": ROMAN,
    "rom_revival_of_arts_and_culture": ROMAN,
    "rom_provincial_governors": ROMAN,
    "byz_autokratoria_rhomaion": ROMAN,
    "byz_modernized_strategikon": ROMAN,
    "ira_sasanian_heritage": "OR = { tag = SAS has_or_had_tag = IRA culture = { has_culture_group = culture_group:iranian_group } }",
}

STRIP: dict[str, set[str]] = {
    "banking_advance": {"can_sell_bonds"},
    "merchant_power_from_maritime_absolutism_advance": {"trade_company_headquarters_level"},
    # Part 3 adds the colonial_range grants here.
}

RENAME: dict[str, tuple[str, str]] = {
    # --- Age 1, Theodosius
    "slave_trade_act_advance": ("Roman Slave Law",
        "Rome's law knows the slave as a thing that can be bought, sold and set free, and every people that "
        "trades with Rome learns that law."),
    "medieval_administration": ("Dioceses and Prefectures",
        "Diocletian's reforms cut the provinces small and set prefects and vicars over them."),
    "scholasticism": ("Patristic Learning",
        "Augustine, Jerome and Ambrose are read and copied in every cathedral school, and the learning of the "
        "Fathers spreads with the faith."),
    "industry_promotion_advance": ("State Workshops",
        "The fabricae of the Empire forge arms and weave cloth under the eye of the state, and the crown can "
        "favour the crafts of the cities it chooses."),
    "castle_advance": ("Burgus",
        "Small fortified towers and strongholds on the frontier give a garrison somewhere to hold when the "
        "legions are far away."),
    "fort_limit_1_advance": ("Limes Forts",
        "Garrison forts are strung along the frontier roads and rivers, and a prefect can hold more of them."),
    "imperial_creed": ("Imperial Creed",
        "Nicene Christianity is the faith of the Empire by Theodosius's law, and the emperor's standing rests on "
        "his care for the Church."),
    "res_publica_christiana": ("Respublica Christiana",
        "We must keep good relations with our fellow Christians of every creed, for the Church spans every "
        "frontier and its bishops write to one another across them."),
    "borjigin_blood": ("Blood of the Great Chief",
        "Our chiefs claim descent from the great war leaders of the steppe, and the clans follow a ruler of that blood."),
    "turco_mongol_tradition": ("Steppe Tradition",
        "Xiongnu, Huns and the peoples after them each took something from the riders before; we are heirs of "
        "them all, and can rule many peoples."),
    "yams_of_the_great_khan": ("Relay Riders of the Great Chief",
        "Fast riders carry the chief's word from camp to camp, with fresh horses waiting at every halt."),
    "kurultai_advance": ("Gathering of the Chiefs",
        "The leaders of every warrior band gather beneath one tent and choose the one they will follow to war."),
    "serfdom": ("Coloni",
        "The coloni are tied to the land they till, and their landlords answer for their rents and their "
        "recruits. The army eats, and the estates grow quiet."),
    "jap_bushido": ("Way of the Bow and Horse",
        "The warrior's conduct is not written down, but it is known: loyalty to his lord, courage in the field, "
        "and no shame at the end."),
    "city_of_scholars": ("Schools of Africa",
        "Carthage, Hippo and Cirta keep schools of rhetoric and grammar that train the best advocates and "
        "bishops of the Empire."),
    "tamazight": ("Tamazight",
        "The Amazigh-speaking tribes, from the Syrtis to the Atlantic, keep their own tongue under every "
        "governor Rome sends them, and their flocks graze the high pastures."),
    "incamisana_advance": ("Huaca Shrines",
        "Stepped platforms of adobe rise above the valley, where priests make their offerings and read the will "
        "of the gods."),
    "tambo_advance": ("Waystations",
        "Rest houses along the roads feed and shelter runners, travellers and soldiers on the march."),
    "mountain_roads": ("Mountain Paths",
        "A network of paths carries goods and runners over the passes and between the valleys."),
    "merchant_officials": ("Publicani",
        "Companies of publicani bid for state contracts and supply the army, and the merchants among them come "
        "to hold office."),
    # --- Age 2, Migrations
    "renaissance_sculptures": ("Spolia and Sculpture",
        "Old statues and columns are reused and new ones carved, and the quarries are worked harder."),
    "renaissance_thought": ("Senatorial Counsel",
        "The notion of a noble council ruling beside the emperor is hardly new, and the counsel of the old "
        "senatorial families opens more offices to us."),
    "renaissance_urbanisation": ("Roman City Planning",
        "Streets laid on a grid, with quarters for workshops and markets, let a city make more of the land around it."),
    "renaissance_court": ("Court of the Rhetors",
        "Poets, rhetors and philosophers crowd the palace, and our culture is known the further for them."),
    "rgo_build_time_advance": ("Brick and Concrete",
        "Masons who know vaults, concrete and brick-faced walls raise great buildings in far less time."),
    "late_feudal_relations": ("Client Kingdoms",
        "Rome rules through client kings who owe it troops and loyalty by treaty, and those bound to us by "
        "treaty are slower to turn."),
    "medieval_military": ("Late Roman Army",
        "The field armies and frontier troops have been reorganised, and discipline and drill hold them steady "
        "in a hard fight."),
    "naval_morale_advance_1": ("Late Roman Fleet",
        "Crews of the provincial fleets drill in coastal waters and know their harbours, and hold together at sea."),
    "subject_integration": ("Absorbing Client Kings",
        "When a client's line fails or its king is deposed, the kingdom is folded into the provinces and its "
        "elites are made citizens."),
    "power_projection_advance_2": ("Imperium",
        "Rome claims the right to command in every land it has ever held, and its ambition outreaches its armies."),
    "crown_power_advance_renaissance": ("Sovereign Majesty",
        "The emperor's sacred person stands above the old orders; senators, curiae and bishops answer to his will."),
    "anatomy_advance": ("Galenic Medicine",
        "Physicians study Galen's anatomy and writings, treat wounds better, and keep more of the sick alive."),
    "pound_lock_canals_advance": ("Canal Locks",
        "Gates of timber and stone hold the water, so barges climb."),
    "slave_center_advance": ("Slave Markets",
        "Dealers gather bondsmen at set markets in the cities, where they are priced, sold and shipped across "
        "the Empire."),
    "university_advance": ("Higher Schools",
        "Rhetors and grammarians teach the sons of the elite in endowed chairs at Rome, Athens, Constantinople "
        "and Alexandria, and the best go on to the law."),
    "art_school_advance": ("Workshops of the Mosaicists",
        "Mosaicists, sculptors and painters train their pupils in set styles, so that the craft does not die "
        "with its masters."),
    "confucian_academy_advance": ("Imperial Academy",
        "The state trains scholar-officials in the classics, and a man who passes its examinations may serve."),
    "national_assemblies_advance": ("Provincial Councils",
        "Delegates of the provincial cities meet each year to petition the governor and the emperor, and the "
        "councils give them a voice."),
    "deus_vult": ("Holy War",
        "Those who do not share our faith are our enemies, and God wills that we fight them."),
    "empiricism": ("Observation of Nature",
        "Things are learned by looking at them closely and writing down what is seen, and law made on what is "
        "known is better law."),
    "privateers": ("Corsairs",
        "Raiding enemy shipping is a poor man's navy; we shall license captains who prey on our enemies' coasts."),
    "paper_guild_cloth_maintenance_advance": ("Rag Paper",
        "Cotton too worn for cloth is pulped and pressed into paper, and the paper-makers keep their cloth supply."),
    "italian_condottieri": ("Great Captains",
        "Our land is known for its great soldiers, whether in the emperor's service or hired out to whoever "
        "pays, and hiring a mercenary and his captain costs less."),
    "slave_soldiers": ("Servile Troops",
        "Our rulers keep corps of bought and freed slaves, loyal to their master alone, and these give us sturdy "
        "infantry and growing numbers."),
    "german_river_toll_castle_advance": ("River Tolls",
        "Strongholds on the great rivers stop every boat and take the lord's toll before they let it pass."),
    "german_mountain_toll_castle_advance": ("Pass Tolls",
        "A tower over the pass takes a toll of every cart and mule that climbs it."),
    "greek_group_hesychast_traditions_advance": ("Ascetic Tradition",
        "The desert fathers and those who follow them teach a life of silence and prayer, and monasteries fill "
        "with men who copy books and write down their sayings."),
    "romanian_the_foundation_of_the_voivodeship_tradition": ("Rule of the Knezes",
        "In the hills and valleys the war leaders of the villages are named knezes and judges, and one of them "
        "holds the rest together."),
    "raj_reorganized_rajput_regiments": ("Clan Contingents",
        "The clan structures that have always filled our armies are drilled into steadier bodies of men."),
    "kainerekowa": ("Law of the Longhouse",
        "We keep faith with the Peacemaker's law, which binds the nations of the longhouse to council before "
        "they go to war, and the weariness of war fades sooner."),
    "mourning_wars": ("Adoption of Captives",
        "When a family has lost one of its own, its women ask for captives to take his place, and war brings new "
        "people into the tribe."),
    "jap_ichiban_yari": ("First Blow",
        "To strike the first blow is an honour and a good omen, and our warriors charge eagerly to claim it."),
    "jap_shinobi": ("Spies and Scouts",
        "Some of our people have long made a trade of watching others and carrying word, and the lords of the "
        "land pay them well."),
    "jap_head_hunting": ("Battle Trophies",
        "A warrior's deed is worth little unless it can be shown, and trophies taken from the fallen carry his "
        "name home."),
    "nanto_rokushuu": ("Continental Learning",
        "Scholars from across the sea bring writing and the teachings of the sages, and the best families keep "
        "clerks and teachers."),
    "honji_suijaku": ("Kami and Foreign Gods",
        "The local kami are read as faces of the gods of other lands, and the clergy of both are content."),
    "xuanzang_travels": ("Faxian's Journey",
        "Faxian, a Chinese Buddhist monk, travelled to India for the sacred texts and came home with them, and "
        "his account makes our name known abroad."),
    "judaism_tikkun_mysticism": ("Merkabah Mysticism",
        "Our mystical school contemplates the divine chariot and the heavenly halls, and the pious find in it a "
        "way to bring the world nearer to God."),
    "albanian_the_stradioti_tradition": ("Illyrian Horsemen",
        "The poverty of our mountains has made our men the finest light horsemen, hired by every emperor and king."),
    # --- Age 3, Justinian
    "matchlock_gun": ("Hunting Traditions",
        "Better bows, spears, snares and nets, and hunters who know the animals' paths, bring in more fur and game."),
    "pike_square": ("Shield Wall",
        "Heavy infantry stand shoulder to shoulder behind a wall of shields and spear-points and hold against a "
        "charge, and our battle tactics improve."),
    "standardized_pikes": ("Spear Levy",
        "A spear is a simple weapon, and spears of one length and make are easy to store and issue, so a levy "
        "can be armed and fed in the field."),
    "correct_box_advance_discovery": ("Tribunes",
        "Tribunes and decurions lead the troops under the commander, and orders reach the line so that the army "
        "fights closer to its plan."),
    "overseas_trade": ("Distant Markets",
        "Merchants and shippers push farther across the Mediterranean, the Red Sea and the Atlantic, and our "
        "trade reaches new markets."),
    "additional_merchants": ("Collegia of Merchants",
        "Merchants form collegia in every port, and their numbers and standing grow."),
    "maritime_advance_age_3": ("Coastal Fleets",
        "Patrol and trade fleets keep to the coasts and chart the harbours, and they reach farther each year."),
    "exploration_maintenance_advance": ("Seaworthy Hulls",
        "Ships built of well-seasoned timber on strong keels stand long voyages and need less patching."),
    "naval_ambitions": ("Mastery of the Sea",
        "A navy that believes it rules the waves sails farther and fights harder."),
    "beat_to_windward_advance": ("Lateen Rig",
        "Triangular sails let a ship sail closer to the wind, so voyages are quicker and surer."),
    "new_world_crops": ("Heavy Plough",
        "The heavy plough with coulter and mouldboard turns the wet clay lands of the north, and fields that "
        "were forest bear grain."),
    "new_currency_demands": ("Small Change",
        "Growing trade needs small coin, and the demand for the copper and tin that coins and bronze work are "
        "made of goes up."),
    "faceting": ("Lapidaries",
        "Master gem-cutters work stones for the crowns and belts of emperors and kings, and the demand for "
        "jewels rises."),
    "saiger_process_discovery": ("Cupellation",
        "Smelters refine silver out of lead ore by cupellation, as the Romans did, to fill the mints."),
    "blast_furnace": ("Improved Bloomeries",
        "Taller bloomery furnaces with water-driven bellows make more iron from the same ore."),
    "lazaretto_advance": ("Plague Houses",
        "After the Plague of 541 cities set aside houses where the sick are kept apart from the healthy."),
    "house_of_parliament_advance": ("Senate House",
        "A hall where the senators or councillors of a city meet, debate and vote."),
    "arts_academy_advance": ("Palace Academy",
        "A palace academy gathers poets, painters and philosophers under the emperor's patronage."),
    "ships_penny": ("Ship Levy",
        "Coastal cities that cannot build ships pay a levy to those who can, and ships are built faster."),
    "merchant_adventures": ("Sea Venturers",
        "Merchants share the risk and the profit of a voyage, and our sea routes grow more efficient."),
    "basic_financial_instruments": ("Bills of Credit",
        "A merchant can pay in one port against a bill drawn in another, and trade becomes safer and surer."),
    "surgery_advance": ("Surgery",
        "Field surgeons set bones, cauterise wounds and cut out arrows, and fewer men die of their wounds."),
    "greek_group_stratioti_levies_advance": ("Limitanei",
        "Frontier soldiers settled on the land and bound to defend it give us hardy light horsemen who know the hills."),
    "trampling_horde": ("Trampling Horde",
        "Attila made the world tremble with his conquests, and we will do the same."),
    "printing_of_religious_texts": ("Scriptoria",
        "Monasteries and cathedral schools copy Scripture and the Fathers by hand and send the codices out, and "
        "new learning takes root more cheaply."),
    "frisian_legend_grutte_pier": ("The Legend of Redbad",
        "Tales are told of a Frisian king who held his marshes against the Franks, and our sea captains take "
        "heart from them: raiding the enemy's shipping is honourable."),
    "nav_people_of_the_sea": ("People of the Sea",
        "From the harbours of the Basque coast, hardy crews man fishing boats and warships alike and know the "
        "Biscay waters better than any."),
    "cir_multireligious_society": ("Religious Coexistence",
        "Our lands are crossed by Christian, Jewish and pagan traders and settlers, and we have learned to let "
        "each keep their own rites."),
    "ira_persian_rug_production": ("Persian Carpets",
        "Persia has long been famous for its carpets and rugs, and the looms of its towns work for courts from "
        "Constantinople to China."),
    "iconostasis": ("Templon",
        "The wall between nave and altar is hung with icons and carved into a screen, and patrons pay well for "
        "its painters."),
    "raj_fortress_architecture": ("Fortress Architecture",
        "Hill forts and walled cities rise across the plains and hills, and every raid taught the builders "
        "where the walls must be thickest."),
    "dai_ca_tru": ("Court Singers",
        "Singers and storytellers carry our culture's tales to the great houses, and our name is known the "
        "further for them."),
    "ukrainian_farmlands": ("Pontic Farmlands",
        "The black earth of the lands north of the Euxine yields enough wheat, pulses and flax to feed a nation."),
    # --- Age 4, the Prophet
    "confessional_court": ("Episcopal Court",
        "A court that lets its bishops advise and manage the household spends more wisely, and the people come "
        "to the ruler's faith faster."),
    "pop_promotion_speed_age_4": ("Monastic Clergy",
        "Monasteries take in the sons of farmers and craftsmen and train them as clerks and priests, and a "
        "gifted boy can rise."),
    "crown_power_advance_reformation": ("Anointed Rulers",
        "The ruler is God's anointed, the clergy preach his right to rule, and the crown commands more of its "
        "estates."),
    "gov_reform_reformation_a": ("Mirror for Princes",
        "Bishops and scholars write books that teach a king his duties, and rulers who read them govern with "
        "more offices."),
    "early_modern_administation": ("Palace Bureaus",
        "A larger palace bureaucracy of secretaries, notaries and treasurers lets the crown govern a wider realm."),
    "artists_advance_reformations": ("Icons and Mosaics",
        "Painters of icons and mosaicists fill the churches, and new artists come to the trade with better skills."),
    "merchant_power_from_maritime_reformation_advance": ("Shipping Partnerships",
        "Sea trade needs capital and shared risk, and merchants who join forces for it gain more from the seas "
        "we hold."),
    "maritime_advance_age_4": ("Reach of the Fleets",
        "Ships from our harbours reach every coast of the Mediterranean and beyond, and our presence at sea grows."),
    "leader_recruit_cost_advance": ("Schools of Command",
        "Young men of good houses are trained in the art of command before they are given troops or ships, and "
        "it costs less to train them."),
    "letters_of_marque": ("Sealed Commissions",
        "A sealed commission turns a pirate into a raider of the crown, and every captain can be hired more cheaply."),
    "sturdy_privateers": ("Hardy Corsairs",
        "Corsairs are always in the line of fire, and ships built for the work, and crews who expect it, last longer."),
    "spy_construction_reformation": ("Cipher Offices",
        "Clerks trained to make and break ciphers help build spy networks faster."),
    "intelligence_agency_advance": ("Agentes in Rebus",
        "The agentes in rebus, couriers who also report on officials, give the state eyes in every province."),
    "flintlock_gun": ("Hunting Methods",
        "Hunters learn better ways of baiting, trapping and tracking, and bring in more fur and game."),
    "correct_box_advance_reformation": ("Strategikon Drill",
        "The drill laid down in the military manuals of Maurice's Strategikon makes bodies of troops fight as "
        "they are taught."),
    "combined_arms_advance_reformation": ("Mixed Formations",
        "Armies now fight with horse, foot and archers together, and commanders who use each to cover the "
        "other's weakness gain a bonus."),
    "assault_ability_reformation": ("Storming Parties",
        "Our best and most disciplined troops are picked to storm a breach, and assaults succeed more often."),
    "supply_depot_advance_age_4_reformation": ("Magazines",
        "Grain and fodder stored in fortified magazines let armies march farther from home."),
    "regiment_reinforcement_speed_reformation": ("Reserve Drafts",
        "Regiments are topped up from depots with fresh men, and losses are made good faster."),
    "standardisation_of_calibre": ("Standard Issue",
        "Arms of one pattern are easier to store and replace, and an army can be supplied further."),
    "bole_smelting": ("Hilltop Smelting",
        "Lead is smelted in open-air hearths on windy hilltops, and output rises."),
    "slitting_mills": ("Water-Powered Forges",
        "Watermills drive hammers and rollers that cut iron bars into rods, and iron output rises."),
    "rgo_size_advance_reformation": ("Land Reclamation",
        "New fields are cleared, terraced and drained, and the land supports more labour."),
    "scientific_experimentation": ("Disputation",
        "Scholars test arguments against one another in public, and new ideas spread faster."),
    "naval_morale_advance_3": ("Long Voyages",
        "Crews used to weeks out of sight of land hold their nerve in battle."),
    "national_bank": ("Imperial Treasury",
        "A central treasury gives the ruler a firm hand on coin, minting and loans."),
    "humanist_tolerance": ("Edicts of Toleration",
        "By making room for other creeds, we can calm the tensions between our peoples."),
    "dai_trade_advance": ("Local Trade Contracts",
        "Our existence has been shaped by our great neighbour for too long. To leave our own mark we write our "
        "own contracts with merchants and extend our trade."),
    "judaism_state_credit_apparatus": ("Radhanite Credit",
        "Our traders pool credit across the Frankish, Byzantine and Persian worlds and lend to rulers, and our "
        "loan capacity grows."),
    "judaism_hasidic_movement": ("Wandering Preachers",
        "Preachers carry comfort and the stories of the sages to the common people in every village, and they "
        "bear their burdens more easily."),
    "judaism_rationalist_yeshiva": ("Talmudic Academies",
        "The academies of Sura and Pumbedita debate and write down the Talmud, and the books of their scholars "
        "spread."),
    "noble_officers": ("Comites and Duces",
        "Counts and dukes command our troops, and our nobles see to it that army and navy keep their traditions alive."),
    "conviction_of_sin": ("Penance",
        "Those who have done wrong fall to their knees; public penance under the clergy gives the pious peace "
        "of mind."),
    "gunpowder_empires": ("Engines of Conquest",
        "The caliphs' armies bring great siege engines, mangonels, ballistae and naphtha throwers, across the "
        "desert, and keeping them costs less."),
    "schools_of_thought": ("Schools of Law",
        "Muslim tradition has always prized learning; from the schools of law and theology scholars and ideas "
        "flow outward, and new practices spread more cheaply."),
    # --- Age 5, the Caliphs
    "industrial_expansion_advance": ("Collegia",
        "Craftsmen's collegia grow in the cities, and the state can promote their trades across a wider web of "
        "workshops."),
    "absolute_rulership": ("Autocracy",
        "The ruler stands above every other power, and the crown's authority over the estates grows."),
    "absolutist_court": ("Sacred Palace",
        "The palace is the heart of the realm; courtiers and officers depend on the ruler, and the estates lose ground."),
    "power_projection_advance_5": ("Dream of Universal Rule",
        "As the ruler's power centralises, his officers begin to look abroad, and more governors are placed."),
    "absolutism_agressive_advance": ("Needs of the State",
        "As more regions are consolidated and resources run short, the ruler's claims are enforced with force, "
        "and the anger it stirs is easier to bear."),
    "subject_loyalty_absolutism": ("Oaths of Fealty",
        "Every subject, and every vassal state, swears loyalty to the ruler, and revolt is counted heresy."),
    "absolutism_control_decline_advance": ("Divan",
        "The divan of ministers and secretaries runs the realm by decree and letter, so control over the "
        "provinces decays more slowly."),
    "national_sovereignty": ("Territorial Rule",
        "The ruler's authority comes to be tied to the land rather than to each subject, and new provinces are "
        "folded in faster."),
    "the_constitution": ("Imperial Edicts",
        "The ruler issues written edicts that bind his officials and assemblies, and the shape of government "
        "can be redrawn."),
    "rgo_size_advance_absolutism": ("Estate Management",
        "Treatises on estate management teach lords to farm and mine their land properly, and it supports more labour."),
    "food_advance_absolutism": ("Three-Field Rotation",
        "Fields are divided into three and sown in turn, and the harvest improves."),
    "lumber_improvements_absolutism": ("Water-Powered Sawmills",
        "With the water wheel at our sawmills, we process timber into planks far faster."),
    "cork_stoppers": ("Cooperage",
        "Casks of well-seasoned oak keep wine through long voyages, and the vintners' output grows."),
    "scientific_mapping_advance": ("Geographers' Maps",
        "Geographers at the caliph's court gather reports from travellers and merchants and draw the known "
        "world with new accuracy."),
    "measuring_the_world": ("Measuring the World",
        "Scholars measure the circumference of the earth and the latitude of cities, and distance from the "
        "capital is felt less."),
    "jesuits_bark": ("Bimaristans",
        "Hospitals with trained physicians treat fevers with herbs and bark, and sufferers in the fever lands "
        "live."),
    "merchant_power_from_maritime_absolutism_advance": ("Merchant Colleges",
        "Merchants of the ports form colleges to protect their trade, and their share of the sea's wealth grows."),
    "maritime_advance_age_5": ("Escorted Fleets",
        "Ships travel in escorted fleets that carry more goods with less loss."),
    "ship_building_techniques_absolutism": ("Slipways",
        "Shipwrights haul hulls ashore on slipways and build and repair them in sheltered yards, so builds go faster."),
    "naval_professionalism": ("Standing Fleets",
        "Permanent fleets with salaried crews sail farther without disbanding."),
    "improve_relation_impact_absolutism": ("Chancery of Foreign Letters",
        "A standing chancery, its clerks fluent in many tongues, keeps friendly letters flowing to every court."),
    "spy_construction_absolutism": ("The Barid",
        "The postal system doubles as a network of informers across the realm."),
    "regiment_reinforcement_speed_absolutism": ("Quartermasters",
        "Standing armies have a quartermaster for each regiment, and reinforcements and supplies reach them faster."),
    "medical_school_advance": ("Medical Schools",
        "At Gundeshapur and elsewhere, physicians of many creeds teach and heal side by side, and learned "
        "doctors are trained."),
    "naval_supplies_manufactory_advance": ("Naval Stores",
        "Dockside depots stock timber, pitch, rope and sailcloth for the fleet."),
    "war_college_advance": ("School of War",
        "Officers learn the art of war from the manuals of old and from veterans, and our commanders are better trained."),
    "regimental_camp_advance": ("Standing Camps",
        "Fortified camps train and house the regiments through the winter."),
    "modern_road_advance": ("Paved Roads",
        "Roads laid on a foundation of stone and gravel with a cambered, paved surface carry carts in any weather."),
    "formalized_officer_corps": ("Ranks of Command",
        "Officers are given rank and pay by the crown, not by birth, and our armies show more initiative."),
    "economic_ideas": ("Directed Economy",
        "The crown measures, taxes and directs the wealth of the country, and the economy serves the government."),
    "humanism": ("Learning for All",
        "Mankind is God's highest creation, and the schools teach more people to read and write."),
    "superior_firepower": ("Massed Engines",
        "Massing engines to break an enemy before the final charge is one of the oldest tactics, and our "
        "artillery hits harder."),
    "regimental_system": ("Theme System",
        "Troops raised from set regions are tied to them, and keeping them in the field costs less."),
    "private_to_marshal": ("Rise from the Ranks",
        "Every soldier may become a captain by his deeds, and our heavy infantry fight with greater power."),
    "suez_canal_advance": ("Canal of the Pharaohs",
        "Clear the old canal between the Nile and the Red Sea, silted and abandoned, and ships pass between the "
        "seas again."),
    "zmw_controlling_the_mutapan_riches": ("Gold of the Interior",
        "Gold from the mines and the Zambezi, traded down to the coast, enriches the land."),
    "nav_shipyards_ironworks": ("Yards and Forges",
        "The shipyards of the Cantabrian coast and the iron forges of its river valleys supply the fleets."),
    "spa_naval_reforms": ("Fleets of Three Seas",
        "The coasts of Iberia face the Bay, the Atlantic and the Mediterranean, and its fleets learn each of them."),
    "albanian_the_fortified_kulla_houses": ("Tower Houses",
        "Nobles and wealthy farmers build stone tower-houses against feud and invader."),
    "dai_literary_reform": ("Literary Reform",
        "Our scholars adapt the writing of the classical tongue to our own speech, and literacy spreads."),
    "dai_don_dien": ("Garrison Farms",
        "Soldiers and landless peasants are settled on new land as garrison farmers, and newly won regions are "
        "integrated faster."),
    "advanced_paik_system_advance": ("Paik Companies",
        "The paik levy system matures into a regular body of light infantry."),
    "jewish_group_court_financiers": ("Radhanite Merchants",
        "Our family firms serve the courts of Franks, Byzantines and caliphs, lending and trading, and the tax "
        "collectors favour them."),
    "judaism_international_banking_networks": ("Kinship Networks",
        "Kin spread across Persian, Frankish and Arab lands pass credit and news between them, and our "
        "envoys are many."),
    "free_subjects": ("Freedmen",
        "A freedman who works for himself produces more raw material than a slave who is beaten into the field."),
    "noble_resilience": ("Noble Connections",
        "The war-bands of this land are headed by lesser nobles, and a ruler who befriends them finds troops for hire."),
    # --- Age 6, Charlemagne
    "artists_advance_revolutions": ("Carolingian Illumination",
        "Scribes and painters fill gospels and psalters with illumination, and new artists come with better skills."),
    "war_score_revolutions_advance": ("Just War",
        "Clerics argue what makes a war just, and a ruler who wins on just grounds takes more from the peace."),
    "enlightened_court": ("Palace School",
        "A palace school teaches the sons of nobles and clerks to read the classics, and the court's culture reaches "
        "far."),
    "separation_of_powers": ("Mixed Constitution",
        "Writers recall Polybius, who held that a lasting state mixes the rule of one, of the few and of the many, "
        "and rulers can open more offices."),
    "rights_of_man": ("Capitularies",
        "Written capitularies set out the rights and duties of free men and officials, and the cabinet runs "
        "better under them."),
    "power_projection_advance_6": ("Imperial Ambitions",
        "Rulers who gather many peoples under one crown dream of empire, and their reach is felt abroad."),
    "modern_bureaucracy": ("Missi Dominici",
        "Envoys of the ruler ride in pairs, a count and a bishop, to inspect every province, and provinces are "
        "integrated faster."),
    "crown_power_advance_revolutions": ("Renewed Empire",
        "A ruler who has gathered all powers under him is hailed as emperor, and subjects across the realm see "
        "themselves as one people under him."),
    "government_size_revolutions": ("Assemblies of the Realm",
        "With regular assemblies of nobles and bishops, government grows in size and capacity."),
    "town_rights_rev_advance": ("Seat of Empire",
        "The capital, seat of the ruler, is granted special rights, and the whole realm looks to it."),
    "peasants_rights_laws_advance": ("Law of the Free Peasantry",
        "The law protects the free peasant against his lord's demands, and the coloni of the Empire have a "
        "claim to the soil they till."),
    "diplomatic_range_age_6": ("Distant Embassies",
        "Envoys travel to far courts, Constantinople, Baghdad, Aachen, Chang'an, and our diplomacy reaches farther."),
    "vaccination_advance": ("Public Hospitals",
        "Public hospitals with trained doctors keep the populace healthier and the old longer lived."),
    "quinine": ("Pharmacopoeia",
        "Apothecaries compile pharmacopoeias of drugs and herbs, and medicine for the fevers is known."),
    "construction_speed_revolutions": ("Stone Vaulting",
        "Masons learn to span wider spaces with vaults and domes, and great buildings go up faster."),
    "rotherham_plough": ("Heavy Wheeled Plough",
        "The heavy plough on wheels breaks the heavy soils of the north and feeds more people."),
    "urbanization": ("Revival of Towns",
        "New markets and walled towns draw people from the countryside."),
    "pop_promotion_speed_age_6": ("Service for Land",
        "Service in the household of a great lord lifts men from the farm to rank and land."),
    "iron_mill_advance": ("Hammer Mill",
        "Water-driven trip hammers beat iron bars out of the bloom, and iron output rises."),
    "distiller_mill_advance": ("Alembic Works",
        "Alchemists' alembics distil spirits and perfumes in works large enough to sell them."),
    "repair_at_sea_aorev": ("Careening",
        "Ships are heeled over in deep coastal water, and cleaned and caulked, without a trip to the yard."),
    "advanced_anti_piracy_warfare": ("Coastal Watch",
        "Watchtowers and patrol ships guard the coast, and the pirates have fewer places to hide."),
    "corps_organisation": ("Comitatus",
        "Bands of sworn companions fight beside their lord; units attached to one another keep pace and fight faster."),
    "march_to_the_sound_of_the_guns_advance": ("Forced March",
        "Commanders learn to push troops hard toward the fight."),
    "siege_ability_revolutions": ("Siege Engineers",
        "Specialist engineers direct sapping, mining and engines at the walls."),
    "assault_ability_revolutions": ("Scaling the Walls",
        "Troops trained to go up ladders and through breaches under missile fire carve a path for our army."),
    "artillery_vs_fort_age_6_revolutions": ("Counterweight Trebuchets",
        "Counterweight trebuchets and heavy rams fill the gap between small engines and mining, and walls fall."),
    "correct_box_advance_revolutions": ("Household of the Commander",
        "Commanders keep staffs of officers and clerks who plan the advance and send out orders."),
    "public_punishments": ("Ship's Discipline",
        "Life at sea is full of dangers, and punishments must be harsh; crews who obey hold together in battle."),
    "impulse_warfare": ("Skirmish Tactics",
        "Light troops harass the enemy line before the main body closes, and our morale is steadier."),
    "combined_arms_advance_revolutions": ("Combined Arms Doctrine",
        "Centuries of fighting with horse, foot and archers together have made the doctrine second nature."),
    "conscription_center_advance": ("Muster Field",
        "Free men gather in arms on the muster field each spring."),
    "conscription_advance": ("Levy",
        "All free men of age are bound to serve when the army is called."),
    "smithian_economics": ("Regulated Markets",
        "The state regulates weights, measures and markets and meddles no further, and production runs more efficiently."),
    "global_empire": ("Tributary Provinces",
        "Our commitment to the provinces and tributary kingdoms changes attitudes toward working in them, and "
        "subjects pay more."),
    "overseas_merchants": ("Foreign Quarters",
        "Merchants who settle abroad are granted rights and protection, and our trade reaches farther."),
    "sea_hawks": ("Sea Captains",
        "We focus on war at sea, and our captains and crews raise our naval tradition."),
    "bayonet_leaders": ("Leading from the Front",
        "Men who are well led will follow, so our officers ride at the head of the charge."),
    "national_conscripts": ("Compulsory Service",
        "Service is made compulsory for every free man who is able, and regiments are raised faster."),
    "massed_battery": ("Siege Train",
        "Let us mass our engines in a single siege train, and its destruction will blast a hole in any line."),
    "press_gangs": ("Coastal Conscription",
        "Fishermen and coastal men are bound to serve in the fleet, so ships are repaired and manned easily."),
    "nationalistic_enthusiasm": ("Care for the Army",
        "Giving our troops adequate support is vital to defence, and with good administration the army is cheaper "
        "to keep."),
    "optimism": ("Confident Councils",
        "Victory is won in the council chamber too, and our advances in war weary our people less."),
    "greek_group_the_modern_greek_enlightenment_advance": ("Macedonian Renaissance",
        "Scholars of Constantinople gather, copy and comment on the classics and write new works in the old forms."),
    "dai_thuan_thien": ("Heaven's Mandate",
        "Our ruler holds the mandate of heaven, shown by omens and victory, and the crown's power over the estates "
        "is great."),
    "bng_bengali_industrialization": ("Muslin Weavers",
        "The weavers of Bengal make the finest muslin in the world, and our cloth and fine cloth output grows."),
    "jap_codified_bushido": ("Ideals of Honour",
        "The conduct of the warrior is praised in poems and chronicles, and our prestige fades more slowly."),
    "tribal_modernization_law_advance": ("Settling the Tribes",
        "Tribes that settle under a king take on law and the plough."),
    "international_nobility": ("Families Across Borders",
        "Great families hold lands and kin in many realms, and can send envoys to them."),
    "emancipation": ("Grants of Freedom",
        "Owners who free their bondsmen gain loyal tenants, and the land is held by those who will fight for it."),
    "jewish_group_civic_emancipation": ("The Geonim",
        "The heads of the great academies guide the communities, and under the host states our people rise in "
        "standing."),
    "judaism_mussar_movement": ("Masoretes",
        "Masoretes copy, vowel and fix the text of Scripture, and the clergy's work is held in respect."),
    "judaism_modern_orthodoxy": ("Karaite Scholars",
        "Scholars who debate Scripture against the rabbis make our learning famous."),
    "judaism_positive_historical_movement": ("Responsa",
        "Rabbis answer questions of law from every community, and their answers are copied and cited."),
    # --- The institutions' root advances take their institution's name (script/institutions.py THEMES)
    "feudalism_advance": ("Patrocinium",
        "Where the state cannot protect the poor, a great landlord can. Peasants and small owners commend "
        "themselves and their land to a patron, pay him rent and service, and are defended in return. The "
        "patron's estate grows into a power of its own."),
    "legalism_advance": ("Roman Law",
        "Rome's jurists have written down how a citizen may sue, marry, bequeath and contract, and the codes "
        "of the emperors bind the whole Empire. Where the law is known and its courts sit, a stranger can "
        "trust a bargain and a governor can be held to a rule."),
    "meritocracy_advance": ("The Nine Ranks",
        "Officials are graded in nine ranks by the quality of their character and learning, and the court "
        "rises by recommendation rather than by blood. The system began under the kings of Wei and shapes the "
        "governments of the east."),
    "renaissance_advance": ("Monasticism",
        "Men and women leave the world for a life of prayer and labour under a rule. Their houses clear land, "
        "copy books, shelter travellers and keep the learning of an older age alive."),
    "banking_advance": ("The Solidus",
        "Constantine's gold coin has kept its weight for generations, and the world prices its goods by it. "
        "Where the solidus circulates, bankers lend against it and merchants trust a bargain made in it."),
    "professional_armies_advance": ("Foederati",
        "Whole peoples are settled within the frontier and bound by treaty to fight for the emperor under "
        "their own chiefs. Their warbands are better soldiers than the levies of the provinces, and they know "
        "it."),
    "new_world_advance": ("The Monsoon Trade",
        "Sailors from Egypt and Arabia have learned the rhythm of the monsoon winds and cross the Indian "
        "Ocean to the pepper coasts of India. Each year the ships carry out gold and wine and bring back "
        "spices, cloth and gems."),
    "printing_press_advance": ("The Scriptorium",
        "The codex has replaced the scroll, and monks and clerks copy it by hand in workshops attached to "
        "cathedrals and monasteries. Books grow cheaper and more people learn to read them."),
    "pike_and_shot_advance": ("Mounted Archery",
        "The riders of the steppe and the Persian plateau shoot from the saddle, wheeling and loosing. Their "
        "way of war spreads to every army that has faced them and survived."),
    "confessionalism_advance": ("Religious Law",
        "A faith that writes down its rules makes a community of its believers, with courts of its own. "
        "Councils, synods and schools of jurists set out what the faithful must do, and judges apply it to "
        "the common life."),
    "global_trade_advance": ("The Silk Road",
        "Caravans carry silk, paper and spice across the oases of Central Asia, and the cities along the road "
        "grow rich on tolls and markets. Goods, faiths and ideas pass from hand to hand between China and the "
        "Mediterranean."),
    "artillery_institution_advance": ("Greek Fire",
        "Engineers of Constantinople learn to throw a burning liquid that water cannot put out. The secret of "
        "its making is closely kept, and the fleets and walls it defends are hard to take."),
    "manufactories_advance": ("Paper",
        "Paper, a Chinese art, reaches the workshops of Samarkand and Baghdad. It is cheaper than parchment "
        "and papyrus, and the clerks, merchants and scholars who use it write more."),
    "scientific_revolution_advance": ("The House of Wisdom",
        "Scholars at the caliph's court gather books from every land and translate them into Arabic. In "
        "Baghdad mathematicians, astronomers and physicians set out to test what the ancients wrote."),
    "military_revolution_advance": ("The Heavy Horse",
        "The stirrup and a stronger breed of horse give the armoured rider a seat from which he can couch a "
        "lance. A charge of such men can break an infantry line, and the ruler who can field them has the "
        "upper hand."),
    "enlightenment_advance": ("The Carolingian Renaissance",
        "Charlemagne gathers scholars from every part of Christendom to his court. Schools open at cathedrals "
        "and monasteries, handwriting is made clear, and the Latin classics are copied again."),
    "industrialization_advance": ("The Manor",
        "A lord's estate is farmed in strips by dependent peasants, who owe him labour on his own fields. The "
        "mill, the heavy plough and the three-field rotation make such estates the cell of the northern "
        "economy."),
    "levee_en_masse_advance": ("Feudalism",
        "Land is held in return for military service, and every lord owes his king a body of mounted men. "
        "Counts and their vassals can call up an army for the season and send it home when the campaign is "
        "over."),
}

TAG_GATED = re.compile(r"(?:has_or_had_tag|tag)\s*=\s*(SAX|RMN|ASK)\b")


def _kids(node: Node) -> list[Node]:
    return node.val if isinstance(node.val, list) else []


@functools.lru_cache(maxsize=None)
def vanilla() -> dict[str, Node]:
    out = {}
    for p in sorted((b.GAME / FOLDER).glob("*.txt")):
        for node in from_entries(parse(p.read_text(encoding="utf-8-sig"))):
            if node.key and node.key != "_advances_template" and isinstance(node.val, list) \
                    and any(n.key == "age" for n in _kids(node)):
                out[node.key] = node
    return out


def _field(node: Node, key: str) -> list[str]:
    return [str(n.val) for n in _kids(node) if n.key == key]


@functools.lru_cache(maxsize=None)
def cut_keys() -> frozenset[str]:
    """CUT, plus every advance whose potential names a tag TFE reuses for another people (SAX, RMN, ASK)."""
    keys = set(CUT)
    for key, node in vanilla().items():
        pot = [n for n in _kids(node) if n.key == "potential"]
        if pot and TAG_GATED.search(render(pot)):
            keys.add(key)
    return frozenset(keys)


def age_of(key: str) -> str:
    return MOVE.get(key) or _field(vanilla()[key], "age")[0]


def _live_ancestors(key: str, age: str) -> list[str]:
    """key if it is live and in `age`, else what its vanilla parents resolve to."""
    if key not in cut_keys() and age_of(key) == age:
        return [key]
    return [a for p in _field(vanilla()[key], "requires") for a in _live_ancestors(p, age)]


def requires(key: str) -> list[str]:
    """The `requires` list of a live advance after our moves and cuts."""
    if key in REQUIRES:
        return REQUIRES[key]
    out: list[str] = []
    for r in _field(vanilla()[key], "requires"):
        out += [a for a in _live_ancestors(r, age_of(key)) if a not in out]
    return out


def changed() -> list[str]:
    """every advance we write a REPLACE: for."""
    van, cut = vanilla(), cut_keys()
    keys = set(MOVE) | cut | set(POTENTIAL) | set(STRIP)
    keys |= {k for k in van if k not in cut and requires(k) != _field(van[k], "requires")}
    return sorted(keys)


def _put(node: Node, key: str, vals: list[Node]):
    """replace the first `key` field with vals in place, drop the others; append when there was none."""
    out, done = [], False
    for n in _kids(node):
        if n.key != key:
            out.append(n)
        elif not done:
            out += vals
            done = True
    node.val = out if done else out + vals


def build() -> tuple[str, str]:
    van, cut = vanilla(), cut_keys()
    out = []
    for key in changed():
        node = Node("REPLACE:" + key, "=", list(_kids(van[key])))
        if key in MOVE:
            _put(node, "age", [Node("age", "=", MOVE[key])])
        if key not in cut:
            _put(node, "requires", [Node("requires", "=", r) for r in requires(key)])
        if key in POTENTIAL:
            _put(node, "potential", [Node("potential", "=", from_entries(parse(POTENTIAL[key])))])
        if key in STRIP:
            node.val = [n for n in _kids(node) if n.key not in STRIP[key]]
        if key in cut:
            _put(node, "potential", [Node("potential", "=", [Node("always", "=", "no")])])
        out.append(node)
    out[0].lead = ["TFE: vanilla's advances moved, cut, re-rooted or re-gated for 395-895 (written by script/advances.py)"]
    loc = ["l_english:"] + [f' {k}: "{n}"\n {k}_desc: "{d}"' for k, (n, d) in sorted(RENAME.items())]
    return render(out), "\n".join(loc) + "\n"


def outputs():
    text, loc = build()
    return {OUT: text, LOC: loc}
