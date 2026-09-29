# Eastern Europe in 395: who owns it, who is missing, who could fill it

Research report for TFE (Europa Universalis V, 395 AD start). Nothing in the mod was edited except this file.
Method: `tools/borders.py`'s own loaders (`load_hierarchy`, `load_centroids`, `dataset_owner`) plus a parse of
`main_menu/setup/start/10_countries.txt` (land locations, excluding sea and non-ownable), the tables in `tools/`,
vanilla `definitions.txt`, and web sources. Counts are locations (EU5's smallest unit).

Confidence labels used for every people below:

- **A**: attested polity (a state or kingdom with a named ruler in the sources).
- **P**: attested people, polity invented (the people is named in ancient sources; we give it a state).
- **X**: archaeology-only name (an archaeological culture is there; the 395 self-name is unknown or the name we use
  is later or modern).

No people in Eastern Europe between the Vistula and the Urals is an **A** at 395 except the Huns themselves and the
Goths already in the mod. Everything proposed is P or X, and this report says so instead of hiding it.

## 1. The gap

### 1.1 Counts

1468 land locations in the six eastern regions are unowned in `10_countries.txt`: 46 areas touched, 257 provinces.
40 of the areas are wholly unowned, 6 partly.

| Region | Unowned locations | Areas touched |
|---|---|---|
| russian_region | 545 | 17 |
| scandinavian_region | 264 | 5 (Norrland, Finland, Kola, Nord-Norge, Karelia) |
| baltic_region | 246 | 7 (Baltic, Lithuania, Samogitia, Greater Poland, Central Poland, Lesser Poland, Mazovia) |
| ural_region | 194 | 9 (Bolghar, Kazan, Vyatka, Ural, Perm, Bashkiria, Karagay, Ust-Sysola, Vorkuta) |
| ruthenia_region | 181 | 7 (White Ruthenia, Black Ruthenia, Polesia, Severia, Right-Bank Ukraine, Volhynia, Red Ruthenia) |
| carpathia_region | 38 | 1 (Slovakia) |
| **Total** | **1468** | **46** |

Partly unowned areas (unowned / all land locations): Tambov 26/41, Slovakia 38/45, Volhynia 13/30, Severia 30/39,
Right-Bank Ukraine 15/39, Red Ruthenia 9/36.

Outside the brief but adjacent: `west_siberia_region` has 313 unowned (only 14 are RRN's), `east_siberia_region`
511. The Sargat country runs into west Siberia; this report stops at the Ural region.

**Already fully owned (no gap): the Pontic steppe and the North Caucasus.** `steppes_region` is entirely HNS, CAL,
AKA or ABG; the Caucasus is entirely owned by EAR, SAS, ASK, IBR, AGV, LZC, ABG, CAL, MSQ, SRR, LPN, DZR, SUA.

### 1.2 Why they are unowned

`world_400.geojson` gives no polity to these lands. Of the 1289 unowned locations this report proposes to fill,
1043 fall in no named polygon, 213 in "Finno-Ugric taiga hunter-gatherers", 27 in "Saami" and 6 in "Paleo-Siberian
hunter-gatherers". The last three names are mapped to `none` in `tools/tag_map.txt`. `tools/overrides/10_west.txt`
has `!scope` over carpathia_region and scandinavian_region only, and `slovakia_area = none` with the comment "omniatlas:
no polity (Gepid/Hun fringe)". No override file covers baltic, russian, ruthenia or ural.

### 1.3 The unowned areas by region

| Region | Area (unowned locations) |
|---|---|
| baltic | baltic_area 56, lithuania_area 43, lesser_poland_area 40, greater_poland_area 35, mazovia_area 33, central_poland_area 23, samogitia_area 16 |
| ruthenia | white_ruthenia_area 56, black_ruthenia_area 39, severia_area 30, polesia_area 19, right_bank_ukraine_area 15, volhynia_area 13, red_ruthenia_area 9 |
| russian | west_novgorod 51, east_novgorod 49, smolensk 46, ryazan 45, samara 43, oka 35, beloozero 33, nizhny_novgorod 31, pomorye 30, totma 29, tambov 26, arkhangelsk 25, moscow 24, yaroslavl 24, tver 23, vladimir 20, suzdal 11 |
| ural | samara-side: bolghar 21, kazan 30; vyatka 18, ural 31, perm 27, bashkiria 26, ust_sysola 17, karagay 15, vorkuta 9 |
| carpathia | slovakia_area 38 |
| scandinavia | norrland 80, finland 58, nord_norge 58, karelia 44, kola 24 |

### 1.4 Who owns what nearby (tag, culture, locations)

Culture is the tag's state culture from `tools/tags.txt`. All are `eurasian_tribe` unless noted.

| Tag | Name | Culture | Religion | Where (region: locations) |
|---|---|---|---|---|
| HNS | Huns (kingdom, `eurasian_horde_no_muslim`; ruler Uldin) | hunnic | tengri | steppes 242, ruthenia 96, carpathia 94, russian 15 (half of Tambov). The geojson "Ostrogoths" and "Hunnic Empire" both map here. |
| AKA | Akatziri | hunnic | tengri | steppes 6 (Yedisan) |
| CAL | Alans | alan_culture | alan_paganism | steppes 69, caucasus 13 |
| SCR | Sciri | gothic_culture | arianism | ruthenia 4 (Podolia) |
| GEP | Gepids | gothic_culture | arianism | carpathia 33 (Transylvania) |
| IAZ | Iazyges | iazyges | alan_paganism | carpathia 27 (south Alfold) |
| HAS | Hasding Vandals | vandal | arianism | carpathia 30 (north Alfold) |
| QAD | Quadi | suebian | norse | carpathia 7 (Pozsony), south_german 8 |
| MKM | Marcomanni | suebian | norse | south_german 47 (Prague) |
| SLX | Siling Vandals | vandal | norse | baltic 50 (Silesia), south_german 5 |
| RUG | Rugii | gothic_culture | arianism | north_german 31 (Pomerania) |
| AES | Aesti | pruthenian | romuva | baltic 44 (Prussia) |
| WND | Venedi | venedi | slavic_paganism | ruthenia 25 (Volhynia 14, Red Ruthenia 11) |
| GEA, SVE | Geats, Svear | swedish | norse | Gotaland 39, Svealand 46 |
| NRW | Norse Petty Kingdoms | norwegian | norse | Syd-Norge 63 |
| DAX, JUT, AGL | Danes, Jutes, Angles | danish, danish, saxon | norse | Denmark and Skane |
| WRE, EAR, VIS | Roman empires, Visigoths | roman/greek/gothic | orthodox/arianism | Transdanubia (WRE 31), Balkans |

Not owned in the east at all today: no Baltic, Slavic (other than WND), Finnic, Permic, Volga-Finnic or Ugric tag.

## 2. Historical research

Sources are cited inline. "Wikipedia:" means the English article of that name, read through the MediaWiki API during
this session. "Getica" is Jordanes, read in Latin at https://www.thelatinlibrary.com/iordanes1.html (section numbers
as printed there). Where a page could not be fetched I say so and mark the claim unverified.

### 2.1 What Jordanes gives (and what it does not)

- **Getica 116**: Ermanaric ruled, among others, "Golthescytha Thiudos Inaunxis Vasinabroncas Merens Mordens
  Imniscaris Rogas Tadzans Athaul Navego Bubegenas Coldas". This is a list from before 375, when Huns broke the
  Greuthungi (Wikipedia: Ermanaric; Greuthungi). It says nothing about anyone's status in 395. It is the
  only ancient source that names forest peoples of the Volga-Oka lands.
- **Getica 34-35**: north of the Vistula sits "Venetharum natio populosa", whose names change "per varias familias et
  loca" but are principally the **Sclaveni** (Novietunum and Lake Mursianus to the Dniester and north to the Vistula)
  and the **Antes** ("fortissimi", from the Dniester to the Dnieper along the Black Sea bend).
- **Getica 36-37**: at the Vistula mouth the Vidivarii "ex diversis nationibus adgregati"; after them the **Aesti** on the
  Ocean shore, "a peaceful people"; south of them the **Acatziri**; beyond, the Bulgar seats and the Huns.
  Jordanes wrote c. 551 about older geography.
- **Getica 247-248**: after the Hunnic conquest the Amal Vinitharius, "aegre ferens Hunnorum imperio subiacere",
  attacked the Antes, crucified their king **Boz** with his sons and 70 nobles, and was then destroyed by Balamber, king
  of the Huns. This is the only ancient evidence that Antes were near the Goths under Hunnic overlordship shortly after 376.
- Tacitus (Germania 45, c. 98) names the **Aesti** east of the Suiones (Wikipedia: Aesti). The Aesti of the ancient
  sources are Balts, not Estonians.

### 2.2 The peoples, one by one

Region of the proposed tag in brackets. "Sub" = whether it starts as an HNS subject (section 4).

**Baltic coast, Poland, Belarus**

- **Sudovians / Galindians (SUD)**. Ptolemy (2nd c.) names "Galindai kai Soudinoi" (Wikipedia: Sudovians). The
  Yotvingian homeland is the Suwalki-Grodno-Podlasie zone. Wikipedia: Balts says West Balts began settling the
  eastern Baltic coast in the fifth century, and that the Galindae moved to the Moscow area in the fourth. Label **P**
  (people attested; polity invented; boundaries follow the later Yotvingian country).
- **Aukstaitians (AUK)**. No 395 self-name is known; the tag stands for the East Baltic forest peoples of the Neris
  and Nemunas. Label **X**. Wikipedia: Balts.
- **Curonians and Samogitians (CUR)**. Wikipedia: Balts lists Curonians among the West Balts who came onto the coast
  in the fifth century, so in 395 the name is a convenience. Label **X**.
- **Latgalians, Selonians (LTG)**. Wikipedia: Balts says the Latgalians expanded into northern Latvia only by the
  sixth or seventh century, which "previously had been occupied by the western Finno-Ugric tribes". So in 395 this
  is an early East Baltic frontier with Finnic neighbours. Label **X**.
- **Estonians (EST)**. Not the Aesti (see 2.1). The land is Finnic in the archaeology; I found the tarand graves on
  eestijuured.ee but did not re-verify them this session. Label **X**.
- **Lugii, Vistula Veneti, Przeworsk country (LUG)**. Wikipedia: Przeworsk culture: 3rd c. BC to 5th c. AD, with its
  eastern area absorbed in the 3rd-4th c. by Wielbark and Chernyakhov, and a decline "in the late 5th century [that]
  coincides with the invasion of the Huns". Wikipedia: Wielbark culture: the Goths' culture, replaced in the 5th c. by the
  Sukow-Dziedzice group associated with early Slavs. Wikipedia: Early Slavs: Pliny, Tacitus and Ptolemy put the
  Veneti east of the Vistula; whether they spoke Slavic is debated. The equation of Przeworsk with the **Lugii**
  is standard but I did not verify it in this session. Poland in 395 is thinly populated after the Goths left, so this is
  the shakiest fill. Label **X** for Lugii; **P** for Veneti (already WND).
- **Venedi (WND, existing)**. Extending it over Lesser Poland, the rest of Volhynia and Red Ruthenia matches Getica 34.
  Label **P**.

**Ukraine and Belarus, Dnieper**

- **Antes (ANE)**. Getica 35 and 247-248 above. Wikipedia: Antes: Jordanes and Procopius appear to treat them as Slavic by
  the fifth century; their centre moved north to the southern Bug in the fourth, and to Volhynia and the middle Dnieper
  in the fifth and sixth. Wikipedia: Chernyakhov culture: with the Hunnic invasion it declined and was replaced by
  Penkovka, "the culture of the Antes". Wikipedia: Kyiv culture: 3rd-5th c., the first identifiable Slavic culture,
  ancestor of Prague-Korchak, Penkovka and Kolochin. Wikipedia: Kolochin culture: Chernihiv, Sumy, Gomel, Mogilev, Bryansk
  and Kursk, "from the 4th or 5th to the 7th century". The geography is a stretch: Jordanes' Antes are on the
  steppe edge (already HNS). The proposed ANE is the northern (Polesia, Kyiv-Kolochin) Slavic country. Label **P** for the name, **X** for the
  boundaries. UNVERIFIED: Kolochin's 4th-century start (Wikipedia gives "4th or 5th").
- **Dnieper Balts (DBL)**. Wikipedia: Moshchiny culture: 4th-7th c., upper Dnieper and upper Oka (Kaluga, Tula, Oryol,
  Smolensk), arising from Yukhnov with Zarubintsy immigration. Baltic hydronymy is the usual evidence; I did not
  fetch Yukhnov or Milograd directly. Label **X**.

**Central and western Russia**

- **Galindae / Golyad (GLJ)**. Wikipedia: Galindians: Ptolemy first mentions Galindoi in the 2nd c.; Wikipedia: Sudovians
  says the "Goliadj", an extinct East Baltic tribe, "lived from the 4th century in the basin of the Protva River, near
  the modern Russian towns of Mozhaysk, Vereya, and Borovsk", all three locations in the proposed Mozhaysk province.
  Wikipedia: Dyakovo culture: an early Finno-Ugric culture around the Moskva and Oka, with "Baltic influence"
  debated. So Moscow-Oka is Baltic and Finno-Ugric mixed. Label **P**.
- **Merya (MRY)**. Getica 116 "Merens"; Wikipedia: Merya says Jordanes mentioned "Merens" as tribute-payers to Ermanaric. The
  identification with the medieval Merya is common, not certain. Label **P**.
- **Ves (VES)**. "Vasinabroncas" of Getica 116 is often read as Ves. I could not fetch Wikipedia: Ves people (the
  fetch returned nothing), so treat the equation as unverified. Label **X**.
- **Vod (VOD)**. The Votes of the Novgorod lands. No source fetched; the people is attested only later. Label **X**.
- **Mordvins (MRD)**. Getica 116 "Mordens"; Wikipedia: Mordvins says the ethnonym is "possibly attested" there. Label **P**.
- **Muroma and Meshchera (MRO)**. Wikipedia: Meshchera: a Finno-Ugric tribe between the Oka and Klyazma, first named in
  a 13th-century source; Volga-Finnic women's jewellery of the 4th-7th c. in the graves. Wikipedia: Volga Finns: modern
  Mari and Mordvins, plus the extinct Merya, Muroma and Meshchera. The Muroma page failed to fetch. Label **X**.
- **Mari (MRR)**. Volga Finnic (Wikipedia: Volga Finns). Some readers take Jordanes' "Merens" for the Mari; I flag that as
  uncertain. Label **X**.

**Volga-Kama and Urals**

- **Udmurts (UDM)** and **Permians / Komi (KMI)**. I meant to cite Pyany Bor, Azelino, Lomovatovo and related Kama
  cultures; the pages I tried (Azelin culture, Kama region archaeology) came back empty. Both are **X** and unverified
  beyond Wikipedia: Finnic peoples, which lists Udmurts and Komis among the Finnic family.
- **Imenkovo (IMK)**. Wikipedia: Imenkovo culture: 4th-7th c., Middle Volga (Tatarstan, Mordovia, Chuvashia, Samara). The
  people is unnamed. Label **X**.
- **Sargat and Kushnarenkovo Ugrians (SRT)**. I read no page on either this session. It is the Ural-Tobol zone
  where a later Hungarian tradition (Julian's 1235 journey, Wikipedia: Volga Finns) places the Magyars' eastern kin. Label **X**
  and treat every detail as unverified.

**Carpathians**

- **Carpi, Costoboci, free Dacians (CRP)**. Wikipedia: Carpi: in Moldavia from c. 140 to "at least AD 318"; many were
  forcibly moved to Pannonia; Zosimus records a coalition of "Huns, Sciri and Karpodakai" in 381. Wikipedia: Costoboci:
  a Dacian tribe between the Carpathians and the Dniester, raiding in 170/171. Wikipedia: Lipitsa culture: supposedly a
  Dacian tribe's, but ended by the early 3rd c., so it is no evidence for 395. Label **P** for Carpi and Costoboci, **X** for the upper
  Tisza and the Maramures country.
- **Quadi (QAD, existing)**. Extending it east over Trencin, Hont and Nograd is my own choice; the polity is unchanged.

**Finland and Karelia**

- **Suomi (SUO)** and **Korela (KRE)**. Nothing verified beyond Wikipedia: Finnic peoples. Both are **X**, invented names.

### 2.3 Who was a Hunnic subject in 395?

By 370 the Huns were on the Volga, and by about 375 they had broken the Greuthungi (Wikipedia: Huns; Ermanaric).
Uldin, "the first Hunnic ruler whose historicity is undisputed", died before 412 (Wikipedia: Uldin). Hunnic power
in 395 is the Pontic steppe plus Dacia; the empire of Attila is 430 onwards (Wikipedia: Huns).

| People | Subject at 395? | Evidence |
|---|---|---|
| Greuthungi / Ostrogoths, and Goths who stayed | Yes, already HNS in the mod | Getica 248; Wikipedia: Ermanaric, Greuthungi |
| Alans who stayed east of the Don | Partly (CAL is independent in the mod) | Wikipedia: Alans: many fled west; those who "remained under Hunnic rule" |
| Antes | Plausible | Getica 247-248 puts Antes and Goths under Huns within a few years of 376 |
| Carpi and Costoboci | Plausible ally or subject | Zosimus 381 coalition of Huns, Sciri and Karpodakai (Wikipedia: Carpi) |
| Sciri | No, not by 395 | Wikipedia: Sciri: near the Goths in the late 4th c.; "by the early 5th century" subdued by the Huns |
| Gepids | Disputed | Wikipedia: Gepids: "in the fourth century, among the peoples incorporated into the Hunnic Empire"; this is a compression of a later fact. GEP stays independent |
| Akatziri | No | Priscus: allied to Attila until the Huns attacked them in 447/448 (Wikipedia: Akatziri) |
| Aesti, Vidivarii | No evidence | Getica 36 gives no Hunnic link |
| Forest peoples of the Volga and Oka (Merens, Mordens etc.) | No evidence | Getica 116 is a pre-375 tribute list to Ermanaric. Nothing shows the tribute passed to the Huns |

## 3. Proposal

22 new tags plus 3 extensions of existing tags, covering 1289 of the 1468 unowned locations. Tags were checked against
vanilla `in_game/setup/countries`, `in_game/common/formable_countries`, `main_menu/setup/*`, coat-of-arms files, `tools/tags.txt` and
`tools/tag_map.txt`: all 22 are unused. Several obvious mnemonics were **not** free and were replaced: `GLD` (vanilla
formable), `GLY`, `MRJ`, `MRI`, `MUR`, `MAR`, `PRM`, `MSC`, `CHM` and `CHR` are used by vanilla, so Golyad is `GLJ`, Mari is `MRR`,
Muroma is `MRO` and Permians `KMI`.

Government: every tag uses the `eurasian_tribe` template, like AES, WND, GEP and SCR (the existing 395 tribes). None needs a
`governments.txt` line unless a named ruler is wanted.
Religion keys were checked against `known_religions()`; culture keys against `known_cultures()`. Vanilla or `tfe_cultures.txt`
cultures exist for every proposal except the two stand-ins noted below. Rank: `rank_duchy` for the six tags over
70 locations; `rank_county` (the default) for the rest.

### 3.1 New countries

| # | Name | Tag | EU5 land | Locs | Culture | Religion | Rank | Capital (location) | HNS sub | Label |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Sudovians | SUD | provinces grodno, novogrudok, slonin, vawkavysk (black_ruthenia); suwalki (lithuania); lomza, podlasie (mazovia); bresta, kobryn (polesia) | 41 | sudovian | romuva | county | grodno | no | P |
| 2 | Aukstaitians | AUK | lithuania_area except suwalki: ashmyany, breslauja, kaunas, lida, svir, trakai, upyte, vilkmerge, vilnius | 40 | aukstaitian | romuva | county | kernave | no | X |
| 3 | Curonians | CUR | samogitia_area (16); baltic_area provinces courland, semigalia (12) | 28 | curonian (Samogitians: pop rule `samogitian` stays) | romuva | county | grobina | no | X |
| 4 | Latgalians | LTG | baltic_area provinces latgalia, selonia, inner_livonia, south_livonia | 20 | latvian | romuva | county | pietalava | no | X |
| 5 | Estonians | EST | baltic_area provinces estonia, north_livonia, rotalia, tartu | 24 | estonian | muinaisusko | county | tartu | no | X |
| 6 | Lugii | LUG | greater_poland_area (35); central_poland_area (23); mazovia provinces ciechanow, czersk, plock, rawa, warsaw (21) | 79 | venedi | slavic_paganism | duchy | kalisz | no | X |
| 7 | Antes | ANE | black_ruthenia: kletsk, mazyr, rechytsa, slutsk; polesia: pinsk, turov; right_bank_ukraine: chornobyl, olevsk, ovruch; severia: chernihiv, gomel, novhorod_siverskyi, starodub_siverskyi, trubchevsk | 71 | venedi (stand-in for Slavic) | slavic_paganism | duchy | ovruch | yes (tributary) | P/X |
| 8 | Dnieper Balts | DBL | white_ruthenia_area (56); smolensk_area (46); severia province bryansk (6) | 108 | aukstaitian | romuva | duchy | smolensk | no | X |
| 9 | Golyad | GLJ | moscow_area (24); oka_area (35); tver_area (23) | 82 | aukstaitian | romuva | duchy | moscow | no | P |
| 10 | Merya | MRY | yaroslavl_area (24); vladimir_area (20); suzdal_area (11); nizhny_novgorod_area provinces galich, gorodets, nizhny_novgorod, unzha (23) | 78 | merya_culture | mari_paganism | duchy | rostov | no | P |
| 11 | Ves | VES | beloozero_area (33); totma_area (29); east_novgorod_area (49); pomorye provinces kargopol, zaonezhye, onega (16) | 127 | vepsian | muinaisusko | duchy | beloozero | no | X |
| 12 | Vod | VOD | west_novgorod_area (51, includes the rzhevskaya province) | 51 | votian | votian_religion | county | koporye | no | X |
| 13 | Mordvins | MRD | ryazan provinces bogdanovo, sarov (15); tambov provinces penza, tambov (14); samara provinces alatyr, kurmysh, troitskoye_kuroedovo (19) | 48 | erzya_culture | erzya_religion | county | saransk | optional | P |
| 14 | Muroma | MRO | ryazan provinces murom, kasimov, ryazan, pronsk, rostislavl | 30 | meschera_culture | moksha_religion | county | murom | no | X |
| 15 | Mari | MRR | kazan provinces yaransk, nema (13); nizhny_novgorod province uren (8) | 21 | mari_culture | mari_paganism | county | morki | no | X |
| 16 | Udmurts | UDM | vyatka_area (18); kazan provinces igra, sarapul (10) | 28 | udmurt | udmurt_paganism | county | sarapul | no | X |
| 17 | Permians | KMI | karagay_area (15); ust_sysola_area (17); perm provinces perm, beryozovka, kasevo (18) | 50 | komi | komi_paganism | county | cherdyn | no | X |
| 18 | Imenkovo | IMK | bolghar_area (21); kazan province kazan (7); samara provinces cheboksary, samara, simbirsk (24) | 52 | chuvash_culture (stand-in) | tengri (stand-in, no vanilla fit) | county | laish | optional | X |
| 19 | Ural Ugrians | SRT | ural_area (31); perm provinces ufa, bisert (9); bashkiria provinces chishmy, krasnaya_gorka (13) | 53 | mansi_culture (stand-in; `hungarian` if the Magyar story is wanted) | obian_paganism | county | ufa | optional | X |
| 20 | Carpi | CRP | slovakia_area provinces szepes, zemplen, maramaros | 19 | dacian | zalmoxism | county | mukachevo | yes (tributary) | P/X |
| 21 | Suomi | SUO | finland_area except vyborg province | 47 | finnish (the `finland_area` pop rule says `tavastian`; pick one) | muinaisusko | county | abo | no | X |
| 22 | Korela | KRE | karelia provinces aunus_karelia, inner_aunus_karelia, korela (31); finland province vyborg (11) | 42 | karelian | muinaisusko | county | korela | no | X |
| | **Total new** | | | **1139** | | | | | | |

Capitals are location keys inside the named province; I checked each exists in `definitions.txt` and lies inside the
land shown. "optional" means no source supports a Hunnic link and the subject line is a game-design choice.

### 3.2 Extensions of existing tags (no new tag)

| Tag | Adds | Locs | Note |
|---|---|---|---|
| WND (Venedi) | lesser_poland_area (40); volhynia provinces chelm, volodymyr, zviahel (13); red_ruthenia provinces przemysl, sanok, drohobych, pocutia (9) | 62 | Getica 34-35; keeps WND the Vistula-Bug Slavic core |
| QAD (Quadi) | slovakia provinces trencsen, hont, nograd | 19 | Quadi country; leaves CRP the east of Slovakia |
| HNS (Huns) | tambov provinces lipetsk, saratov (12); bashkiria provinces sorochinskaya, meleuz (13) | 25 | Fills the steppe-forest fringe next to Hunnic Tambov and the Ural steppe. No source; game-design fringe |

### 3.3 Optional extensions the brief did not ask for

| Tag | Adds | Locs | Note |
|---|---|---|---|
| NRW | nord_norge_area provinces sor_trondelag, nor_trondelag, romsdalen, jamtland (Trondelag and Jamtland) | 32 | Trondelag is inside the Norse zone; EU5 files it under `nord_norge_area`. Only the southern strip is taken |
| SVE | norrland_area provinces halsingland, angermanland | 12 | The northern edge of the Svear |

These 44 are counted in the 1289 but sit in the Nordic north. Drop them if the Nordic section is left alone.

### 3.4 What to leave empty, and why

179 locations, all far north; no proposal fills them:

| Area | Locs | Why |
|---|---|---|
| norrland_area (rest) | 68 | Sami country (kemi, torne, lule, pite, ume lappmark, Vasterbotten, Kajanaland). The geojson polity "Saami" maps to `none` |
| nord_norge_area (rest) | 26 | Finnmark, Troms, Nordland: Sami and the Norse fringe |
| kola_area | 24 | Kola: Sami; no agriculture |
| arkhangelsk_area | 25 | Kholmogory, Kuloy, Mezen, Zavolochye: Zavolotskaya Chud forest; no source |
| pomorye_area (rest) | 14 | White Sea coast: taiga hunters (Pomorye, Shenkursk, Yemetsk) |
| karelia_area (rest) | 13 | White Karelia; taiga |
| vorkuta_area | 9 | Arctic Urals; Samoyed and Ob-Ugric country |

The geojson calls the Finno-Ugric taiga and Sami zones hunter-gatherers. Their absence is cheap, historical and does
not read as a hole on the map. The RoadMap design rule "fun over accuracy" points the other way for playable fills, which
is why the taiga forest peoples (Ves, Vod, Merya, Mordvins, Permians) are filled and only the Arctic edge is left.
Siberia beyond the Urals is out of scope here.

## 4. Hunnic subjects

Proposed start as HNS subject (in `main_menu/setup/start/12_diplomacy.txt`, `subject_type = tributary`, see the Funan and
Aksum lines already there): **ANE** (Antes; Getica 247-248) and **CRP** (Carpi; Zosimus via Wikipedia: Carpi). This
supports RoadMap item 10, the "Hunnic storm" tribute situation, without asserting more than the sources do.

Optional, unsupported by sources: MRD, IMK, SRT (Volga and Ural border peoples). If none of these is taken, HNS keeps its
current subjects: none in `12_diplomacy.txt`. I did not find any `first = HNS` line there.

## 5. How this enters the pipeline

Nothing below was edited. Rerun `tools/borders.py` after all of it; never hand-merge generated files (CLAUDE.md).

1. `tools/tags.txt`: 22 new lines, 8 `|`-fields: `TAG | name | adjective | capital | template | culture | religion | r g b`
   (template `eurasian_tribe` for all). `-` as capital lets `borders.py` pick, but the capitals in 3.1 are checked and better.
2. `tools/overrides/70_east.txt` (new file, sorts after `60_himalaya.txt`; later lines win): begin with
   `!scope baltic_region russian_region ruthenia_region ural_region` (10_west already scopes carpathia and scandinavian),
   then area lines, then province lines, then location lines, like `10_west.txt`. Every name in section 3 was checked
   against `definitions.txt`. Slovakia needs care: `10_west.txt` already has `slovakia_area = none` and
   `pozsony_province = QAD`, and a later file wins, so `70_east.txt` may name `trencsen_province = QAD` etc. without
   touching those lines.
3. `tools/tag_map.txt`: no change; none of the proposed tags come from a geojson polygon.
4. `tools/ranks.txt`: add LUG ANE DBL GLJ MRY VES to `rank_duchy` (others default to county).
5. `tools/cultures.txt` and `tools/religions.txt`: they already give the pops of the six regions rules like
   `oka_area | * | aukstaitian` and `* | merya_culture | mari_paganism`. I found **no rule for `ural_region`**, no rule
   mapping `komi` (only `bjarmian`) to a religion, and none for `chuvash_culture`, `udmurt`, `komi`: add
   these, or the pops there stay on 1337 cultures (Tatar, Bashkir, Komi). Slovakia's `slovakia_area | * | suebian`
   would hold for CRP; add `szepes_province`, `zemplen_province` and `maramaros_province` rules for `dacian`.
6. `tools/settlements.txt`: `filter_unowned` in `borders.py` strips markets, towns and roads from unowned land. Once
   these locations are owned, vanilla's 1337 towns and market centres return (Moscow, Tver, Vladimir, Nizhny, Novgorod, Smolensk,
   Kazan, Riga, Tallinn, Vilnius). Pin the ones that did not exist in 395 as `rural` here.
7. `main_menu/common/coat_of_arms/coat_of_arms/tfe_countries.txt`: one flag per tag (`tools/test_flags.py` fails without it).
8. `main_menu/setup/start/12_diplomacy.txt` (hand-written, not generated): two `dependency = { first = HNS second = ANE
   subject_type = tributary }` lines (and CRP).
9. `tools/country_types.txt`: nothing. A tiny tribe can be `pop` (AI-only) if you do not want it playable; I did not pick that.
10. `tools/governments.txt`: nothing unless a ruler is written.
11. Python tests before a PR: `uv run --no-project --with numpy --with pytest --with pillow --with shapely python -m pytest -q tools/`.

## 6. Open questions and assumptions

1. **Does the gap belong in the map?** Any of the 22 can be dropped alone; no tag depends on another. Poland (LUG) and the far
   Kama peoples are the weakest historically.
2. **Poland**: Wielbark left, Przeworsk is fading, and the Slavs have not arrived. An empty Poland is the historical choice;
   LUG is the "fun over accuracy" one.
3. **Ves is the biggest tag (127 locations)** and takes the Novgorod core (Staraya Ladoga, Novgorod). Consider giving
   `volkhovskaya_province` to VOD, or splitting off a Pomorye tribe.
4. **Culture stand-ins**: IMK (chuvash_culture) and SRT (mansi_culture) are guesses because no vanilla culture fits; a new culture
   in `tfe_cultures.txt` would be better. Estonian and Finnish cultures also disagree with the `finland_area` pop rule.
5. **HNS fringe (25 locations)** has no source.
6. **Slovakia**: the east is filled by CRP as a design choice; Quadi extension (QAD+) removes nothing from `10_west.txt`.
7. **Unverified this session**: Lugii identification; Ves and Vasinabroncas; Kolochin's start date; Muroma; the Mari-Merens
   link; all Kama and Ural cultures (Pyany Bor, Azelino, Sargat, Kushnarenkovo); Tarand graves; the Free Dacians; the Gepids under
   the Huns. Their pages failed to load or I did not read them. Wikipedia is a secondary source throughout, and Jordanes
   wrote in 551 about the fourth century.
8. **Assumption**: "owned" means listed in `10_countries.txt` `own_control_core`. Unowned locations were counted only if they
   are land (not sea or non-ownable). A few "unowned" locations may be non-ownable in-game that the loader missed; run
   `borders.py` to confirm.
9. **Not done**: I did not run `borders.py` with these changes, so the tags, cultures and counts have not been through its
   `check_*` functions, and nothing was tested in game.
