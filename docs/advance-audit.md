# Vanilla advances against TFE's ages (audit, 2026-10-03)

Six read-only passes, one per age, over vanilla 1.4's `in_game/common/advances/`. Ages as planned:
1 Theodosius 395-400, 2 Migrations 400-500, 3 Justinian 500-600, 4 the Prophet 600-700, 5 the Caliphs 700-800,
6 Charlemagne 800-895. "Live" means a country in the 395 start can get it. Dead advances (tag, culture or religion
absent in 395) are counted, not listed.

| Age | Total | Live generic | Live restricted | Dead | Flagged |
|---|---|---|---|---|---|
| 1 Theodosius | 675 | ~100 | ~110 | ~475 | ~60 |
| 2 Migrations | 712 | ~120 | ~100 | ~490 | 69 |
| 3 Justinian | 595 | 132 | ~100 | ~338 | ~90 |
| 4 Prophet | 584 | 122 | 79 (+10 once Islam/Miaphysitism exist) | 373 | ~95 |
| 5 Caliphs | 524 | 142 | 54 | 328 | 118 |
| 6 Charlemagne | 469 | 127 | ~53 | ~289 | ~115 |

Actions: **cut** (remove or never-potential), **rename** (keep effect, new name/desc), **rewrite** (new effect too),
**move N** (to age N), **re-root** (change `requires` so it survives a cut parent), **re-gate** (change potential).

## A. Systems (one decision each covers dozens of advances)

1. **Institutions.** 18 vanilla institutions root most generic trees, 3 per age:
   age 1 feudalism, legalism, meritocracy; 2 renaissance, banking, professional_armies; 3 new_world, printing_press,
   pike_and_shot; 4 confessionalism, global_trade, artillery_institution; 5 manufactories, scientific_revolution,
   military_revolution; 6 enlightenment, industrialization, levee_en_masse. Each root advance needs
   `has_embraced_institution`. Vanilla spawns them at Florence, Augsburg, Lisbon and so on, and
   `setup/395/08_institutions.txt` includes 1337's map as is (Stockholm starts with feudalism and legalism in 395).
   Subtree sizes: renaissance ~1/3 of age 2; new_world 136, printing_press 140, pike_and_shot 145; global_trade 186,
   confessionalism 101, artillery 89; manufactories+scientific+military ~60 roots-and-children.
2. **Gunpowder.** Age 2 gunpowder_advance, gun_smith, handgonners, cannon_maker, houfnice; age 3 matchlock_gun,
   arquebusiers, matchlock levy, falconet; age 4 arquebusiers, pistoleers, flintlock levy, chambered cannon, cannon/guns/
   saltpeter workshops, bastion, naval battery; age 5 musketeers, hunters, militiamen, royal mortar, siege cannons,
   cannon foundry, firearms manufactory, putrefaction works, line/gustavian infantry, star fort; age 6 sharpshooters,
   fusiliers, grenadiers, light dragoons, cuirassiers, flying battery, long_rifle, napoleonic_warfare, gun/weapon/
   firearms factories, putrefaction mill. Age 1 hand_cannon_guild (East Asia). Age 2 trap: Hunnic/Alan/cataphract
   cavalry (`unlock_cavalry_advance`, `unlock_heavy_cavalry_advance`) hang off Commissioned Officers, behind gunpowder.
3. **Exploration and colonisation.** Age 1 mapmaking (`may_explore`, immigration law), colonies (`can_colonize`),
   colonial_tradition/heritage, settle_the_frontier; age 2 merchants_and_trade (`colonial_range`), route_to_the_indies;
   age 3 the whole new_world tree (explorer commissions, open sea, cb_exploration, colonial charters/policy/native policy/
   administration, colonial ventures, faster colonists, send-people cabinet actions, plantations, new world crops); age 4
   trade_companies (subject type + 6 buildings), chartered_companies, safe_exploration, land_of_opportunity,
   free_colonies; age 5 additional_colonists, vice_roys, panama canal, colonial_nations; age 6 superior_ship_design,
   joint_stock_companies, eastindiaman, overseas_merchants, colonial_ambition.
4. **Age-of-sail ships.** Age 1 cog; 2 early carrack (hulk, barque mild); 3 carrack, caravel, flute, baochuan, sekibune,
   atakebune, iberian galleon, square-rigged caravel; 4 galleon, war galleon, pinnace, galleass, italian galleass,
   galiot, brig, cakradonya, iberian galleon, xebec; 5 two-decker, frigate, xebec, merchantman, corvettes; 6 threedecker,
   ship of the line, heavy frigate, bomb ketch, archipelago frigate. Galleys, dromon-likes and longships are what fit.
5. **Printing.** Age 3 printing_press root, print_culture, artistic prints, printers shop, paper workshop; age 5
   newspapers (Press Laws), printing manufactory; age 6 printing mill.
6. **Modern finance.** Age 2 banking (bonds); age 4 national_bank; age 5 central_bank, stock_exchange, bookkeeping; age 6
   insurance_companies, the_gold_standard (also gates Basic Roads), clearing_house.
7. **Industry.** Age 6 industrialization, hot blast, cupola, steam engine, beehive ovens, steel mill, railroad, wood pulp
   paper; age 5 coke blast furnace, improved coking, hollander beater.
8. **Feudalism (age 1).** feudalism_advance needs the feudalism institution and is required by 125 advances (8 live:
   Sasanian Heritage, Spirit of Resistance, Noble Knights ...). Unlocks fiefdom subject type, feudal nobility,
   margraviate; plus feudal levy, castle, castellany, royal court, salic/semi-salic/partition laws. windmills ->
   ranching -> horse_riding -> feudalism is a chain.
9. **Later religions.** Catholic, Protestant, Muslim, Miaphysite files are dead in 395. Protestant: cut. Muslim and
   Miaphysite: mostly period-fitting, wake when those faiths are created; fix the few early-modern ones (gunpowder
   empires). Catholic: decide with the Latin/Greek split.
10. **Tag collisions.** TFE reuses vanilla tags, so vanilla advances go live for the wrong people: `SAX` (Saxons get
    Meissen/Wettin: meissen_lion, a_mining_heritage, meissner_groschen, a_resilient_soul, saxon_court,
    a_tolerant_society, meissner_porcelain, saxon_baroque, retablissement, saxon_industrialization), `RMN` (Thaton gets
    Romanian advances), `ASK` (Armenia gets Ashikaga advances). Also the `greek_group`/`italian_group`/`iberian_group`/
    `german_group`/`netherlandish_group`/`maghrebi_group` memberships of TFE's Roman and Germanic cultures wake late
    culture-group advances (listed per age below).
11. **Roman advances that never fire.** Vanilla gates them on ROM/BYZ: aqueduct_system, unlock_legionaries_1/2,
    varangians_2, rom_restore_the_legions, rom_revival_of_arts_and_culture, rom_provincial_governors, 5 country_byz
    (byz_autokratoria_rhomaion, byz_modernized_strategikon ...). Re-gate to EAR / `tfe_is_western_rome`.
12. **Slavery laws.** Only `slave_trade_act_advance` (age 6, "Slave Trade Act" 1807) unlocks `slavery_laws`: rename and
    move to age 1.

## B. Individual advances by age (not covered by A)

### Age 1, Theodosius (395-400)
- windmills_advance (Windmill): move 4, re-root ranching and alchemy first.
- pest_house_advance: move 3 (Plague of Justinian); re-root hospital_advance (keep hospitals, Basil's Basiliad 369).
- medieval_administration: rename (Dioceses and Prefectures).
- scholasticism (Classic Scholasticism): rename (Patristic Learning).
- industry_promotion_advance (Industrial Patronage): rename (State Workshops / fabricae).
- castle_advance, fort_limit_1_advance (Castellany): rename (Burgus, Limes Forts).
- unlock_long_fada: rename (currach) or cut.
- porcelain_kiln_advance: move 4 or rename (Celadon Kiln).
- paper_guild_advance (+ fiber pulp PM): gate to East Asia, or leave.
- fortress_church_advance: cut or move 6.
- unlock_crusader_knights_advance: cut (dead anyway).
- Restricted, live:
  - greek_group_the_spirit_of_resistance_advance (1204 text): rewrite or cut.
  - italy_great_families (unified Italy text, WRE): rewrite or cut.
  - the_pentarchy: move 3; imperial_creed: rewrite (no schism yet); filioque_issue: move 6; anagignoskomena: move 3.
  - res_publica_christiana (Universal Christendom): rename.
  - wallachian_tradition (Carpi, Gepids): cut.
  - netherlandish_protoindustry (Verlagssystem), flemish_cloth_making (Franks, Frisians): cut.
  - scottish_morale, peel_towers_advance (Picts): cut.
  - irish_monastacism_advance (Irish are pagan in 395): move 2, re-root Traveling Bards.
  - scandinavian_bergslag_privileges, scandinavian_tar_privileges: cut.
  - ira_shahnameh (c. 1010): move 6 or cut, re-root ira_persian_plateau.
  - ira_sasanian_heritage: re-gate to include SAS; re-root off feudalism.
  - borjigin_blood, turco_mongol_tradition, yams_of_the_great_khan, kurultai_advance (Huns, Rouran ...): rename.
  - serfdom (Serfs): rename (Coloni). salic_law, semi_salic, partition_inheritance: move 3.
  - heian_kyo, matsuri: move 6; onmyodo: move 4.
  - jap_bushido: rename. mounted_people: drop the iron pagoda cavalry unlock.
  - paik_system_advance (Kamarupa): cut. geo_georgian_script: move 2.
  - city_of_scholars (madrasas): rewrite text. tamazight: rewrite text.
  - incamisana, tambo, mountain_roads (Moche, Nazca): rename. copperworking: move 4. merchant_officials: rename.

### Age 2, Migrations (400-500)
- renaissance_advance + renaissance_sculptures/thought/urbanisation/court, rgo_build_time_advance: rename with the
  institution (A1).
- banking_advance: rewrite as argentarii, drop `can_sell_bonds`.
- late_feudal_relations: rename (Client Kingdoms). medieval_military, naval_morale_advance_1: rename (Late Roman Army /
  Fleet). subject_integration (Consolidation of Titles): rename. power_projection_advance_2 (Supranational Ambitions):
  rename. crown_power_advance_renaissance (Sovereignty): rename. anatomy_advance: rename (Galenic Medicine).
- pound_lock_canals_advance: cut or rewrite (aqueducts, harbours).
- slave_center_advance: re-root off Gunsmith, rename.
- university_advance: rename (Higher Schools). art_school_advance: rename. confucian_academy_advance: rename (Imperial
  Academy).
- unlock_crossbowmen, unlock_men_at_arms: rename. national_assemblies_advance: rename.
- deus_vult (cb_deus_vult): cut. marcher_lords (march subject): move 6 or rename. empiricism: rename. privateers:
  rename (Corsairs). boarding_parties: swap icon. unlock_reformed_crusader_knights: cut.
- unlock_byzantine_cataphracts_2: rename (drop "Byzantine"). paper_guild_cloth_maintenance: rename.
- Restricted, live:
  - iberian_caravel (hispano_roman): cut. italian_condottieri (Romans via italian_group): rename.
  - hispano_moresque_style, slave_soldiers, tuareg_veiled_cavalry (afro_roman, Amazigh): cut or rename.
  - saiger_process, german_river_toll_castle, german_mountain_toll_castle (Germanic peoples): cut or rename.
  - swiss_mercenaries, the_swiss_confederation (Alamanni): cut.
  - greek_group_hesychast_traditions: rename. romanian_the_foundation_of_the_voivodeship_tradition: rename.
  - polders_advance (Franks, Frisians): cut. bng_habshi_generals, bng_rupees: cut. raj_reorganized_rajput_regiments:
    rename.
  - kainerekowa, mourning_wars, federal_constitution (Haudenosaunee): rename or cut.
  - wake_of_the_mongol_horde (any Asian capital): cut.
  - jap_ichiban_yari, jap_shinobi, jap_head_hunting: rename. nanto_rokushuu, honji_suijaku: rename. xuanzang_travels:
    rename (Faxian). judaism_tikkun_mysticism: rename.
  - thai_royal_poets, father_governs_children, dai_nha_nhac, sudano_sahelian_architecture: minor.
  - aristocracy (levy_plated_knights): cut or rename. albanian_the_stradioti_tradition: rename.
  - church_councils fits; unchanging_tradition, religious_icon_power_advance: minor.

### Age 3, Justinian (500-600)
- matchlock_gun (Early Hunting Guns): rename (Hunting Traditions), it gates 82 advances.
- pike_square, standardized_pikes: rename (Shield Wall, Spear Levy). unlock_halberdiers: cut or spear unit.
- correct_box_advance_discovery (Lieutenants): rename.
- overseas_trade, additional_merchants, maritime_advance_age_3, exploration_maintenance_advance, naval_ambitions: rename.
- beat_to_windward_advance: rename (lateen rig). new_world_crops: rename (Heavy Plough). new_currency_demands: rename.
- improved_book_binding: keep. study_institutions, spy_construction_discovery, diplomatic_training,
  formalized_relations: re-root off printing. faceting: rename.
- patio_process_advance: cut or rewrite (cupellation). saiger_process_discovery: rename. blast_furnace: rename
  (Improved Bloomeries), re-root off plantations.
- lazaretto_advance: keep (Plague of 541), reword. house_of_parliament_advance: rename (Curia / Senate House).
  arts_academy_advance: rename. ships_penny, merchant_adventures: rename. basic_financial_instruments, surgery_advance,
  unlock_supply_convoy: reword.
- Restricted, live:
  - rmn_the_byzantine_heirs, romanian_the_letter_of_neacsu: cut.
  - greek_group_stratioti_levies_advance: rewrite (limitanei). landsknechte: cut. military_traditions
    (levy_cavaliers): cut.
  - trampling_horde: reword. printing_of_religious_texts: rewrite (scriptoria).
  - comets, modernized_royal_scots_navy, unlock_late_gallowglass (Picts): cut.
  - arm_melikdom_organization: cut. frisian_legend_grutte_pier: rewrite (Redbad). nav_people_of_the_sea,
    cir_multireligious_society, ira_persian_rug_production: reword. ira_spread_of_persian_influence: re-root.
  - iconostasis: rename (Templon). judaism_court_patronage_banking: cut. hachiman_worship: move 5; gozan_jissetsu: cut.
  - jap_ashigaru, jap_wandering_ronin: cut. paik_regiments, mhr_tradition_of_military_service: cut.
    raj_fortress_architecture, dai_ca_tru: reword. dai_giao_chi_arquebus: cut.
  - ukrainian_farmlands: rename (Pontic Farmlands). rais_of_the_navy, maghrebi_galiots, andalusi_arquebusiers: cut.
    spa_viceroyalties: cut.

### Age 4, the Prophet (600-700)
- confessional_court: rename (Episcopal Court). pop_promotion_speed_age_4: rename (Monastic Clergy).
  crown_power_advance_reformation (Cuius Regio): rename. gov_reform_reformation_a (The Prince): rename (Mirror for
  Princes). early_modern_administation: rename. artists_advance_reformations: rename (Icons and Mosaics).
- merchant_power_from_maritime_reformation (Merchant Companies): rename. maritime_advance_age_4 (Global Fleets): rename.
  leader_recruit_cost_advance, letters_of_marque, sturdy_privateers: rename. spy_construction_reformation,
  intelligence_agency_advance: rename (Agentes in Rebus).
- pan_amalgamation_advance: cut. flintlock_gun: rename (Hunting Methods). correct_box_advance_reformation: rename
  (Strategikon Drill). spanish_square: cut. combined_arms_advance_reformation, assault_ability_reformation: rename.
  supply_depot_advance_age_4: rename (Magazines). maurician_infantry: keep, re-describe as Emperor Maurice's
  Strategikon. regiment_reinforcement_speed_reformation (Powder Flask), standardisation_of_calibre: rename.
  fort_limit_4_advance: re-root off bastion.
- bole_smelting, slitting_mills, rgo_size_advance_reformation (Spinning Wheels), scientific_experimentation,
  naval_morale_advance_3: rename.
- The craft workshops (beer, tanning, cloth, fine cloth, tools, pottery, glass, dyes, furniture): move 1 or 2, re-root.
  The crafts are ancient.
- unlock_pikemen_advance: cut or replace. national_bank: rename (Imperial Treasury). humanist_tolerance: rename.
  copper_bottoms: cut.
- Restricted, live:
  - tercio, iberian_galleon (hispano_roman): cut. maghrebi_xebec: rename or cut. subsaharan_musketeer_corps: cut.
  - greek_group_the_phanariote_network: cut or rename. romanian_the_postelnic_bureaucracy: cut.
  - netherlandish_ship_building (north_sea_shipyards): cut. saxon_defensioner, gebirgsschutzen_infantry,
    swiss_religious_refuge: cut.
  - geo_dasturlamali, geo_sadrosho_districts: cut. bng_artillery_corps, mhr_ashta_pradhan, mhr_office_of_the_peshwa,
    raj_expanded_artillery_arm, raj_the_purbias: cut.
  - the_eight_banners, jap_jokamachi, photduang: cut. dai_trade_advance: rename.
  - judaism_state_credit_apparatus, judaism_hasidic_movement, judaism_rationalist_yeshiva: rewrite (Talmudic academies,
    Radhanites). neo_confucianism (Shinto): cut. noble_officers: rename. conviction_of_sin: rename.
  - Once Islam exists: gunpowder_empires, schools_of_thought: rewrite.

### Age 5, the Caliphs (700-800)
- industrial_expansion_advance: rename (Collegia). absolute_rulership, absolutist_court, power_projection_advance_5,
  absolutism_agressive_advance, subject_loyalty_absolutism, absolutism_control_decline_advance: rename (Autocracy,
  Sacred Palace ...).
- national_sovereignty, the_constitution: rewrite (territorial rule; capitularies).
- rgo_size_advance_absolutism (Physiocracy): rewrite. food_advance_absolutism (Closed Fields): rewrite (three-field
  rotation). lumber_improvements_absolutism: rename (water-powered). cork_stoppers: rewrite (cooperage).
- scientific_mapping_advance, measuring_the_world: reword (Abbasid geographers). jesuits_bark: rewrite (bimaristan).
- merchant_power_from_maritime_absolutism (Chamber of Commerce): rename, drop trade-company effect.
  maritime_advance_age_5, ship_building_techniques_absolutism, naval_professionalism,
  improve_relation_impact_absolutism, spy_construction_absolutism: rename.
- regiment_reinforcement_speed_absolutism (Marshal of Lodgings): rename (Quartermasters).
- medical_school_advance: keep (Gundeshapur), reword, re-root off newspapers. paper_manufactory_advance: re-root.
  naval_supplies_manufactory: rename. The 15 manufactory buildings (cloth, pottery, glass, porcelain, winery ...): rename
  "Workshop", re-root off manufactories.
- opera_house_advance: replace (Hippodrome / Theatre). war_college_advance, regimental_camp_advance: rename.
- unlock_hussars, unlock_gallop_cavalry: rename (Light / Heavy Horse). modern_road_advance: rename (Paved Road).
- formalized_officer_corps, economic_ideas, humanism, superior_firepower, regimental_system, private_to_marshal: rename.
  naval_fighting_instruction: swap icon. suez_canal_advance: rename (Canal of the Pharaohs).
- Restricted, live:
  - zmw_controlling_the_mutapan_riches, nav_shipyards_ironworks, baghlah_advance: rename. unlock_camel_5: replace
    (camel corps without guns).
  - balkan_hajduks: cut. spa_naval_reforms: rewrite. albanian_the_fortified_kulla_houses: rename.
  - dai_literary_reform, dai_don_dien: rewrite. pun_strength_of_the_misls, mhr_forts_of_maharashtra, jap_terakoya: cut.
    advanced_paik_system: rewrite.
  - jewish_group_court_financiers, judaism_international_banking_networks: rewrite (Radhanites).
    judaism_religious_emancipation, judaism_reform_movement: cut.
  - deliberative_council, manchu_script, romanian_the_romanian_renaissance, danka_system, jisha_bugyou: cut.
  - free_subjects, noble_resilience: rewrite. christianization_of_the_slavs, cyril_and_methodius: move 6.
  - unlock_byzantine_cataphracts_5: re-root off military_revolution.

### Age 6, Charlemagne (800-895)
- enlightenment_advance + artists_advance_revolutions, war_score_revolutions_advance: rewrite (Carolingian / Abbasid
  learning: Palace School, House of Wisdom). enlightened_court: rename (Palace School).
- separation_of_powers, rights_of_man, power_projection_advance_6, modern_bureaucracy: rename (Mixed Constitution,
  Capitularies, Imperial Ambitions, Missi Dominici).
- crown_power_advance_revolutions (Nation), government_size_revolutions, town_rights_rev_advance: rename.
  nation_state_advance (merge_culture_group): cut or rename. peasants_rights_laws_advance: rename, move earlier.
- diplomatic_range_age_6 (Global Embassies): rename. vaccination_advance, quinine: rename (Bimaristan, Pharmacopoeia).
- construction_speed_revolutions, rotherham_plough, urbanization: rename (Stone Vaulting, Heavy Wheeled Plough,
  Revival of Towns). pop_promotion_speed_age_6 (Capitalist Social Mobility): rename.
- iron_mill, distiller_mill: reskin. paper_mill_advance: keep (Abbasid paper, 794). road_advance_2: re-root off the gold
  standard.
- repair_at_sea_aorev (Parliamentary Heel): rename. advanced_anti_piracy_warfare: rename (Coastal Watch).
- corps_organisation, march_to_the_sound_of_the_guns, siege_ability_revolutions, assault_ability_revolutions,
  artillery_vs_fort_age_6, correct_box_advance_revolutions, public_punishments, impulse_warfare, combined_arms_revolutions:
  rename (Comitatus, Forced March, Siege Engineers ...). fort_limit_6_advance: re-root off long_rifle.
- conscription_center_advance, conscription_advance: rename (Muster Field, Levy), and they gate the cataphract chain.
  unlock_logistics_corps: rename (Baggage Train).
- smithian_economics, global_empire, overseas_merchants, sea_hawks, bayonet_leaders, national_conscripts,
  massed_battery, press_gangs, nationalistic_enthusiasm, optimism: rename.
- Restricted, live:
  - greek_group_the_modern_greek_enlightenment (all Romans): rename (Macedonian Renaissance).
  - rmn_the_pandur_militias, romanian_the_scoala_ardeleana, nav_royal_basque_society,
    albanian_the_albanian_alphabet_commission, npl_the_divya_upadesh, npl_gurkhas, pun_reforming_the_punjabi_army,
    a_new_dawn, manchu_reborn, swiss_ambition, swiss_banking, kokugaku, fukko_shinto, cro_pandurs_recruitment: cut.
  - geo_georgian_unification: keep. dai_thuan_thien, bng_bengali_industrialization, jap_codified_bushido,
    tribal_modernization_law_advance, international_nobility, emancipation: rename.
  - jewish_group_civic_emancipation, judaism_mussar_movement, judaism_modern_orthodoxy,
    judaism_positive_historical_movement: rewrite (Geonim, Masoretes, Karaites).
  - unlock_byzantine_cataphracts_6: re-root off conscription center.
