# Expanzia Nám./nám. na cestách a adresných bodoch

- jednorazová zmena dohodnutá v rámci OSM komunity
- na prípravu dát na import bol použitý skript `namestie.py`
- import bol realizovaný pod účtom [freemap-operations](https://www.openstreetmap.org/user/freemap-operations)
- diskusia v skupine osm_sk: https://groups.google.com/g/osm_sk/c/fDTgUgD_bJ0/m/8qGFa3BUAwAJ?pli=1

Overpass query (záber):

```
[out:json][timeout:25];

(
  node["addr:housenumber"][~"name"~"[nN]ám\\."]({{bbox}});
  way[highway][~"name"~"[nN]ám\\."]({{bbox}});
);

out body;
>;
out skel qt;
```

