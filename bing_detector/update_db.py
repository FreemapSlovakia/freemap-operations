#!/usr/bin/env python3
'''
update_db.py
'''

from shapely.geometry import Point, Polygon, box
from collections import defaultdict
import xml.etree.ElementTree as ET
import argparse
import datetime
import fiona
import configparser
import sys
import sqlite3
import bs4
import logging
import requests
import os.path

# slovakia bounding box (approximate)
bbox = '16.7980957,47.6875792,22.6208496,49.6320619'
cursor_file = 'latest_changeset.txt'
db_file = 'bing_detector.db'

currdir = os.path.dirname(sys.argv[0])
os.chdir(currdir)

cookies = {}

def initialize_db():
    logging.info('Initializing empty database..')
    cur.execute('''
        CREATE TABLE "changesets" (
         	"changeset_id"	INTEGER,
         	"user"	TEXT,
         	"created_at"	TEXT,
         	"message_sent"	INTEGER,
         	PRIMARY KEY("changeset_id") );
                ''')
    cur.execute('''
        CREATE TABLE "sent_messages" (
         	"user"	TEXT,
         	"last_message_sent_when"	INTEGER,
         	PRIMARY KEY("user") );
                ''')
                

def get_property(element, match_string, key='v'):
    match = element.find(match_string)
    return match.get(key) if match is not None else match

parser = argparse.ArgumentParser(description='Send notification to user if iD editor was used without Ortofotomozaika imagery') 
parser.add_argument('-d',
                    help='debug mode',
                    action='store_true',
                    dest='debug')

parser.add_argument('-t',
                    nargs=1,
                    help='look at changesets from this date (YYYY-MM-DD)',
                    dest='date')

options = parser.parse_args()

if options.debug:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

if os.path.exists(cursor_file):
    with open('latest_changeset.txt') as f:
        cursor = int(f.read())
else:
    cursor = 0

if not os.path.exists(db_file):
    con = sqlite3.connect(db_file, timeout=120)
    cur = con.cursor()
    initialize_db()
else:
    con = sqlite3.connect(db_file)
    cur = con.cursor()

print(f'# Only changesets with id > {cursor} will be parsed')
slovakia = fiona.open('slovakia.geojson', 'r')
slovakia = Polygon(*slovakia[0]['geometry']['coordinates'])

if options.date:
    start_date = options.date[0]
    end_date = (datetime.datetime.strptime(start_date, '%Y-%m-%d') + datetime.timedelta(days=1))
    end_date = end_date.strftime('%Y-%m-%d')
    r = requests.get(f'https://api.openstreetmap.org/api/0.6/changesets?bbox={bbox}&time={start_date},{end_date}')
else:
    r = requests.get(f'https://api.openstreetmap.org/api/0.6/changesets?bbox={bbox}')

user_badchangesets = defaultdict(list)

for changeset in ET.fromstring(r.text).findall('changeset'):
    changeset_id = int(changeset.get('id'))
    user = changeset.get('user')
    created_at = changeset.get('created_at')
    created_by = get_property(changeset, 'tag[@k="created_by"]')
    imagery_used = get_property(changeset, 'tag[@k="imagery_used"]')
    bounding_box = box(*[float(changeset.get(x)) for x in ('min_lon', 'min_lat', 'max_lon', 'max_lat')])

    # did we already look at this changeset?
    if changeset_id <= cursor:
        logging.debug(f'Changeset ID {changeset_id} >= cursor ({cursor}) - ignoring')
        continue
    # are we within Slovakia borders?
    if not bounding_box.within(slovakia):
        logging.debug(f'Changeset ID {changeset_id} not within Slovakia borders - ignoring')
        continue
    # has iD editor been used?
    if not created_by or not created_by.startswith('iD'):
        logging.debug(f'Created_by={created_by} - ignoring')
        continue
    # is Ortofotomozaika SR among used imagery?
    if 'Ortofotomozaika SR' in imagery_used:
        logging.debug(f'Ortofotomozaika SR in imagery_used - ignoring')
        continue
    # was Mapbox Satellite or Bing aerial imagery used as imagery?
    if 'Mapbox Satellite' not in imagery_used and 'Bing aerial imagery' not in imagery_used:
        logging.debug(f'Neither Mapbox Satellite nor Bing aerial imagery used in sources - ignoring')
        continue

    user_badchangesets[user].append(changeset_id)
    cur.execute('INSERT OR IGNORE INTO changesets VALUES (?, ?, ?, 0)', (changeset_id, user, created_at))
    print(changeset_id, user, created_by, imagery_used)

# write cursor so that we won't process the same changeset twice
latest_changeset = ET.fromstring(r.text).find('changeset').get('id')
with open('latest_changeset.txt', 'w') as f:
    f.write(latest_changeset)

con.commit()
