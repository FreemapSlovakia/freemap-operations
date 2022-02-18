#!/usr/bin/env python
'''
Hromadna zmena adresnych bodov a ciest z "Nam." na "Namestie". Zmena sa tyka:
  - uzlov s tagom addr:housenumber a tagom addr:street obsahujucim hodnotu "nám."
  - ciest s tagom highway a tagom name obsahujucim "nám."

Vyzaduje overpass python modul.

Postup:
  - spustit skript bez parametrov
  - otvorit modified.osm v JOSM a skontrolovat
  - upload ako freemap-operations user

'''
import xml.etree.ElementTree as ET
from io import BytesIO
from overpass import API

# stiahne uzly a cesty z overpass
api = API(timeout=1800)
query = '''
(
  // adresne body/uzly
  node["addr:street"~"[nN]ám\\\."](area:{rel});
  // ulice
  way[highway]["name"~"[nN]ám\\\."](area:{rel});
  // adresy na budovach
  way["addr:street"~"[nN]ám\\\."](area:{rel});
  // adresy na relaciach
  relation["addr:street"~"[nN]ám\\\."](area:{rel});
);'''
query = query.format(rel=3600014296)

data = api.get(query=query, verbosity='meta', responseformat='xml')

xml_tree = ET.parse(BytesIO(data.encode('utf-8')))
root_element = xml_tree.getroot()
name_tag = None
altname_tag = {}
longname_tag = {}
for element in list(root_element):
    # preskoci neuzitocne elementy
    if element.tag in ('note', 'meta'): continue
    name_tag = altname_tag = longname_tag = None

    # adresa (addr:street) ako uzol
    if element.tag == 'node':
        name_tag = element.find('tag[@k="addr:street"]')
    # adresa (addr:street) na budove
    elif element.tag == 'way' and isinstance(element.find('tag[@k="addr:street"]'), ET.Element):
        name_tag = element.find('tag[@k="addr:street"]')
    # ulica s nazvom (name)
    elif element.tag == 'way':
        name_tag = element.find('tag[@k="name"]')
        altname_tag = element.find('tag[@k="alt_name"]')
        longname_tag = element.find('tag[@k="long_name"]')
    # adresa ako relacia
    elif element.tag == 'relation':
        name_tag = element.find('tag[@k="addr:street"]')

    # prida priznak action=modify
    element.attrib['action'] = 'modify'

    # rozbali nam/Nam na namestie/Namestie
    name_tag.set('v', name_tag.get('v').replace('nám.', 'námestie'))
    name_tag.set('v', name_tag.get('v').replace('Nám.', 'Námestie'))

    if altname_tag is not None and name_tag.get('v') == altname_tag.get('v'):
        print('Odstranujem altname kedze je rovnaky ako name po rozbaleni')
        element.remove(altname_tag)

    if longname_tag is not None and name_tag.get('v') == longname_tag.get('v'):
        print('Odstranujem longname kedze je rovnaky ako name po rozbaleni')
        element.remove(longname_tag)

with open('original.osm', 'w') as f:
    f.write(data)
xml_tree.write('modified.osm', encoding='UTF-8')

print('Povodny .osm subor najdete v original.osm, subor so zmenami je modified.osm')
