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
```

## Spustenie a syntax

```shell
import_address.py [-h] city

positional arguments:
  city        Mesto/obec, ktore/a sa ma spracovat

options:
  -h, --help  show this help message and exit
```

## Priklad

```shell
$ ./import_address.py Trnava
INFO:root:Spusta sa spracovanie obce/mesta Trnava..
INFO:root:Stahuju sa nove data z MINV, ak su k dispozicii..
INFO:root:Zistena potreba stahovania - ziskavam adresy.zip..
INFO:root:Nacitam hranice obci (ZSJ)..
INFO:root:Zostavujem polygon(y) pre Overpass query..
INFO:root:Ukladam povodne hranice obce do suboru..
INFO:root:Ukladam zjednodusene hranice obce do suboru..
..
..
INFO:root:Spajam s datami z OSM..
INFO:root:conflate -l "Trnava/Trnava_list.txt" -vi "Trnava/result_Trnava.geojson" "/tmp/importaddress/./profile" -o "Trnava/result_Trnava.osm" -c preview.json --osm "Trnava/source_Trnava.osm"
$ josm Trnava/result_Trnava.osm
# v JOSM: Ctrl-U na stiahnutie clenov ciest (bodov)
$ firefox Trnava/index.html
```

## Poznamka

Chybu "recevied corrupt data from Overpass" je mozne riesit tymto patchom: https://github.com/mvexel/overpass-api-python-wrapper/issues/135.
