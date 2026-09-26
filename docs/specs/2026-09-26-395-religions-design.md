# 395 religions

The pops, countries and characters of 395 get the faiths of the day after Theodosius died.

## Decisions

- **One Nicene church.** Vanilla `orthodox` is renamed "Nicene Christianity". It is used because its patriarchate
  mechanics need no Pope, and both empires hold it. `catholic` is unused in 395. Copts, Syrians, Armenians, Georgians
  and Aksum are Nicene: Ephesus (431) and Chalcedon (451) have not happened.
- **New religions** (`in_game/common/religions/tfe_religions.txt`, icons borrowed from vanilla):
  - `arianism`: the Goths, Gepids, Rugii, Sciri and Hasding Vandals, plus the Goths in Roman service.
  - `donatism`: Numidia, Sitifensis, Caesariensis, and the peasants of Proconsularis and Hippo.
  - `celtic_paganism`, `slavic_paganism` and `arabian_paganism`: the peoples vanilla has no faith for.
- **Vanilla religions switched on or renamed:**
  - `hellenism_religion` is REPLACEd without its 9999 `enable`.
  - `norse` is renamed "Germanic Paganism".
  - `nestorianism` is renamed "Church of the East" (Persia's Syriac Christians).
- **Pops** come from `tools/religions.txt` (same format as cultures.txt, run after it, and matching the pop's 395
  culture). Scope `*` means anywhere. Social-class rules make mixed places:
  - Symmachus' pagan senate in Rome.
  - Pagan Gallo-Roman peasants in Armorica, Belgica and the Rhine.
  - Celtic peasants under Christian Romano-British towns.
  - A Jewish court in Himyar over a pagan people.
- **Pagan pockets:** Harran, Baalbek, Gaza, Philae (Aswan), Laconia, Athens' nobles, Panopolis' nobles, the Anaunians
  of Trentino, and the Vascones.
- **Nubia and Aksum:** a new `kushite_religion` (Amun, Apedemak, Isis) for the Nobades and Blemmyes. Aksum has a
  Nicene court, clergy and burghers over peasants who keep Almaqah and Mahrem (`arabian_paganism`).
- **The wider world:** no pop anywhere keeps a faith born after 395 (`LATE_FAITHS` in borders.py: Islam, the Latin
  and medieval churches, Miaphysitism, Tibetan Buddhism). `purge_late_faiths` gives such a pop the commonest older
  faith of its culture in the region, else of its area, else of its region. Rules cover the places where nothing older
  is near: Bön for Tibet, Waaq for Somalia, Buddhism for the Tarim oases, Germanic paganism for the North Atlantic.
- **Result:** the WRE is about two thirds Nicene; the EAR is about 95% Nicene.

## Minorities and the reference map (2026-09-26)

- **Mixed rules.** A rule's target may be a mix (`religio_romana 55 orthodox 45`). The pop is split by size, and the
  biggest share colours the map. The other shares live on as minorities, so over 80% of Roman places hold several faiths.
- **Town and country.** In the Roman world, clergy are Nicene. Burghers and nobles are mostly Nicene with a pagan
  fifth, and area rules set the mix for everyone else (peasants, tribesmen, slaves).
- **Target.** The map follows the user's Fallen Eagle reference: a Nicene church in the towns over a pagan countryside,
  with the sects of the day in their home provinces.
- **New faiths:**
  - `religio_romana`: the Latin West's old gods. `hellenism_religion` is now the Greek East only.
  - `priscillianism`: Gallaecia and Avila.
  - `montanism`: Phrygia.
  - `messalianism`: Mesopotamia.
  - `nuragic_religion`: the Barbaricini.
  - `basque_paganism`: the Vascones.
  - `zalmoxism`: the Dacian peasants under the Gepids and Huns.
  - `illyrian_paganism`: Illyricum's local gods.
  - `armazi_religion`: the Iberian countryside.
- **Reused vanilla faiths:**
  - Manichaeism: Septimania, Malaga and Granada, Africa, Egypt, Palmyra and Babylonia.
  - Celtic paganism: Armorica, Belgica, Noricum, Asturias and Galatia.
  - Zoroastrianism: the Magusaeans of Cappadocia and Persarmenia.
- **Illyricum.** The reference calls it "Tadenusism", but Tadenus is one altar: Apollo Tadenus at the Bosna springs
  (CIL III 13858). Illyrian cult was local:
  - the sun in the north and the serpent in the south;
  - Silvanus, Vidasus and Thana;
  - Bindus of the Iapodes, Medaurus of Risinium and Redon of the sailors.

  So the faith is "Illyrian Paganism", placed by tribe. The hinterland of the Delmatae, Iapodes and Daesitiates is
  Illyrian; Sirmium, Salona, Sopianae, Naissus and the Danube forts are Nicene.

## Later

- The Papacy (needs a Bishop of Rome tag).
- Patriarchates for Rome, Constantinople, Alexandria and Antioch.
- Zoroastrian fire-temple holy sites.
- Events for Ephesus and Chalcedon to split off the Church of the East and the Miaphysites.
- Priscillianism in Gallaecia and Pelagius.
