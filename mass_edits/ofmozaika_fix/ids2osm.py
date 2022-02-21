#!/usr/bin/env python
'''
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

'''
from collections import defaultdict
from glob import glob
import xml.etree.ElementTree as ET
import bz2
import logging
import csv
import os
import overpass
import re
import requests
import subprocess
import sys

overpass_api = overpass.API(endpoint='https://overpass.freemap.sk/api/interpreter', timeout=600)
to_replace = ("ofmozaika|ofmozaka|ofmozajka|ofmozika|Ortofotomazaika SR|"
              "Orthopho.o mosaic Slovakia|"
              "orto\s*-?\s*zbgis®?( *, úrad geodézie, kartografie a katastra slovenskej republiky)?|ortozbgis|zbgis\s*orto|zbis ortofoto|zbgis-orto")
affected_users = ('aceman444', 'Durko_freemap', 'synalik', 'laznik')
input_file = 'ids.txt'

export_dir = 'exports'
chunk_size = 5000

element_type_map = {'0': 'node', '1': 'way', '2': 'relation'}


def chunks(l, n):
    n = max(1, n)
    l = list(l)
    return (l[i:i+n] for i in range(0, len(l), n))


def get_data(ids, element_type='node'):
    '''get xml data from overpass for ids (list) of a given element_type (node/way/relation'''
    query = '('
    query += ';'.join(['''{}({}) '''.format(element_type, x) for x in ids])
    query += ';)'
    result = overpass_api.Get(query, responseformat='xml', verbosity='meta')
    return result


def get_files_from_overpass():
    tainted = {}
    tainted['node'] = set()
    tainted['way'] = set()
    tainted['relation'] = set()
    logging.info('Reading {}'.format(input_file))
    with open(input_file) as f:
        while True:
            line = f.readline()
            if not line: break
            line = line.strip()
            tainted_flag, element_id, lat, lon, user, element_type, version, source = line.split('\t')
            element_type = element_type_map[element_type]
            # ids[element_type].append(element_id)
            ids[element_type].update([element_id])
            if int(tainted_flag) == 1:
                tainted[element_type].update([int(element_id)])

    logging.info('Getting latest data via overpass and writing in batches of {}'.format(chunk_size))
    for element_type in ids.keys():
        for i, chunk in enumerate(chunks(ids[element_type], chunk_size),
                                  start=1):
            with open(os.path.join(export_dir, '{}_{}.osm'.format(element_type, i)), 'w') as f:
                f.write(get_data(chunk, element_type))
    return tainted

def modify_tags(tainted):
    '''
    change source value (replace with "Ortofotomozaika SR")

     returns old_new dictionary containing
        key set to original_value (e. g. ofmozaika)
        value set to a list of
          - new_value (e. g. "Ortofotomozaika SR")
          - number of replacements
          - list of all users who recently modified the element
    '''
    old_new = defaultdict(lambda: [0, 0, list()])
    for filename in glob('exports/*.osm'):
        logging.info('opening {}'.format(filename))
        xml_tree = ET.parse(filename)
        root_element = xml_tree.getroot()
        for element in list(root_element):
            if element.tag in ('note', 'meta'): continue
            source_tag = element.find('tag[@k="source"]')
            element_id = int(element.get('id'))
            if source_tag is None:
                logging.info('{} id {} deleted (or source tag gone)'.format(element.tag,
                                                                            element_id))
                # we don't need this in our changeset
                root_element.remove(element)
                continue
            user = element.get('user')
            source_val = source_tag.get('v')
            new_source_val = source_val

            new_source_val = re.sub(to_replace, 'Ortofotomozaika SR', new_source_val, flags=re.I)

            # only replace zbgis in tainted objects
            if element_id in tainted[element.tag]:
                new_source_val = re.sub(r'zbgis(ws|\.skgeodesy\.sk|®(, Úrad geodézie, kartografie a katastra Slovenskej republiky)?)?', 'Ortofotomozaika SR', new_source_val, flags=re.I)

            # fix typo
            new_source_val = new_source_val.replace('survey, GPS, Ortofotomozaika SRGPS,', 'survey, GPS, Ortofotomozaika SR')
            if source_val == new_source_val:
                logging.info('source {} did not change ({}: {}, latest modification by {})'.format(source_val,
                                                                                                   element.tag,
                                                                                                   element_id,
                                                                                                   user))
            else:
                element.attrib['action'] = "modify"
                source_tag.set('v', new_source_val)
                old_new[source_val] = (new_source_val, old_new[source_val][1]+1, old_new[source_val][2] + [user])
        xml_tree.write('{}_new.osm'.format(filename), encoding='UTF-8')
    return old_new


def create_spreadsheet(old_new):
    with open('will_be_replaced.csv', 'w') as f:
        for orig_value in old_new:
            all_users = set(sorted(old_new[orig_value][2]))
            used_count = old_new[orig_value][1]
            compressed_users = []
            for user in sorted(list(all_users)):
                compressed_users.append('{}x {}'.format(old_new[orig_value][2].count(user), user))
            compressed_users = '; '.join(compressed_users)
            writer = csv.writer(f, ('orig', 'new'))
            writer.writerow([orig_value, old_new[orig_value][0], compressed_users, used_count])

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    ids = defaultdict(set)

    if not os.path.exists(export_dir):
        os.mkdir(export_dir)

    tainted = get_files_from_overpass()
    old_new = modify_tags(tainted)
    create_spreadsheet(old_new)
