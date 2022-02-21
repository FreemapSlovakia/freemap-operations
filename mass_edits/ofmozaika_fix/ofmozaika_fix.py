#!/usr/bin/env python
'''
[ OBSOLETE - this was an original approach but has not been used ]

 get all elements tagged source=*ofmozaika*/zbgis orto (or similar) from freemap overpass and 
 replace matched string with "Ortofotomozaika SR", store result to .osm files in export/

  - first Slovakia dump is pulled from geofabrik
  - source tags are being filtered from dump and put into two files:
      will_be_replaced.csv - source tag to be modified + how
      wont_be_replaced.csv - source tag won't be touched (ignored)
  - then district (okres) boundaries (relation ids) are pulled from overpass api
  - district-by-district query for source matching regular expression is run towards overpass
    api and source tag key is replaced by a desired value
  - output is stored in exports/ directory (one file per district, no file if overpass returned empty dataset)

[ OBSOLETE - this was an original approach but has not been used ]

'''
from collections import defaultdict
import bz2
import logging
import csv
import os
import osmapi
import overpass
import re
import requests
import subprocess
import sys

overpass_api = overpass.API(endpoint='https://overpass.freemap.sk/api/interpreter', timeout=600)
source_re = r'\s*<tag k="source" v="([^"]*)"'
to_replace = ("ofmozaika|ofmozaka|ofmozajka|ofmozika|Ortofotomazaika SR|"
              "Orthopho.o mosaic Slovakia|"
              "orto\s*-?\s*zbgis®?( *, úrad geodézie, kartografie a katastra slovenskej republiky)?|ortozbgis|zbgis\s*orto|zbis ortofoto|zbgis-orto")
export_dir = 'exports'

def get_slovakia_dump():
    print('Downloading Slovakia dump from Geofabrik..', end='')
    r = requests.get('https://download.geofabrik.de/europe/slovakia-latest.osm.bz2')
    with open('slovakia-latest.osm.bz2', 'wb') as f:
        f.write(r.content)
    print('OK')

def parse_slovakia_dump():
    print('Parsing Slovakia dump..')
    will_be_replaced = dict()
    wont_be_replaced = set()

    bz2file = bz2.BZ2File('slovakia-latest.osm.bz2')
    while True:
        line = bz2file.readline()
        if not line:
            break
        line = line.decode('utf-8')
        match = re.match(source_re, line)
        if match:
            source = match.group(1)
            if re.search(to_replace, source, re.I):
                new = re.sub(r'({})'.format(to_replace), 'Ortofotomozaika SR', source, flags=re.I)
                will_be_replaced[source] = new
            else:
                wont_be_replaced.update([source])

    with open('will_be_replaced.csv', 'w') as f:
        writer = csv.writer(f, ('orig', 'new'))
        writer.writerows(will_be_replaced.items())

    with open('wont_be_replaced.csv', 'w') as f:
        f.write('\n'.join(list(wont_be_replaced)))

def get_data(relation_id):
    '''get xml data (elements with source=*ofmozaika*) from overpass for given relation_id (okres)''' 
    query = '''area(36{:08d});
    (  ._; )->.boundaryarea;
    nwr [source ~ "({})", i][source !~ "Ortofotomozaika SR"](area.boundaryarea) ->.ofmozaika;
    ( .ofmozaika;
    );'''.format(int(relation_id), to_replace)
    logging.debug(query)
    result = overpass_api.Get(query, responseformat='xml', verbosity='meta')
    if len(result) < 300: return None
    return result

def get_okresy():
    print('Getting okres boundaries..', end='')
    query = '''relation["admin_level"~"8"]["boundary"~"administrative"]["name"~"okres"];'''
    print('Done')
    result = overpass_api.Get(query, responseformat='csv(::"id", "name")')
    okresy = {}
    for r in result.split('\n')[1:-1]:
        okres_id, okres_name = r.split('\t')
        okresy[okres_id] = okres_name

    # sort okresy by name
    okresy = {k: v for k, v in sorted(okresy.items(), key=lambda n: n[1])}
    return okresy

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # get_slovakia_dump()
    # parse_slovakia_dump()
    # sys.exit()

    if not os.path.exists(export_dir):
        os.mkdir(export_dir)

    okresy = get_okresy()
    # we have 79 district in Slovakia
    assert len(okresy) == 79

    for i, okres in enumerate(okresy, start=1):
        print('Processing {} - {} ({})..'.format(i, okresy[okres], okres), end='')
        data = get_data(okres)
        if data: 
            data_to_write = []
            for line in data.splitlines():
                if re.match(r'\s*<(node|way|relation) id', line):
                    line = re.sub(r'>$', ' action="modify">', line)
                if re.search(source_re, line):
                    line = re.sub(r'({})'.format(to_replace), 'Ortofotomozaika SR', line, flags=re.I)
                data_to_write.append(line)
            with open('{}/{}.osm'.format(export_dir, okresy[okres]), 'w') as f:
                f.write('\n'.join(data_to_write))
            print('OK')
        else:
            print('No data')
