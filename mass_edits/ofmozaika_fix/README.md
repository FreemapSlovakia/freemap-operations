# Nahradenie source=ofmozaika/zbgis (a ich variánt) source=Ortofotomozaika SR

Vzhľadom na fakt, že niektorí mapperi miesto "Ortofotomozaika SR" používali v source reťazec "zbgis" bola zmena závislá aj od používateľa.

Upozornenie! Tento import bol jednorazovou záležitosťou a nie je určený na opakované použitie. Skripty a postupy tu uvedené slúžia iba ako referencia!

## Postup

- stiahnuť úplnú históriu všetkých OSM objektov z https://osm-internal.download.geofabrik.de/europe.htm a uložiť ako `slovakia-latest-internal.osm.pbf`
- spustiť `filter.pl`, ktorý vygeneruje niekoľko `.txt` súborov v aktuálnom adresári
- vyčistiť adresár `exports/`
- spustiť `ids2osm.py`, čím sa vygenerujú `osm_new` súbory v adresári `exports/` - changesety sú automaticky rozdelené po 5000 elementoch
- nahrať pod dedikovaným používateľom

## Poznámka

- pôvodne napísaný skript `ofmozaika_fix.py` nakoniec nebol použitý. nerozlišuje totiž medzi tým, kto daný element editoval, čo bolo potrebné na to, aby sa dalo s určitosťou povedať, či source=ZBGIS označoval v skutočnosti Ortofotomozaiku alebo iný zdroj (WMS vrstva).
- súvisiaca diskusia: https://groups.google.com/g/osm_sk/c/yt3CPftHtO8/m/WTjNJRUTAwAJ
