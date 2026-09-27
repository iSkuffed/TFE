# EU5 game systems and modding hooks for a Late Antiquity (395 AD) mod

Source convention: `G/` = `/home/skuffed/.local/share/Steam/steamapps/common/Europa Universalis V/game/`, `M/` = the TFE mod folder. Local game files were read directly (current installed patch, Sept 2026) and are the authoritative source; each file-path citation below is a file I opened or grepped. Web sources are linked.

## 1. Which EU5 systems exist and are data-driven/moddable?

### Takeaway
Almost every EU5 system the brief lists is a script database under `G/in_game/common/`, and most folders ship a `readme.txt` or `.info` schema. International organizations, situations, disasters, resolutions, laws/policies, government reforms, estates and privileges, subject types, CBs, religions/aspects/schools, movements, diseases, formables, generic actions, cabinet actions, bureaucracies, character interactions and scripted GUIs are all fully scriptable. The things that are hardcoded are the engine behaviours underneath: migration logic, battle casualty logic, map modes, the list of government types a reform can target, and the rule that country types are location/pop/army/building.

### Cited Findings
**Folder inventory.** `G/in_game/common/` holds about 130 database folders. The ones that matter here are:
- advances, age, bureaucracies, cabinet_actions, casus_belli, character_interactions, child_educations
- country_ranks, culture_groups, cultures, diseases, disasters, estate_privileges, estates, formable_countries
- generic_actions, government_reforms, government_types, hegemons, heir_selections, holy_sites, holy_site_types
- institution, international_organizations, international_organization_special_statuses, international_organization_payments, international_organization_land_ownership_rules
- laws, policies, movements, on_action, parliament_types, parliament_issues, parliament_agendas, pop_types, rebel_demands
- religions, religious_aspects, religious_schools, religious_factions, religious_figures, religious_focuses, resolutions
- scripted_guis, script_values, situations, societal_values, subject_types, traits, wargoals

Events live separately in `G/in_game/events/` (41 entries, 349 .txt files). Sources: `ls G/in_game/common`, `G/in_game/events/readme.txt`.

**Situations** (world-level set pieces) — `G/in_game/common/situations/readme.txt`
- Keys: `monthly_spawn_chance`, `international_organization_type`, `resolution`, `voters` (a global list), `can_start`, `can_end`, `visible`, `on_start`, `on_monthly`, `on_ending`, `on_ended`, `tooltip`, `map_color`, `secondary_map_color`.
- Vanilla has 22: black_death, great_pestilence, hundred_years_war, western_schism, council_of_trent, reformation, rise_of_timur, rise_of_the_ottomans, italian_wars, guelphs_and_ghibellines, hussite_wars, little_ice_age, war_of_religions, red_turban_rebellions, sengoku, the_revolution, and others. Source: `ls G/in_game/common/situations`.

**Disasters** (per-country crises) — `G/in_game/common/disasters/readme.txt`
- Keys: `monthly_spawn_chance`, `modifier`, `can_start`, `can_end`, `on_start`, `on_monthly`, `on_end`, `map_mode`, `fire_only_once`.
- About 37 vanilla disasters, including byzantine_succession_crisis, decline_of_empire, horde_civil_war, succession_crisis, coup_attempt, time_of_troubles, religious_turmoil, peasants_war and D008_fate_of_the_phoenix.

**International organizations** — `G/in_game/common/international_organizations/readme.txt`
- Leaders:
  - `leader_type` (country, character or none) and `leader_change_trigger_type` (none, rulerchange or timed).
  - `leader_change_method` (rotation, vote, lottery, score or none), plus `leadership_election_resolution` and `leader_score`.
  - `override_ruler_title`, `leader_title_key` and `use_regnal_number`.
- State and members:
  - `variables` (with `monthly_change`, min/max and hidden). This is how papal_authority and TFE's tfe_unity work.
  - `special_statuses_implemented`, `payments_implemented`, `land_ownership_rule`, `has_parliament`/`parliament_type`, `has_dynastic_power`.
  - Member annexation rules, modifiers for members, leader, non-leaders and target, and treasuries per currency (e.g. `gold = yes`).
- War and territory:
  - A family of join-war rules (`join_defensive_wars_*` and similar), `can_declare_war`, `has_military_access`.
  - `can_recruit_regiments_in_members` and `has_buildings`.
  - `show_as_overlord_on_map_trigger`, which draws the IO as an overlord on the political map.

**IO special statuses** — `G/in_game/common/international_organization_special_statuses/readme.txt`
- Keys: `can_bestow_trigger`, `auto_bestowal_trigger`, `auto_dismissal_trigger`, `max_countries`, on-bestow and on-rescind effects, `modifier`, `leader_modifier`, `map_color`, `special_status_power` (weight in the IO parliament).
- Existing statuses: emperor, elector, archbishop_elector, free_city, imperial_prince, imperial_prelate, curia, bishopric, military_order, senior_partner, junior_partner, tatar_overlord, tatar_tax_collector, ilkhan_claimant, high_king, celestial_governor, lieutenant, loyalist, absentee, and others.

**Resolutions (voting)** — `G/in_game/common/resolutions/readme.txt`
- A fully scripted voting system for IOs and situations. Keys: `votes`, `total_votes_needed`, `should_finalize_vote`, `select_trigger` (the last select is what members vote on), `propose_effect`, `effect`, `reject_effect`, `vote_effect`, `vote_ongoing_modifier`, `cooldown`, and AI weights.
- The readme says: "create a resolution entirely in script and place a GUI button for it entirely in script - no need for coders!"

**Generic actions** (EU5's equivalent of decisions and buttons) — `G/in_game/common/generic_actions/readme.txt`
- `type` = owncountry, religious, religiousfaction, diplomacy, subject, character, location, internationalorganization, situation or internationalorganizationparliament.
- Also: `price`, `payer`/`payee`, multi-stage `select_trigger` target pickers with map colouring, and AI ticks.

**Government** — `G/in_game/common/government_types/00_default.txt`, `G/in_game/common/government_reforms/readme.txt`
- Five government types: monarchy, republic, theocracy, steppe_horde (power = `horde_unity`) and tribe (power = `tribal_cohesion`).
- Reforms can be gated by `age`, `government`, `major` (exclusive) or `unique`, can set `male_regnal_names`/`female_regnal_names`, and take effect over a duration.

**Laws and policies** — `G/in_game/common/laws/readme.txt`
- A law is a container of policies. A law can apply to a country or to an IO (`requires_vote` in IOs).
- It can be gated by religion group, government group or country tag. Policies carry country, province and location modifiers plus IO modifiers.
- Vanilla files include 00_tribes, 20_hre, 31_catholic_church, christian_tenets, 40_personal_unions, 02_distribution_of_power and 01_legal_system.

**Estates** — `G/in_game/common/estates/00_default.txt`, `G/in_game/common/estate_privileges/readme.txt`
- Estates: crown, nobles, clergy, burghers, peasants, dhimmi, tribes and cossacks.
- There are 261 privileges across `estate_privileges/*.txt`, including the tribal ones: tribal_host, tribal_autonomy, tribes_land_rights and tribes_tribal_levies.

**Societal values** — `G/in_game/common/societal_values/00_default.txt`
- 16 axes, including centralization_vs_decentralization, traditionalist_vs_innovative, spiritualist_vs_humanist, aristocracy_vs_plutocracy, individualism_vs_communalism, mysticism_vs_jurisprudence and sinicized_vs_unsinicized.
- It also has `latinization_vs_hellenization`, which is gated by `has_dlc = "d008_fate_of_the_phoenix"`, `has_or_had_tag = BYZ` and `allow_roman_movement`.

**Other systems**
- **Pop types** (`G/in_game/common/pop_types/00_default.txt`): nobles, clergy, burghers, laborers, soldiers, peasants, tribesmen, slaves.
- **Country ranks** (`G/in_game/common/country_ranks/00_default.txt`): empire, kingdom, duchy, county.
- **Cabinet actions** (`ls G/in_game/common/cabinet_actions`, `G/in_game/common/bureaucracies/byz.txt`): about 70, including encourage_migration, expel_people, settle_tribesmen, form_new_culture, merge_culture_group, promote_culture and promote_religion.
- **Bureaucracies**: country-specific sets exist. The Byzantine set is nomos_empsychos, honorary_titles, court_eunuchs, ritualistic_court, sixty_books_of_the_basilika, romanitas, imperial_senate, kephalai, magister_militum, themata and allelengyon.
- **Religions** (`G/in_game/common/religions/christian.txt`, `G/in_game/common/religious_schools/sunni.txt`, `G/in_game/common/religious_aspects/common.txt`):
  - Per-religion flags: `has_religious_head`, `has_cardinals`, `has_canonization`, `has_patriarchs`, `has_autocephalous_patriarchates`, `needs_reform`, `has_religious_influence`, `tithe`, `important_country`.
  - Religious schools (e.g. the Sunni madhhabs) use `enabled_for_country`/`enabled_for_character` with modifiers.
  - Religious aspects are selectable per religion (see question 2 for the Late Antique ones already in vanilla).
- **Movements** (`G/in_game/common/movements/readme.txt`): culture or religion spreading through pops like a contagion, with `r0`, `spawn` and resistance/growth modifiers. Vanilla movements: calvinism, lutheranism, hellenism_religion and roman_culture.
- **Diseases** (`G/in_game/common/diseases/readme.txt`): an SIR-style pop model with `r0`, `mortality_rate`, `character_mortality_chance`, spread along neighbours, markets, trade and the capital, and `specific_pop_type_effect` filters by culture or religion.
- **Formables** (`G/in_game/common/formable_countries/readme.txt`, `00_formable_countries.txt`): `level`, `required_locations_fraction`, regions/areas/locations, `rule = historical/plausible/fantasy`. Vanilla already defines ROM_f, ROM_BYZ_f, BYZ_f, ITA_f and HRE_f (151 formables in total).
- **Ages and advances** (`G/in_game/common/age/00_default.txt`, `G/in_game/common/institution/*.txt`, `ls G/in_game/common/advances`):
  - Six ages: age_1_traditions has `year = 1`, then 1342, 1437, 1537, 1637 and 1737.
  - Advances are 215 files, including country-specific trees such as `country_byz.txt`.
  - Institutions are tied to ages: feudalism, legalism, meritocracy, renaissance, printing_press, and so on.
- **Scripted GUI** (`G/in_game/common/scripted_guis/scripted_guis.info`): `scope`, `is_shown`, `is_valid`, `effect`, `ai_is_valid`, `ai_chance`. `.gui` files live in `G/in_game/gui/` and mods can override them; TFE already overrides `M/in_game/gui/panels/organization/common.gui`.
- **Wiki on hardcoding**: "While certain elements remain hardcoded and cannot be modified, such as the Migration or Battle casualty logic or map modes, a wide range of options are available for customization" — [EU5 Wiki: Modding](https://eu5.paradoxwikis.com/Modding).
- **Wiki documentation index**: it has pages for Actions, Disasters, Events, Missions, Scripted gui, Setup, Situations, International organizations, Laws, Movements, Religion, Subject types and others — [EU5 Wiki: Modding](https://eu5.paradoxwikis.com/Modding).

### Inferences
**The main building blocks, mapped to 395–600 AD:**

| Late Antique concept | EU5 system to use |
|---|---|
| Imperial dignities (Augustus, Caesar, magister militum, patricius) | IO special statuses on the Imperium Romanum IO |
| Imperial acclamation or consulship votes | resolutions |
| Church councils (Constantinople 381, Ephesus 431, Chalcedon 451) | situations with a `voters` list plus a resolution |
| Hunnic arrival, Radagaisus, Gothic wars, Justinianic Plague | situations or disasters |
| Arianism vs Nicene spread, Latin vs Greek drift | movements |
| Plague of Justinian (541) | diseases |
| "Buttons" (foederati treaties, the annona, hosting games) | generic actions |

**Gaps to scale:**
- Ages are keyed by absolute year. At 395 the whole game sits in age_1_traditions until 1342, so a mod will want to redefine the ages: for example Late Antiquity from 395, Justinianic from about 527, Early Medieval from about 600.
- The vanilla institutions (feudalism, legalism) are Late-Medieval-flavoured and would need re-scoping for this period.

### Gaps
- I did not verify whether new government *types* (a sixth type such as "imperial" or "foederati") can be added by script without engine support. government_types/00_default.txt carries no readme, and power names like `horde_unity` may be engine-bound.
- I did not check whether advances can be age-gated to a custom age list without breaking the hardcoded age UI.

## 2. How does vanilla model the HRE, the Papacy, Byzantium, the Golden Horde and the Black Death (templates for a divided Rome, councils, Huns, plague)?

### Takeaway
All five are data-driven and copyable:
- The HRE is an IO with a character leader, an election resolution, electors and other special statuses, land ownership, a parliament, payments and IO laws.
- The Papacy is an IO with a variable (papal_authority), a tithe payment, curia and bishopric statuses, and resolutions such as excommunication and crusades.
- Byzantium is a country-specific stack: disasters, bureaucracies, cabinet actions, a CB, a subject type, a societal value, an advance tree and a movement. Much of it is gated behind the Fate of the Phoenix DLC (D008).
- Hordes are a government type plus the tatar_yoke IO and dedicated CBs and disasters.
- The Black Death is a situation wrapped around a disease definition.

### Cited Findings
**HRE** (`G/in_game/common/international_organizations/hre.txt`, `G/in_game/common/international_organization_special_statuses/hre.txt`, `G/in_game/common/international_organization_payments/hre.txt`, `G/in_game/common/laws/20_hre.txt`, `G/in_game/common/parliament_types/*.txt`, `G/in_game/common/resolutions/hre_election.txt`)
- Leadership: `unique = yes`, `has_leader_country = yes`, `leader_type = character`, `leader_change_trigger_type = rulerchange`, `leader_change_method = vote`, `leadership_election_resolution = hre_election`, `override_ruler_title = yes`, `use_regnal_number = yes`, `disband_if_no_leader = no` (commented "can have no leader while there's a power battle").
- Parliament, land and dynasty: `has_parliament = yes`, `parliament_type = hre_court_assembly`, `land_ownership_rule = hre_land_ownership`, `has_dynastic_power = yes`.
- War: `only_leader_country_joins_defensive_wars = yes`, `joins_defensive_wars_as_co_belligerent = yes`, `antagonism_modifier_for_taking_land_from_member_as_outsider = 2.0`.
- Special statuses: emperor, elector, archbishop_elector, free_city, imperial_prince, imperial_prelate, primas_germaniae, legatus_natus, imperial_peasant_republic.
- Payments: imperial_contribution, imperial_treasury_contribution, imperial_army_contribution.
- Parliament types for the HRE: hre_court_assembly, hre_early_imperial_diet, hre_bi_camerial_imperial_diet, hre_tri_camerial_imperial_diet.
- The election gives each elector 1 vote (`votes = { add = { desc = "[elector|e]" value = 1 } }`).

**Papacy / Catholic Church** (`G/in_game/common/international_organizations/catholic_church.txt`, `G/in_game/common/religions/christian.txt`, `ls G/in_game/common/resolutions`, `ls G/in_game/common/situations`)
- The IO has `leader_type = character`, `max_active_resolutions = 1`, `gold = yes`, a `papal_authority` variable, `payments_implemented = { tithe }` and `special_statuses_implemented = { curia military_order bishopric }`.
- The catholic religion has `has_religious_head = yes`, `has_cardinals = yes`, `has_canonization = yes`, `important_country = PAP` and `tithe = 0.02`.
- Resolutions include 00_excommunicate, call_crusade and western_schism, plus several papal bulls.
- Council template: `situations/council_of_trent.txt` sets `international_organization_type = catholic_church` and `voters = council_of_trent_voters`, fills the global voter list in `on_start`/`on_monthly` via `add_to_global_variable_list`, and drives `resolution:policy_vote`.
- `resolutions/western_schism.txt` has candidate votes with `total_votes_needed` and `should_finalize_vote = { scope:highest_vote >= scope:total_votes_needed }`.

**Orthodoxy** (`G/in_game/common/religions/christian.txt`, `G/in_game/common/international_organizations/autocephalous_patriarchate.txt`)
- Orthodox has `has_patriarchs = yes` and `has_autocephalous_patriarchates = yes`.
- autocephalous_patriarchate is a non-unique IO with a country leader and a `religion` variable. It could template the Pentarchy sees (Rome, Constantinople, Alexandria, Antioch, Jerusalem).

**Byzantium at 1337 (tag BYZ)**
- `disasters/byzantine_succession_crisis.txt`: `tag = BYZ`, fire-once. It fires on no heir, a regent or a bad heir combined with stability < 50 and legitimacy < 80, and applies `monthly_pretender_rebel_growth`.
- `disasters/decline_of_empire.txt`: a generic imperial decline. It needs age ≥ 2, stability < 0, complacency ≥ 75%, and either low control in the home region or more than a third of the population in non-tolerated cultures.
- `disasters/D008_fate_of_the_phoenix.txt`.
- The Fate of the Phoenix DLC (`G/dlc/D008_fate_of_the_phoenix`; 157 `has_dlc = "d008_fate_of_the_phoenix"` references) adds:
  - CB `cb_restore_roman_borders` (`casus_belli/D008_restore_roman_borders.txt`) and subject type `pronoia` (`subject_types/D008_pronoia.txt`).
  - Character interactions assign_despot, compose_strategikon and mutilations.
  - Cabinet actions: spread_philhellenism, encourage_latin_militarism, reform_imperial_armies, grant_a_triumph, roman_festivals, greek_festivals, patronize_orthodox_monastery, request_papal_donation, demand_beylik_tribute and others.
  - Generic action D008_host_olympiad.
  - `movements/roman_culture_movement.txt`, which spawns roman_culture weighted towards Rome and requires the DLC.
- The Byzantine bureaucracies (magister_militum, themata, imperial_senate, romanitas and the rest) are in `bureaucracies/byz.txt`. There is also a country advance tree, `advances/country_byz.txt`.

**Golden Horde / hordes**
- `government_types/00_default.txt`: `steppe_horde` uses `government_power = horde_unity`, with `horde_unity_hit_at_ruler_death = -50`, `war_no_cb_cost_modifier = -0.5`, `amount_looted_modifier = 0.33`, `global_war_score_efficiency = 0.25`.
- The wiki adds "Auto conquer when at war", "Can raze", "Can raid borders", "Reforming government takes 20 years" — [EU5 Wiki: Government](https://eu5.paradoxwikis.com/Government).
- `government_reforms/steppe_horde.txt`: `legacy_of_genghis` is a major reform requiring `country_type = army` plus Mongol culture or the Borjigin dynasty.
- `international_organizations/tatar_yoke.txt`: a unique IO with a character leader, `leader_change_trigger_type = none`, payments tatar_yoke_contribution and tatar_yoke_leader_payments ("Tribute from everyone to the Tax Collector" / "What the Tax Collector pays to the Leader", `international_organization_payments/tatar_yoke_payment.txt`), and statuses tatar_overlord and tatar_tax_collector.
- `casus_belli/horde_vs_civ.txt`: `cb_horde_vs_civ` is usable by a steppe_horde against any non-horde neighbour, with wargoal `superiority_horde`.
- `disasters/horde_civil_war.txt`: starts when `horde_unity <= 40`, or `<= 75` with a regent, or `<= 60` with an heir.
- `situations/rise_of_timur.txt`: a situation keyed on tag TIM. `on_start` fires events on neighbours and regional countries, gives TIM the modifier `rise_of_timur_impact`, adds `add_area_preference = timurids_timur_conquests` and calls `set_personality = ai_personality:ai_expansionist`. This is a ready template for an AI-directed Hunnic conquest arc.
- `international_organizations/ilkhanate.txt`: a unique IO whose `ilkhan_claimant` status passes leadership to the last claimant standing. The wiki describes three claimant hordes at start — [EU5 Wiki: International organization](https://eu5.paradoxwikis.com/International_organization). This is a template for a succession struggle after Attila.

**Black Death** (`G/in_game/common/situations/black_death.txt`, `G/in_game/common/diseases/bubonic_plague.txt`)
- The situation starts when `disease_is_active = disease:bubonic_plague`, is a data map (`is_data_map = yes`), and has its own actions in `generic_actions/black_death.txt`.
- The disease: `calc_interval_days = 25`, `mortality_rate = { 0.3 0.6 }`, `character_trait = bubonic_plague_trait`, `monthly_resistance_reduction = 0.0002`, and `spawn_disease` inside `spawn`.
- There is also a separate great_pestilence situation and disease.

### Inferences
**Divided Rome.** TFE's Imperium Romanum IO already follows the union/HRE pattern. Possible next steps, borrowed from the templates above:
- Special statuses (Augustus West, Augustus East, Caesar, magister militum praesentalis, foederatus) using `auto_bestowal_trigger`.
- IO payments modelled on tatar_yoke/HRE for the annona or subsidies to foederati.
- IO laws modelled on 20_hre (e.g. "Consular dating", "Joint legislation").
- A `leadership_election_resolution` for senior Augustus or acclamation.

**Church councils.** Clone the council_of_trent pattern: a situation, a global `voters` list and a resolution whose last `select_trigger` picks a doctrine (Nicene, Arian, Nestorian, Miaphysite), with `effect` changing religions or adding modifiers. The Pentarchy fits autocephalous_patriarchate-style IOs, or special statuses in a "Church of the Empire" IO modelled on catholic_church, with a `papal_authority`-style variable.

**Huns.** Combine the pieces: steppe_horde government plus a tatar_yoke-style tribute IO over subject Goths, Alans and Gepids, the `cb_horde_vs_civ` pattern, a rise_of_timur-style situation for 370–453, and a horde_civil_war-style disaster for the Nedao breakup.

**Plague of Justinian (541).** A near 1:1 copy of the bubonic_plague disease plus the black_death situation.

**DLC caveat.** The Byzantine Roman flavour (restore Roman borders, Latin/Hellenic value, Roman culture movement) is DLC-gated. A free mod would have to re-implement it rather than depend on `has_dlc`. Shipping copied DLC script or art is a separate licensing question.

### Gaps
- I did not read the full HRE land-ownership rule or the IO-laws text, so exact mechanics such as circles and imperial reform progression are not documented here.
- I did not verify how `has_dynastic_power` works mechanically.

## 3. Is there migration, nomad hordes, "Society of Pops" or tribal/steppe government in vanilla EU5?

### Takeaway
Yes, all of these exist.
- **Country types.** Four exist in data (location/settled, pop/Society of Pops, army-based, building/extraterritorial) plus navy-based per the wiki. They are switchable by script with `change_country_type`.
- **Pop-based countries** have a migrate action (`add_migration`) and a "settle" transition.
- **Tribes** have a Tribal Migration law, a Force Migration CB and a tribal confederation IO.
- **Steppe hordes** are army-based countries with horde_unity.
- **Limits.** The migration logic itself is hardcoded, and Society of Pops countries are flagged "Not playable" on the wiki.

### Cited Findings
**Country types**
- The wiki's table lists Settled (must own locations), Army Based (armies), Extraterritorial (buildings), Navy Based (navies) and Society of Pops (pops, "Not playable"). Army-based countries unlock "Legacy of Činggis Khān", "Group of Conquistadors" and "Sich Rada" — [EU5 Wiki: Country](https://eu5.paradoxwikis.com/Country).
- The wiki describes SOPs as "landless tribal Nations found in Americas, Oceania, Indo-Burma and Siberia", whose population is location- and culture-based and can overlap colonised land — [EU5 Wiki: Country](https://eu5.paradoxwikis.com/Country).
- Subject types can be bound to a country type: `type = <location/pop/building/army>` — `G/in_game/common/subject_types/readme.txt`.

**Migration actions** (`G/in_game/common/generic_actions/pop_based_countries.txt`, `G/in_game/common/generic_actions/settle_country.txt`)
- `migrate_pop_based_country` (potential `country_type = pop`) picks a source province with no active migration and a neighbouring passable destination, then runs `add_migration = { owner from to amount = 0.100 months = -1 }`.
- `settle_country` requires the agriculture, city_building, metallurgy and taxation advances plus a nomad pop on settleable land, then runs `change_country_type = location`. Its AI weight is `value = -1 # disabled until we have made them fully playable`.

**Tribal laws** (`G/in_game/common/laws/00_tribes.txt`)
- Six tribal laws: legal_basis, organization, religious_values, migration, cultural_identity, modernization.
- `tribal_migration_law` offers three policies:
  - frequent_migration: +10% army movement speed, −25% migration cost.
  - seasonal_travel: −50% migration cost.
  - permanent_settlement: +100% migration cost; `on_fully_activated = { change_country_type = location }` after 5 years.

**Tribal CB and IO**
- `casus_belli/force_migration.txt`: `cb_force_migration` is tribe versus tribe, with wargoal `superiority_force_migration`. Other related CBs: `expansion_into_the_steppes`, `tribal_feud`, `slave_raiding`.
- `international_organizations/tribal_confederation.txt`: a non-unique IO with a country leader that expels members at war with each other. The wiki lists member effects as +0.05 monthly prestige, +0.05 monthly tribal cohesion, mutual defence and mutual offence — [EU5 Wiki: International organization](https://eu5.paradoxwikis.com/International_organization).

**Pop management**
- Cabinet actions for moving pops: encourage_migration, expel_people, settle_tribesmen, settle_the_frontier, send_people_to_the_colonies — `ls G/in_game/common/cabinet_actions`.
- The on_action `on_albanian_migration` exists, so vanilla scripts a historical migration event — `G/in_game/common/on_action/*.txt`.

**Tribe government** (`G/in_game/common/government_types/00_default.txt`)
- Power: `tribal_cohesion`. Heir selections: tribal_oldest_male, ritual_selection, tanistry_elective, tribal_matrilineal.
- Modifiers: −25% nobles food consumption and diplomatic_upkeep_efficiency 1.5.
- Tribal estate privileges include tribal_host, tribal_autonomy and tribes_tribal_levies (`estate_privileges/*.txt`). The wiki adds "Cannot appoint a Head of Cabinet" — [EU5 Wiki: Government](https://eu5.paradoxwikis.com/Government).

**What TFE already does** (`M/in_game/common/generic_actions/tfe_migratory.txt`): TFE's migratory hosts use `country_type = army`, the steppe-horde pattern, rather than `pop`.

**Hardcoded core**: "Migration or Battle casualty logic" is listed as hardcoded — [EU5 Wiki: Modding](https://eu5.paradoxwikis.com/Modding).

### Inferences
- **Three ways to model Völkerwanderung peoples:**
  - Army-based hosts (TFE's current choice). Playable, and horde-like.
  - Pop-based SOPs. They migrate as population but are "not playable" per the wiki and have weak AI.
  - Settled tribes with the Tribal Migration law and `change_country_type` for the settling moment, e.g. the Visigoths in Aquitaine in 418 or the Vandals in Africa in 439.
- **A foederati hook.** Combine the permanent_settlement policy's `change_country_type = location` with a custom subject type (`type = location`, `subject_pays`, `join_defensive_wars_always`) granted by the Empire.
- **Scripting around the hardcoded layer.** Since migration logic is hardcoded, mods can only call `add_migration`, `change_country_type` and cabinet actions, not change how pops pick destinations.

### Gaps
- I did not test whether `country_type = pop` countries can be made player-selectable by modding. The wiki says "Not playable", and whether that is hardcoded or a setup flag is unverified.
- I did not confirm whether army-based countries can hold IO membership or special statuses (relevant to foederati inside the Imperium IO).

## 4. Known modding limits, start-date constraints and comparable mods

### Takeaway
Start dates before 1337 work, via the `START_DATE` define; TFE already runs at 395. Setup data (pops, ownership, characters) must be supplied wholesale, and scenario IDs are hardcoded in the front-end GUI. The only EU5 antiquity total conversion I found (Ancient World, Nov 2025) is a small, early-stage project, so there is no mature Late Antiquity EU5 comparable. The known hardcoded areas are migration and battle-casualty logic and map modes, plus age years anchored at 1342 onwards.

### Cited Findings
**Start date and setup**
- Vanilla `START_DATE = "1337.4.1"` is in `G/loading_screen/common/defines/00_defines.txt`. TFE overrides it in `M/loading_screen/common/defines/tfe_defines.txt`, and its setup uses dates such as `start_date = 382.10.3` in `M/main_menu/setup/start/12_diplomacy.txt` and `313.1.1` in `13_religion.txt`.
- TFE's scenario file notes: "The IDs are hardcoded in main_menu/gui/frontend_singleplayer.gui, so the keys stay vanilla while the countries point at 395 tags" — `M/main_menu/common/scenarios/00_scenarios.txt`.
- Most setup managers are additive, "which makes the addition to vanilla setup relatively easy, but makes it so that replacing entire files is required in order to remove certain entries". setup/start files must be UTF-8 without BOM, while setup/countries and setup/templates use UTF-8 with BOM — [EU5 Wiki: Setup modding](https://eu5.paradoxwikis.com/Setup_modding).
- Mods need `.metadata/metadata.json`. `game_custom_data.replace_paths` is "the only" supported custom data (e.g. replacing `events`) — [EU5 Wiki: Mod structure](https://eu5.paradoxwikis.com/Mod_structure).

**Known problems**
- Non-ASCII user paths break mod file loading on Windows — [EU5 Wiki: Modding](https://eu5.paradoxwikis.com/Modding).
- Age years are absolute (1, 1342, 1437, …) in `G/in_game/common/age/00_default.txt`.
- Many vanilla disasters and situations hard-reference 1337 tags (`tag = BYZ` in byzantine_succession_crisis, `c:TIM` in rise_of_timur). TFE's own borders spec records that vanilla in_game scripts referencing 1337 characters and tags produce errors — `M/docs/plans/2026-09-25-395-borders.md`.

**Community discussion.** Players say the single 1337 start exists partly because setting up population data per date is "an order of magnitude more work" — [dtgre.com analysis](https://www.dtgre.com/2025/11/europa-universalis-5-1337-start-date-analysis-timeline-guide.html). This is a secondary blog, not a Paradox statement.

**Comparable mods**
- "Ancient World; Bronze & Iron Age - Before They Came" bills itself as the "First Total Conversion Mod for the Antiquity in EUV", with intended start dates "from 3200s BCE… until Late Antiquity 500s and Early Medieval". Its creator explicitly seeks to build "EUV Equivalents of CKIII Mods like Apotheosis, Hegemonia, Fallen Eagle or Bronze Age Reborn". The file is 598 KB, posted Nov 5, 2025, which suggests an early or minimal release — [Steam Workshop 3600046075](https://steamcommunity.com/sharedfiles/filedetails/?id=3600046075).
- Search results also surface a "Roman Empire Collection" workshop collection and a "Basileía Romaíon: 1337" Byzantine rework, both 1337-based rather than antiquity — [Steam Workshop collection 3608056145](https://steamcommunity.com/workshop/filedetails/?id=3608056145). I did not open that page, so its contents are unverified.
- The mature antiquity comparables are EU4 mods (Imperium Universalis, Roma Universalis), not EU5 ones — [EU4 Wiki: Imperium Universalis](https://eu4.paradoxwikis.com/Imperium_Universalis), [ModDB Roma Universalis](https://www.moddb.com/mods/roma-universalis).

### Inferences
- **Age handling.** A 395 mod should replace `age/00_default.txt`, e.g. age_1 at 395, age_2 at about 527, and so on. The alternative is accepting that all age-gated content (institutions, advances, the `legacy_of_genghis` `age = age_1_traditions` gate) stays in age 1 for centuries.
- **Avoid 1337-coupled vanilla content.** Vanilla situations and disasters keyed to 1337 tags will either never fire (the tags don't exist) or throw errors. The cleanest approach is `replace_paths` or empty overrides for situations and disasters, then re-adding Late Antique versions, following TFE's existing "stub 1337 files" approach.
- **No proven reference implementation.** There is currently no mature EU5 mod to borrow Late Antiquity mechanics from, so vanilla game files are the only template base.

### Gaps
- Web fetching was partly blocked in this environment: WebFetch was hook-blocked and the context-mode fetch errored, and Steam once returned HTTP 429. I could not read the Paradox forum modding subforum, the Tinto Talks dev diaries or wiki pages on "hardcoded" topics beyond the Modding, Mod structure, Setup, Country, Government and International organization pages.
- I found no primary Paradox statement on whether ages, government power types or map modes are extensible.
- I found no list of other EU5 Rome or antiquity mods beyond Ancient World.
- I did not verify whether the "Navy Based" country type has its own script key: the wiki lists it, but the subject_types readme only mentions location/pop/building/army.
