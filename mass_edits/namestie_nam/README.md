# Expanzia Nám./nám. na cestách a adresných bodoch

- zmena názvov ulíc a adresných bodov dohodnutá v rámci OSM komunity
- skratka "nám." alebo "Nám." sa nahrádza reťazcom "námestie", resp. "Námestie"
- týka sa tagov name ulíc (`way`, `highway=*`) a tagov `addr:street`
- na prípravu dát na import bol použitý skript `namestie.py`
- import bol realizovaný pod účtom [freemap-operations](https://www.openstreetmap.org/user/freemap-operations)
- diskusia v skupine osm_sk: https://groups.google.com/g/osm_sk/c/fDTgUgD_bJ0/m/8qGFa3BUAwAJ?pli=1

Overpass query (záber):

```
[out:json][timeout:1800];

(
  // adresne body/uzly
  node["addr:street"~"[nN]ám\\."](area:3600014296);
  // ulice
  way[highway]["name"~"[nN]ám\\."](area:3600014296);
  // adresy na budovach
  way["addr:street"~"[nN]ám\\."](area:3600014296);
  // adresy na relaciach
  relation["addr:street"~"[nN]ám\\."](area:3600014296);
);

out body;
>;
out skel qt;
```

## História

Vo februári 2021 bol urobený úvodný import. Vo februári 2022 upozornil používateľ [aceman444](https://www.openstreetmap.org/user/aceman444) na fakt, že do rozsahu zmien neboli zahrnuté elementy `addr:street` na prvkoch typu `way` a `relation`. Toto bolo o pár týždňov neskôr opravené.
