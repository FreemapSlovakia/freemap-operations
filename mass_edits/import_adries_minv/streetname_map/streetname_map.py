#!/usr/bin/env python
import sys
"""
Mapovanie nespravnych nazvov ulic na spravne (alebo aspon spravnejsie).

Pri upravach sa riadim nasledovnym:
    - zakladne typograficke pravidla (medzera za bodkou, spojovnik bez medzery)
    - slovenska gramatika (velke/male, nespravna diakritika, pravidlo rytmickeho kratenia a i.)
    - VZN uverejnenych na webstranke obce
    - ine verejne dostupne zdroje

Pozri tiez:
    https://jazykovaporadna.sme.sk/q/1332/

  Ak je v názve ulice prídavné meno utvorené od všeobecného podstatného mena
  alebo akostné prídavné meno (na ktoré sa pýtame otázkou aká?), je na konci
  dlhá prípona, napr. Púpavová ulica, Prístavná ulica, Dlhá ulica, Stromová
  ulica (s výnimkou názvov, v ktorých sa prípona skracuje z dôvodu dodržiavania
  pravidla o rytmickom krátení, teda v ktorých je predposledná slabika dlhá,
  napr. Robotnícka ulica,Krátka ulica, Račianska ulica).

  Krátka prípona v názve ulice je vtedy, keď sa v nej použilo privlastňovacie
  prídavné meno utvorené od osobného mena, na ktoré sa pýtame otázkou čia? (nie
  aká?), napr. Štúrova ulica, Štefánikova ulica.

    https://jazykovaporadna.sme.sk/q/1483/

  Podľa súčasných Pravidiel slovenského pravopisu (posledné vydanie je z r.
  2000) sa s veľkým začiatočným písmenom píšu všetky plnovýznamové slová vo
  viacslovných názvoch miest (napr. Spišská Nová Ves, Nové Mesto nad Váhom),
  obcí (napr. Plavecké Podhradie, Špania Dolina) a častí obcí (napr. Ladislavov
  Dvor, Čierna Voda) a vtedy, keď sa vlastné meno stáva súčasťou viacslovného
  mena, napr. pri názve pohorí Karpaty – Malé Karpaty, Tatry – Vysoké Tatry.
  Pri názvoch štátov, krajín, hradov a zámkov sa s veľkým začiatočným písmenom
  píšu všetky plnovýznamové slová vtedy, keď podstatné meno v názve neoznačuje
  štát, krajinu, hrad alebo zámok, napr. Pobrežie Slonoviny (štát), Červený
  Kameň (hrad).

  Pri viacslovných názvoch ulíc neplatí pravidlo o písaní všetkých
  plnovýznamových slov s veľkým začiatočným písmenom, preto sa názov ulice
  Mlynské nivy píše s veľkým začiatočným písmenom iba na začiatku názvu. Veľké
  začiatočné písmeno vo viacslovnom názve ulice sa píše vtedy, keď je jeho
  súčasťou iné vlastné meno, napr. Pod Hrebienkom, Nad Bielym krížom (názvy
  bratislavských ulíc).

https://jazykovaporadna.sme.sk/q/7955/
  Zásada, že ak má názov ulice formu nezhodného prívlastku, daný prívlastok za
  slovom ulica sa píše s malým začiatočným písmenom, platí iba v prípade, ak
  nezhodný prívlastok predstavuje všeobecné pomenovanie, napr. Ulica slobody,
  Ulica duklianskych hrdinov. Ak vo funkcii nezhodného prívlastku vystupuje
  vlastné meno, prívlastok sa píše s veľkým začiatočným písmenom, napr. Ulica
  Slovenského národného povstania, Ulica Prvého mája  (Prvý máj – názov
  sviatku), Ulica Jána Kostru. V takýchto názvoch slovo ulica stojí na začiatku
  príslušného pomenovania, je jeho súčasťou, a keďže signalizuje začiatok
  vlastného mena, píše sa s veľkým začiatočným písmenom (porov. aj názvy
  Námestie Jána Kostru, Nábrežie arm. gen. Ludvíka Svobodu). Iným typom sú
  názvy ulíc, v ktorých druhové označenie ulica stojace pred vlastným
  pomenovaním nie je súčasťou vlastného mena, a preto sa píše s malým
  začiatočným písmenom (názvom ulice je zvyčajne predložkové spojenie), napr.
  ulica Pri starom mýte, ulica Na bôriku, ulica Na paši, ulica Pri Habánskom
  mlyne, ulica Na Slavíne (ulice sa volajú Pri starom mýte, Na bôriku, Na paši,
  Pri Habánskom mlyne, Na Slavíne – porov. Pravidlá slovenského pravopisu,
  2000, VIII. kapitola Písanie veľkých písmen, podkapitola 1.3.2. Názvy
  objektov vo vesmíre a názvy útvarov na ich povrchu, 7. bod Názvy ľudských
  sídel, ich častí a verejných priestranstiev, s. 63).

  Vlastným menom Kalvária sa označuje miesto v Jeruzaleme, kde bol ukrižovaný
  Ježiš Kristus. Názov kalvária, ktorým sa pomenúva návršie so zastaveniami
  znázorňujúcimi výjavy z umučenia a ukrižovania Ježiša Krista, ako aj umelecké
  stvárnenie umučenia a ukrižovania Ježiša Krista, je všeobecné pomenovanie a
  píše sa s malým začiatočným písmenom (porov. Krátky slovník slovenského
  jazyka, 2003, i Slovník cudzích slov, 2005). Mnohé mestá i obce majú takéto
  návršie zobrazujúce krížovú cestu, okrem Topoľčian napr. Banská Štiavnica,
  Nitra, Prešov, Bardejov, Ružomberok i Bratislava, kde sa jedna z ulíc nazýva
  Na Kalvárii a iná Pod Kalváriou. Názvy oboch ulíc sa odvodzujú od
  štandardizovaného nesídelného názvu bratislavského vrchu Kalvária. Keďže ide
  o vlastné meno, píše sa s veľkým začiatočným písmenom i v názvoch ulíc.
  Uplatňuje sa tu zásada formulovaná v Pravidlách slovenského pravopisu, podľa
  ktorej vlastné meno, ktoré je súčasťou viacslovného vlastného mena, ponecháva
  si veľké písmeno na ktoromkoľvek mieste názvu, napr. Amerika – Južná Amerika,
  Červený kríž – Slovenský Červený kríž, Univerzita Komenského – Filozofická
  fakulta Univerzity Komenského, Spojené národy – Organizácia Spojených
  národov, tak aj Kalvária – Na Kalvárii, Pod Kalváriou (porov. kap. VI.
  Písanie veľkých písmen, podkap. 1. 2. Zásady písania veľkých písmen vo
  vlastných menách, s. 53). Slovo ulica tak ako v názvoch ulíc typu Pri starom
  mýte, Na Slavíne tu nie je súčasťou názvu, iba ho bližšie určuje, a preto sa
  píše s malým začiatočným písmenom: ulica Na Kalvárii, ulica Pod Kalváriou.
  Podobne je to s pomenovaním ulice Pod Kalváriou v Nitre, kde sa vlastným
  menom Kalvária označuje takisto vrch. V Topoľčanoch sa vlastným menom
  Kalvária označuje nesídelný pôvodný názov poľa, preto aj tu je namieste písať
  názov ulice v podobe Pod Kalváriou.

Nepouzite nahrady + odovodnenie
  'A. Jedlika': 'Á. Jedlika', - moze sa jednat bud o Ániosa alebo Aniána
  'Blahova': 'Bláhova' - Pavel Blaho, Anton Blaha, ale aj ??? Bláha
  'Červeňákova': 'Červenákova' - Benjamín Pravoslav Červenák vs Andrej Červeňák
  'Čsl. armády': 'Čsľ. armády' - Československej ľudovej armády != Česko-slovenskej armády
  'Drahy': 'Dráhy' - informacia z VZN + OSM o tom, ze "Drahy" je spravne
  'Gogolova': 'Gogoľova' - web mesta Trencianske Teplice
  'Hlinická': 'Hlinícka' - web mesta Bytča (ale pozor na Zavar!)
  'Hrbky': 'Hŕbky' - http://www.liptovskesliace.sk/kontakt/zoznam-ulic/?ftresult=hrbky
  'Janka Matúšku': 'Janka Matušku' - pravdepodobne oba prepisy su spravne
  'Kalinová': 'Kalinova' - web obci
  'Križná': 'Krížna' - frekvencia oboch nazvov
  'Laurínska': 'Laurinská' - web obce Badin
  'Lycejná': 'Lýcejná' - obchodny register
  'Mikuláša Koperníka': 'Mikuláša Kopernika' - http://www.trnava.sk/sk/clanok/zoznam-ulic
  'Nemcovej': 'Němcovej' - pouzivaju sa oba prepisy mena
  'Nevädzová': 'Nevädzova' - https://www.nitra.sk/Zobraz/Obsah/18113
  'Potočky': 'Potôčky' - http://www.kokava.sk/download_file_f.php?id=707944
  'Pusta': 'Pustá' - http://www.ulany.sk/files/dokumenty/2015-10-20.pdf
  'Rákocziho': 'Rákócziho' - pravdepodobne oba prepisy su spravne
                             madarske meno 9rztm. kratenie neplati0
  'Seredská': 'Sereďská' - web mesta Trnava
  'Svätého Urbána': 'Svätého Urbana' - http://www.svodin.sk/turisticky-portal/o-obci/zoznam-ulic/
  'Vršok': 'Vŕšok' - http://foaf.sk/firmy/467159
  'Zákostolská': 'Zakostolská' - weby obci

"""

replacement_map = {
    # spojovnik je bez medzery pred i za nim
    'A. Lackovej - Zory': 'A. Lackovej-Zory',
    'Boženy Slančíkovej- Timravy': 'Boženy Slančíkovej-Timravy',

    # bodka na konci
    'Floriánske námestie.': 'Floriánske námestie',

    # nelogicke skracovanie slov
    '26. nov.': '26. novembra',
    'Máj. Povst. Čes. Ľ.': 'Májového povst. českého ľudu',
    'Slov. nár. pov.': 'SNP',

    # porusene pravidlo rytmickeho kratenia
    'Banícká': 'Banícka',
    'Cintorínská': 'Cintorínska',
    'Dobránska': 'Dobranská',
    'F. Rákócziho': 'F. Rákocziho',
    'Hájská': 'Hájska',
    'Hornocintorínská': 'Hornocintorínska',
    'Hviezdná': 'Hviezdna',
    'Kalinčiaková': 'Kalinčiakova',
    'Kaštieľná': 'Kaštieľna',
    'Keblianská': 'Keblianska',
    'Kollárová': 'Kollárova',
    'Kossúthova': 'Kossuthova',
    'Kossúthová': 'Kossuthova',
    'Kováčská': 'Kováčska',
    'Krížná': 'Krížna',
    'Krtíšská': 'Krtíšska',
    'Krtíšská': 'Krtíšska',
    'Kutlíková': 'Kutlíkova',
    'Lúčná': 'Lúčna',
    'Mládežnícká': 'Mládežnícka',
    'Morovnianská': 'Morovnianska',
    'Na výhliadke': 'Na vyhliadke',
    'Partizánská': 'Partizánska',
    'Pionierská': 'Pionierska',
    'Priečná': 'Priečna',
    'Rybárská': 'Rybárska',
    'Sibírská': 'Sibírska',
    'Topoľčianská': 'Topoľčianska',
    'Trenčianská': 'Trenčianska',
    'Ústianská': 'Ústianska',
    'Úzká': 'Úzka',
    'Vážská': 'Vážska',
    'Vlárska': 'Vlárska',
    'Vlárská': 'Vlárska',
    'Zemianská': 'Zemianska',
    'Železničiarská': 'Železničiarska',

    # chybajuca diakritika
    'Agátova': 'Agátová',
    'Cergátova': 'Cergátová',
    'Kaštiel Pata': 'Kaštieľ Pata',
    'Agatová': 'Agátová',
    'Albinov': 'Albínov',
    'Albinovska': 'Albínovská',
    'Albinovská': 'Albínovská',
    'Alžbetinská': 'Alžbetínska',
    'A. Sladkoviča': 'A. Sládkoviča',
    'Baštova': 'Baštová',
    'Bitunková': 'Bitúnková',
    'Borodačova': 'Borodáčova',
    'Bronzova': 'Bronzová',
    'Budovateľska': 'Budovateľská',
    'Budovatelská': 'Budovateľská',
    'Červenova': 'Červeňova',
    'Chmelová': 'Chmeľová',
    'Dlha Lúka': 'Dlhá Lúka',
    'Hugolina Gavloviča': 'Hugolína Gavloviča',
    'Drahová': 'Dráhová',
    'Dukelska': 'Dukelská',
    'Fakľova': 'Fakľová',
    'Festivalova': 'Festivalová',
    'Fraňa Krála': 'Fraňa Kráľa',
    'Gaštanova': 'Gaštanová',
    'Grobska': 'Grobská',
    'Hanzlikovská': 'Hanzlíkovská',
    'Harmančekova': 'Harmančeková',
    'Hlboka': 'Hlboká',
    'Hlinik': 'Hliník',
    'Horešska': 'Horešská',
    'Hradišska': 'Hradišská',
    'Hradocká': 'Hrádocká',  # http://www.obeclieskovec.sk/organizacie/podnikatelia-v-obci-1/?ftresult=hradocka
    'Hreždovská': 'Hrežďovská',  # http://www.banovce.sk/?id_menu=1316&limited_level=1&stop_menu=540
    'J. A. Komenskeho': 'J. A. Komenského',
    'Jana Hollého': 'Jána Hollého',
    'Jana Kollára': 'Jána Kollára',  # http://www.malacky.sk/_docs/ZOZNAM%20ULIC%20A%20OKRSKOV.pdf
    'Jánošikova': 'Jánošíkova',
    'Janošíkova': 'Jánošíkova',
    'Jantárova': 'Jantárová',
    'Jarkova': 'Jarková',
    'Jaseňova': 'Jaseňová',
    'J. Krála': 'J. Kráľa',
    'Júliusa Fučíka': 'Juliusa Fučíka',
    'J. Zaborského': 'J. Záborského',
    'Kaštielna': 'Kaštieľna',
    'Kaštielná': 'Kaštieľna',
    'Klačany': 'Kľačany',
    'Klinčekova': 'Klinčeková',
    'Komenskeho': 'Komenského',
    'Konvalinkova': 'Konvalinková',
    'Kukučinova': 'Kukučínova',
    'Kúpelna': 'Kúpeľná',
    'Kúpelná': 'Kúpeľná',
    'Kupeľná': 'Kúpeľná',
    'Kúpelska': 'Kúpeľská',
    'Kútova': 'Kútová',
    'Kvetna': 'Kvetná',
    'Kvetova': 'Kvetová',
    'Lávkova': 'Lávková',
    'Licionska': 'Licionská',
    'Lieskovska': 'Lieskovská',
    'Lipova': 'Lipová',
    'Litovelska': 'Litovelská',
    'Ľudovita Štúra': 'Ľudovíta Štúra',
    'Májova': 'Májová',
    'Marhuľova': 'Marhuľová',
    'Marianska': 'Mariánska',
    'Michalska': 'Michalská',
    'Mierova': 'Mierová',
    'Mlynska': 'Mlynská',
    'Mostova': 'Mostová',
    'Môtovská cesta': 'Môťovská cesta',
    'Mrazová': 'Mrázová',  # http://www.bratislava.sk/assets/File.ashx?id_org=700000&id_dokumenty=11052914
    'M. R. Štefanika': 'M. R. Štefánika',
    'Muškátova': 'Muškátová',
    'Nádražna': 'Nádražná',
    'Na Hlinik': 'Na Hliník',
    'Na Hlinik': 'Na Hliník',
    'Na Horke': 'Na Hôrke',
    'Námestie Ľudovita Štúra': 'Námestie Ľudovíta Štúra',
    'Námestie Ľudovita Štúr': 'Námestie Ľudovíta Štúr',
    'Narcisova': 'Narcisová',
    'Na Zahradách': 'Na záhradách',
    'Na Zahumní': 'Na záhumní',
    'Nezábudkova': 'Nezábudková',
    'Nezabudková': 'Nezábudková',
    'Nova': 'Nová',
    'Novozámocka': 'Novozámocká',
    'Okružna': 'Okružná',
    'Orgovánova': 'Orgovánová',
    'Orgovanová': 'Orgovánová',
    'Orlova': 'Orlová',
    'Parkova': 'Parková',
    'Pasienkova': 'Pasienková',
    'Plánkova': 'Plánková',
    'Platanova': 'Platanová',
    'Plechoticka': 'Plechotická',
    'Poľna cesta': 'Poľná cesta',
    'Polná': 'Poľná',
    'Polská': 'Poľská',
    'Poštova': 'Poštová',
    'Prejtska': 'Prejtská',
    'Prídavkova': 'Prídavková',  # http://www.old.sabinov.sk/obcan/uradna-tabua/prekopavky.html
    'Puchovská': 'Púchovská',
    'Rakove': 'Rakové',
    'Ráztocka': 'Ráztocká',
    'Ríbezlová': 'Ríbezľová',
    'Rozmarínova': 'Rozmarínová',
    'Ružova': 'Ružová',
    'Rybniková': 'Rybníková',
    'Sadova': 'Sadová',
    'Šafarikova': 'Šafárikova',
    'Sidl. Hanza': 'Sídl. Hanza',
    'Škovrančia': 'Škovránčia',
    'Škultetyho': 'Škultétyho',
    'Sladkovičova': 'Sládkovičova',
    'Sladkovičová': 'Sládkovičova',
    'Slávikova': 'Sláviková',  # http://www.obecdobraniva.sk/e_download.php?file=data/editor/140sk_1.pdf&original=1_vysledky_komunalnych_volieb_2014_starosta.pdf
    'Smrekova': 'Smreková',
    'Snežienkova': 'Snežienková',
    'Solna': 'Soľná',
    'Solná': 'Soľná',
    'Šoltesovej': 'Šoltésovej',
    'Športova': 'Športová',
    'Štadionová': 'Štadiónová',
    'Štefanikova': 'Štefánikova',
    'Strednočepenská': 'Strednočepeňská',  # http://www.sered.sk/sered-zoznam-ulic
    'Strma': 'Strmá',
    'Tabakova': 'Tabaková',
    'Tajovskeho': 'Tajovského',
    'Tatranska': 'Tatranská',
    'Tomašikova': 'Tomášikova',  # http://www.jelsava.sk/index.php?id_menu=0&module_action__294023__id_ci=123345
    'Továrenska': 'Továrenská',
    'Trávnicka': 'Trávnická',
    'Trstie': 'Tŕstie',
    'Tulipánova': 'Tulipánová',
    'Tulipanová': 'Tulipánová',
    'Turbínova': 'Turbínová',
    'Ustianska': 'Ústianska',
    'Valkovská': 'Vaľkovská',
    'V. B. Nedožerskeho': 'V. B. Nedožerského',
    'Vodárenska': 'Vodárenská',
    'Vrbova': 'Vŕbová',  # https://www.kosice.sk/ulice.php
    'Vršky': 'Vŕšky',  # osm
    'Vysoka': 'Vysoká',
    'Zahradná': 'Záhradná',
    'Záhradnicka': 'Záhradnícka',
    'Zahradnícka': 'Záhradnícka',
    'Zámočnicka': 'Zámočnícka',  # https://www.kosice.sk/ulice.php
    'Za Zahradami': 'Za záhradami',
    'Zelena': 'Zelená',
    'Žriedlova dolina': 'Žriedlová dolina',
    'Zvončekova': 'Zvončeková',

    # nadbytocna diakritika
    'Bernoláková': 'Bernolákova',
    'Šagátová': 'Šagátova',  # Tibor Šagát
    'Čierný les': 'Čierny les',
    'Betliarská': 'Betliarska',
    'Brigádnická': 'Brigádnicka',
    'Bulíková': 'Bulíkova',
    'Chalúpkova': 'Chalupkova',
    'Chalúpková': 'Chalupkova',
    'Cyrila a Metóda': 'Cyrila a Metoda',
    'Devátová': 'Devátova',
    'Donátová': 'Donátova',
    'Dovčíková': 'Dovčíkova',
    'Ferletová': 'Ferletova',
    'Gen. Goliána': 'Gen. Goliana',
    'Gottwaldová': 'Gottwaldova',
    'Hviezdoslavová': 'Hviezdoslavova',
    'Ivana Krásku': 'Ivana Krasku',
    'Jána Ámosa Komenského': 'Jána Amosa Komenského',  # https://register.finance.sk/adresa-92522-velke-ulany-jana-amosa-komenskeho-16-1886231
    'Jánošíková': 'Jánošíkova',
    'Káplnská': 'Kaplnská',
    'K. Harmoša': 'K. Harmosa',  # http://komarnodnes.sk/wp-content/uploads/2014/11/Zoznam-adries-za%C4%8Dlenen%C3%BDch-v-jednotliv%C3%BDch-okrskoch.pdf
    'Kukučínová': 'Kukučínova',
    'Leninová': 'Leninova',
    'Ľ. Kossutha': 'L. Kossutha',  # http://www.kralovskychlmec.sk/ms-ul-kossutha.phtml?id_menu=32414&limited_level=1&stop_menu=32414
    'L. Kossútha': 'L. Kossutha',  # http://www.tvrdosovce.sk/obecny-urad/dokumenty/category/34-vzn-platne?download=664:vzn-697-o-sposobe-oznaovania-ulic-a-inych-verejnych-priestranstiev-a-o-islovani-stavieb
    'Madáchová': 'Madáchova',
    'Malodvornícká cesta': 'Malodvornícka cesta',
    'Mičurínova': 'Mičurinova',  # http://www.obecdedinamladeze.sk/-historia
    'Mikszáthová': 'Mikszáthova',
    'M. Jankoľu': 'M. Jankolu',  # Matúš Jankola (http://www.old.trstena.sk/index.php?option=com_content&task=view&id=1704&Itemid=109)
    'Morovnianská cesta': 'Morovnianska cesta',
    'Nígrob': 'Nigrob',  # http://bela.sk/dokumenty/Zmluvy%2C%20fakt%C3%BAry%20a%20objedn%C3%A1vky/2016/Preh%C4%BEad%20objedn%C3%A1vok%202016%20-%20Obec%20Bel%C3%A1.pdf
    'Obráncov mieru': 'Obrancov mieru',
    'Obráncov Mieru': 'Obrancov mieru',
    'Padlíčkovo': 'Padličkovo',  # https://www.brezno.sk/docpublishing/contracts/zmluva_o_vypozicke_c.483.pdf
    'Pekáreňská': 'Pekárenská',  # http://volkovce.sk/en/business-entities/
    'Pod Teheľňou': 'Pod tehelňou',
    'Predné Hálny': 'Predné Halny',  # https://www.brezno.sk/mestski-poslanci-schvalili-buducu-kupu-bytoveho-domu-predne-halny-10/ + pozri tiez Zadne Halny
    'Puškinová': 'Puškinova',
    'Šafáriková': 'Šafárikova',
    'Sama Chalúpku': 'Sama Chalupku',
    'S. Chalúpku': 'S. Chalupku',
    'Schubertová': 'Schubertova',
    'Škovránková': 'Škovránkova',
    'Sládkovičová': 'Sládkovičova',
    'Sládkovičová': 'Sládkovičova',
    'Š. Petöfiho': 'S. Petöfiho',  # http://www.kralovskychlmec.sk/?id_menu=59626&module_action__186057__paging=23
    'Špitalská': 'Špitálska',
    'Šrobárová': 'Šrobárova',
    'Štefániková': 'Štefánikova',
    'Štúrová': 'Štúrova',
    'Súkenická': 'Súkenícka',  # https://www.modra.sk/mestske-centrum-socialnych-sluzieb-modra/os-1059
    'Teheľňa': 'Tehelňa',
    'Teslová': 'Teslova',
    'Tyršová': 'Tyršova',
    'Vodáreňská': 'Vodárenská',  # http://samorin.sk/volby-2016-rozdelenie-okrskov/
    'Zadné Hálny': 'Zadné Halny',  # https://www.brezno.sk/statut-a-kompetencie-mesta/
    'Zákamenica': 'Zakamenica',  # http://www.rajec.info/files/66553-2017-142-dodatok-1-ZML-2017-114.pdf
    'Ž. Bošniakovej': 'Ž. Bosniakovej',  # je Bosniaková alebo Bošňáková
    'Zigmundíková': 'Zigmundíkova',

    # chybna diakritika
    'Andreja Trúchleho Sitnianskeho': 'Andreja Truchlého Sitnianskeho',
    'Cintorinská': 'Cintorínska',
    'Cukrovárska': 'Cukrovarská',
    'Cyrilometódska': 'Cyrilometodská',
    'Dobrovoľnická': 'Dobrovoľnícka',
    'Kukučinová': 'Kukučínova',
    'Kunerádska': 'Kuneradská',  # http://www.bratislava.sk/assets/File.ashx?id_org=700000&id_dokumenty=11052914
    'Mikszathová': 'Mikszáthova',
    'Mládežnická': 'Mládežnícka',
    'Mlýnska': 'Mlynská',
    'Námestie Jána Kálvina': 'Námestie Jána Kalvína',
    'Okruhlá': 'Okrúhla',
    'Petőfiho': 'Petöfiho',  # osm + https://register.finance.sk/adresa-08001-presov-petofiho-2-2301743
    'Pöschlova': 'Pőschlova',  # https://register.finance.sk/adresa-08001-presov-poschlova-15-2304134
    'Požiarnícka': 'Požiarnická',  # http://www.zilina.sk/co-sa-urobilo/231/
    'Rőntgenova': 'Röntgenova',
    'Rybarská': 'Rybárska',
    'Sladkovičová': 'Sládkovičova',
    'Striebornická': 'Striebornícka',
    'Šafariková': 'Šafárikova',
    'Tomašíkova': 'Tomášikova',  # http://www.mestotornala.sk/?program=295&module_action__0__id_z=93940 http://www.jelsava.sk/index.php?id_menu=0&module_action__294023__id_ci=123345
    'Tulčická': 'Tulčícka',  # http://www.velkysaris.sk/?search_string=tulcicka&search_string_verify=&post_verification=4a5f0fb2ad254a791d61653303bef7ce
    'Vinohradnická': 'Vinohradnícka',

    # chybajuca bodka
    'Palešovo nám': 'Palešovo nám.',
    'Slovenského Národného povst': 'Slovenského národného povst.',
    'Slovenského národného povst': 'Slovenského národného povst.',

    # velke/male pismena
    'Červeného Kríža': 'Červeného kríža',
    'Červenej Armády': 'Červenej armády',
    'Nábrežie čiernej vody': 'Nábrežie Čiernej vody',
    'Československej Armády': 'Československej armády',
    'Cesta na Červený Most': 'Cesta na Červený most',
    'Cesta Osloboditeľov': 'Cesta osloboditeľov',
    'Čierne Blato': 'Čierne blato',
    'Čsl. Armády': 'Čsl. armády',
    'Čsl. Brigády': 'Čsl. brigády',
    'Dlhé Hony': 'Dlhé hony',
    'Dlhý Rad': 'Dlhý rad',
    'Do Mlyna': 'Do mlyna',
    'Družstevný Rad': 'Družstevný rad',
    'Februárového Víťazstva': 'Februárového víťazstva',
    'Gaštanový Rad': 'Gaštanový rad',
    'Horný Rad': 'Horný rad',
    'Krátky Rad': 'Krátky rad',
    'Krivý Kút': 'Krivý kút',
    'Ku Kaplnke': 'Ku kaplnke',
    'K Vinohradom': 'K vinohradom',
    'Lipový Rad': 'Lipový rad',
    'Ľ. štúra': 'Ľ. Štúra',
    'Malá Okružná': 'Malá okružná',
    'Malá Ulička': 'Malá ulička',
    'Malý Rad': 'Malý rad',
    'Matice Slovenskej': 'Matice slovenskej',
    'Mlynský Rad': 'Mlynský rad',
    'Na Barine': 'Na barine',
    'Na Brezinách': 'Na brezinách',
    'Nad Brehmi': 'Nad brehmi',
    'Nad Jazerom': 'Nad jazerom',
    'Nad Mlynom': 'Nad mlynom',
    'Na Dolinu': 'Na dolinu',
    'Nad Potokom': 'Nad potokom',
    'Nad Školou': 'Nad školou',
    'Nad Tehelňou': 'Nad tehelňou',
    'Na Hlinách': 'Na hlinách',
    'Na Hôrke': 'Na hôrke',
    'Na Hôrke': 'Na hôrke',
    'Na Hrádzi': 'Na hrádzi',
    'Pod Hrádzou': 'Pod hrádzou',
    'Na Kopci': 'Na kopci',
    'Na Lánoch': 'Na lánoch',
    'Na Lúkach': 'Na lúkach',
    'Námestie Baníkov': 'Námestie baníkov',
    'Námestie Osloboditeľov': 'Námestie osloboditeľov',
    'Námestie Padlých hrdinov': 'Námestie padlých hrdinov',
    'Námestie Požiarnikov': 'Námestie požiarnikov',
    'Námestie Republiky': 'Námestie republiky',
    'Námestie Rodiny': 'Námestie rodiny',
    'Nám. Osloboditeľov': 'Nám. osloboditeľov',
    'Nám. Osloboditeľov': 'Nám. osloboditeľov',
    'Na Pažiti': 'Na pažiti',
    'Na Priekope': 'Na priekope',
    'Na Rovni': 'Na rovni',
    'Na Rybníku': 'Na rybníku',
    'Na Sihoti': 'Na sihoti',
    'Na Skotni': 'Na skotni',
    'Na Stráni': 'Na stráni',
    'Na Vŕšku': 'Na vŕšku',
    'Na Vyhliadke': 'Na vyhliadke',
    'Na Výhone': 'Na výhone',
    'Na Záhumní': 'Na záhumní',
    'Nová Štvrť': 'Nová štvrť',
    'Nový Dvor': 'Nový dvor',
    'Nový Rad': 'Nový rad',
    'Nový Svet': 'Nový svet',
    'Orechový Rad': 'Orechový rad',
    'Pod Agátmi': 'Pod agátmi',
    'Pod Baštou': 'Pod baštou',
    'Pod Brehom': 'Pod brehom',
    'Pod Čerencom': 'Pod Čerencom',
    'Pod Hôrkou': 'Pod hôrkou',
    'Pod Horou': 'Pod horou',
    'Pod Hrádkom': 'Pod hrádkom',
    'Pod Hradom': 'Pod hradom',
    'Pod Kalváriou': 'Pod kalváriou',
    'Pod Kaplnkou': 'Pod kaplnkou',
    'Pod Kaštieľom': 'Pod kaštieľom',
    'Pod Kostolom': 'Pod kostolom',
    'Pod Krížom': 'Pod krížom',
    'Pod Lesom': 'Pod lesom',
    'Pod Lipami': 'Pod lipami',
    'Pod Lipkou': 'Pod lipkou',
    'Pod Lipou': 'Pod lipou',
    'Pod Poliankou': 'Pod poliankou',
    'Pod Tehelňou': 'Pod tehelňou',
    'Pod Úbočou': 'Pod úbočou',
    'Pod Vinicami': 'Pod vinicami',
    'Pod Vinicou': 'Pod vinicou',
    'Pod Vinohradmi': 'Pod vinohradmi',
    'Pod Vodojemom': 'Pod vodojemom',
    'Pod Vŕškom': 'Pod vŕškom',
    'Pod Záhradami': 'Pod záhradami',
    'Poľský Dvor': 'Poľský dvor',
    'Pri Cintoríne': 'Pri cintoríne',
    'Pri Hati': 'Pri hati',
    'Pri hliníku': 'Pri Hliníku',
    'Pri Jazere': 'Pri jazere',
    'Pri kamennom moste': 'Pri Kamennom moste',
    'Pri Kamennom Moste': 'Pri Kamennom moste',
    'Pri Kaplnke': 'Pri kaplnke',
    'Pri Kríži': 'Pri kríži',
    'Pri Mlyne': 'Pri mlyne',
    'Pri Potoku': 'Pri potoku',
    'Pri Rybníku': 'Pri rybníku',
    'Pri Štadióne': 'Pri štadióne',
    'Pri Tehelni': 'Pri tehelni',
    'Pri Zvonici': 'Pri zvonici',
    'Roľníckej Školy': 'Roľníckej školy',
    'Rumunskej Armády': 'Rumunskej armády',
    'Slovenského Národného Povst': 'Slovenského národného povst.',
    'Slovenskej Jednoty': 'Slovenskej jednoty',
    'Slov. Národného Povstania': 'Slov. národného povstania',
    'Slov. Národ. Povstania': 'Slov. národ. povstania',
    'Slov. Nár. Povstania': 'Slov. nár. povstania',
    'Sovietskej Armády': 'Sovietskej armády',
    'Veľká Ulička': 'Veľká ulička',
    'Vyšný Mlyn': 'Vyšný mlyn',
    'Za Jarkom': 'Za jarkom',
    'Za Kalváriou': 'Za kalváriou',
    'Za Kasárňou': 'Za kasárňou',
    'Za Kaštieľom': 'Za kaštieľom',
    'Za Kostolom': 'Za kostolom',
    'Za Mlynom': 'Za mlynom',
    'Za Mostom': 'Za mostom',
    'Za Poštou': 'Za poštou',
    'Za Potokom': 'Za potokom',
    'Za Školou': 'Za školou',
    'Za Štadiónom': 'Za štadiónom',
    'Za Tehelňou': 'Za tehelňou',
    'Za Traťou': 'Za traťou',
    'Za Vodou': 'Za vodou',
    'Za Záhradami': 'Za záhradami',
    'Ro Gazárka': 'RO Gazárka',
    'Nám. Slovenskej Republiky': 'Nám. Slovenskej republiky',
    'Pri Železničnej Stanici': 'Pri železničnej stanici',
    'Psk Rybníčky ': 'PSK Rybníčky',
    'Pri Vyšnej Hati': 'Pri Vyšnej hati',
    'Pri Miklušovej Väznici': 'Pri Miklušovej väznici',
    'Pod 100 Lipami': 'Pod 100 lipami',
    'Dlhá Lúka': 'Dlhá lúka',
    'Dolné Hony': 'Dolné hony',
    'Dolné Hrady': 'Dolné hrady',
    'Slovenského Raja': 'Slovenského raja',
    'Slovenského Nár. povstania': 'Slovenského nár. povstania',

    # chybny pravopis
    'Kubányho': 'Kubániho',  # Ľudovít Kubáni
    'Ku Kamennému Stľpu': 'Ku kamennému stĺpu',  # Ľudovít Kubáni
    'Bjőrnsonova': 'Björnsonova',
    'Pri Celulozke': 'Pri celulózke',
    }


# nahrady len v ramci jednej obce
# gramaticky nespravne, avsak obec ich viackrat uvadza ako oficialne nazvy na svojich
# strankach
muni_replacement_map = {
    'Gemerská Poloma': {'Suľovská': 'Súlovská'},  # http://www.gemerskapoloma.sk/samosprava-1/obecne-zastupitelstvo/prijimanie-podnetov-obcanov/?ftresult=s%C3%BA%C4%BEovsk%C3%A1
    'Hlohovec': {'Sereďská': 'Seredská'},  # http://mesto.hlohovec.sk/download_file_f.php?id=865936
    'Jelka': {'Vŕbová': 'Vrbová'},  # http://www.jelka.sk/webimages/file/zverejnovanie/obec_faktury/2013_115.pdf
    'Piešťany': {'Žilinská': 'Žilinská cesta'},  # emailova odpoved od mesta Piestany
    'Topoľčany': {'Tríbečská': 'Tribečská',  # http://www.topolcany.sk/download_file_f.php?id=899672
                  'Pod kalváriou': 'Pod Kalváriou'},  # https://jazykovaporadna.sme.sk/q/7955/
    'Veľké Kapušany': {'Centrum II': 'Centrum II.'},  # web obce
    'Zavar': {'Hlinická': 'Hlinícka'},

    }


if __name__ == "__main__":
    sys.exit()
