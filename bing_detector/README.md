Popis
-----


Skript na poslanie spravy pouzivatelovi, ak sa zisti, ze v nedavnom changesete(-och) pouzil na editaciu editor iD s podkladovou vrstvou Bing alebo MapBox bez kombinovania s Ortofotomozaikou.

Pouzivatel sa tak dozvie, ze Ortofotomozaika je zdroj kvalitativne lepsi ako vyssie spomenute dva. V sprave (spolu s kratkym sumarom v anglictine) je tiez uvedeny postup ako si Ortofotomozaiku do iD prida.

Suvisiaca issue na Githube:
[16](https://github.com/FreemapSlovakia/freemap-operations/issues/16)

Ako to funguje
--------------
Pomocou OSM API je stiahnuty bbox okolo Slovenska obsahujuci zoznam poslednych 100 changesetov (limit API). Tento sa dalej okrese o changesety v ramci uzemia hranic krajiny.

Zaujimaju nas changesety, ktore:

  - este skript nevidel  - priebezne si preto ukladame najvyssi changeset ID do `latest_changeset.txt`
  - boli vytvorene editorom iD (metadata changesetu)
  - vznikli pri pouziti podkladovej vrstvy Bing a/alebo MapBox (metadata changesetu)
  - nepouzili podkladovu vrstvu Ortofotomozaika SR (metadata changesetu)

Changesety, ktore vyhovuju vsetkym podmienkam vyssie su ulozene do sqliteDB `bing_detector.db` spolu s datumom vzniku a autorom. DB subor potom precita dalsi skript a odosle spravy jednotlivym pouzivatelom.

Text spravy (spolu s udajmi prihlasenia) je definovany v subore `.bing_detector`.

Skript cita a zapisuje z/do tychto suborov:

  - `.bing_detector` (r) - obsahuje informacie o pouzivatelovi, ktory odosiela spravu a jej text

  - `slovakia.geojson` (r) - obsahuje polygon hranic Slovenska pouzity pri zistovani, ci sa bounding box changesetu cely nachadza na uzemi SR

  - `latest_changeset.txt` (rw) - obsahuje cislo posledneho spracovavaneho changesetu. kedze toto cislo nemoze klesat, pouzivame ho na zistenie,
                             ci uz v minulosti bol ten-ktory changeset spracovavany

  - `bing_detector.db` (rw) - Sqlite DB, ktora obsahuje 2 tabulky:
    - `changesets` - informacie o vsetkych changesetoch vyhovujucich definovanemu filtru spolu s informaciou, ci bola pre dany changeset odoslana jeho autorovi sprava
    - `sent_messages` - tabulka pouzivatelov spolu s informaciou, kedy im bola odoslana posledna sprava

Spustenie
---------
Skript je napisany v Pythone a vyzaduje instalaciu niekolkych modulov.

V Debiane to zabezpeci prikaz:
```
  sudo apt install python3-shapely python3-fiona python3-requests
```

V Arch Linuxe:
```
  sudo pacman -Sy python-shapely python-fiona python-requests
```

Spustenie sa sklada z dvoch casti:

  - `update_db.py`
    Stahuje z OSM API zoznam changesetov a filtruje ich podla popisanych pravidiel. Changesety, ktore prejdu filtrom su ulozene do DB.

  - `send_message.py`
    Otvori DB s changesetmi a autorom tych, ktorym este nebola poslana sprava odosle prostrednictvom OSM spravu s informaciou o Ortofotomozaike. Nasledne aktualizuje v DB informaciu o tom, ze sprava tykajuca sa konkretneho changesetu uz bola odoslana.

    Pouzivatelovi je odoslana sprava iba vtedy, ak od poslednej spravy uplynulo aspon 10 dni (premenna `days_rest` v subore `send_message.py`.

    Pre ucely testovania sa odporuca pouzivat prepinac `-n`, kedy nedojde k odoslaniu spravy, iba k jej vypisani na standardny vystup.u

Oba skripty je mozne spustat nezavisle, no nakolko pri zmene sqliteDB dochadza k jej zamykaniu je vhodne naplanovat *spustanie v roznych casoch*.


Priklad spustenia
-----------------
```
rm latest_changeset.txt
./update_db.py -t 2021-01-02
./send_message.py -n
```

Priklad nasadenia
-----------------
- v subore `.bingdetector` uviest platne meno pouzivatela a heslo
- odstranit subor `latest_changeset.txt`
- spustat plnenie db cez crontab kazdych 30 minut

    ```
    0,30 * * * * /cesta/ku/update_db.py
    ```

- nastavit odosielanie sprav raz denne (o 9:15)

    ```
    15 9 * * * /cesta/ku/send_message.py
    ```

Naplnenia databazy pre ucely testovania
---------------------------------------
```
# databazu naplnime udajmi z changesetov od zaciatku roka 2021 do 4. augusta 2021
mv bing_detector.db{,.bk}
rm latest_changeset.txt
for i in $(seq 0 215); do ./update_db.py -t $(date '+%Y-%m-%d' -d "2021-01-01 + $i days"); done
# zobrazenie prefiltrovanych changesetov
sqlite3 bing_detector.db 'select * from changesets'
```

Podakovanie
-----------
* \*Martin\* za mentoring a tipy
* Peto Vojtek, Sano Zatko - review a napady
* Tibor - nasadenie na Freemap server

Zname problemy a obmedzenia
---------------------------
- OSM API umoznuje stiahnut najviac 100 poslednych changesetov. Preto je potrebne zabezpecit, aby `update_db.py` skript bezal relativne casto a ziadne changesety tak neboli preskocene.
- je mozne, ze existuju dovody, preco by pouzivatel mohol chciet pouzit Bing/MapBox miesto Ortofotomozaiky a posielanie spravy je tak zbytocne a obtazujuce. Ak sa toto v buducnosti preukaze, bude vhodne zvazit napr. spracovanie tagu #bing v komentari changesetu, ktorym by sa oznacovali changesety, pre ktore by sprava nebola odosielana

Myslienky do buducna
--------------------
- zoznam ignorovanych pouzivatelov?
- pouzit locale v metadatach na poslanie spravy v zodpovedajucom jazyku?

Historia
---------
* 2021, 18. maj - zalozenie GH issue #16 (\*Martin\*)
* 2021, 2. august - predstavenie uvodnej verzie skriptu clenom OZ Freemap (jose)
* 2021, 8. august - 0.1 - prva verejna verzia skriptu (jose)
* 2021, 10. august - nasadenie skriptu na Freemap server (Tibor)
