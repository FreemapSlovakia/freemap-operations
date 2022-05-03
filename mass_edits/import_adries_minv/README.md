# import address

Spajanie adries z MINV a OSM (`conflate`).

## Instalacia a priprava prostredia

Na spustenie je potrebna funkcna instalacia Pythonu 3 a virtualenv - idealne v najnovsej verzii.

```shell
virtualenv import_adries
source import_adries/bin/activate
git clone https://github.com/FreemapSlovakia/freemap-operations.git
cd freemap-operations/mass_edits/import_adries_minv
pip install -r requirements.txt
mv config.yaml.example config.yaml
# edit config.yaml
```

## Spustenie a syntax

```shell
import_address.py [-h] citycode

positional arguments:
  citycode    Kod mesta/obca, ktore/a sa ma spracovat

options:
  -h, --help  show this help message and exit
```

## Priklad

```shell
./import_address.py SK0101528595
INFO:root:Spusta sa spracovanie obce/mesta SK0101528595..
INFO:root:Stahuju sa nove data z MINV, ak su k dispozicii..
INFO:root:Nacitam hranice obci (ZSJ)..
INFO:root:Zostavujem polygon(y) pre Overpass query..
INFO:root:Ukladam povodne hranice obce do suboru..
INFO:root:Ukladam zjednodusene hranice obce do suboru..
..
INFO:root:Nacitam .csv subor Adresy_2022-04-17.csv..
INFO:root:Konvertujem do GeoDataFrame..
INFO:root:Normalizujem nazvy ulic napriec datasetom..
INFO:root:Normalizujem nazvy ulic v ramci jednotlivych obci..
INFO:root:Zistujem priemernu a max. vzdialenost bodov v ramci jednej adresy
..
INFO:root:Kontrolujem spravnost adries..
INFO:root:Zistujem adresy bez lokacie..
INFO:root:Zistujem adresy s rovnakou lokaciou..
INFO:root:Orezavam body podla hranic obce
INFO:root:Orezanych 0 adresnych bodov
INFO:root:Stahujem budovy v ramci hranic obce ..
INFO:root:Stahujem adresne body v ramci hranic obce ..
INFO:root:Robim prienik budov a adresnych bodov a pridavam pomocny tag (dont_tag_buildings2=true/false)
..
INFO:root:Zapísané do SK0101528595/source_SK0101528595.geojson
INFO:root:Hladam adresne body mimo budov..
INFO:root:Spajam s datami z OSM..
INFO:root:conflate -l "SK0101528595/SK0101528595_list.txt" -vi "SK0101528595/result_SK0101528595.geojson" "/home/jose1711/freemap-operations/mass_edits/import_adries_minv/./profile" -o "SK0101528595/result_SK0101528595.osm" -c preview.json --osm "SK0101528595/source_SK0101528595.osm"
$ josm Trnava/result_Trnava.osm
# v JOSM: Ctrl-U na stiahnutie clenov ciest (bodov)
$ firefox Trnava/index.html
```

## Poznamka

Chybu "recevied corrupt data from Overpass" je mozne riesit tymto patchom: https://github.com/mvexel/overpass-api-python-wrapper/issues/135.
