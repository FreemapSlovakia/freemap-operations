#!/usr/bin/env python3
'''
send_message.py
'''
import argparse
import datetime
import configparser
import sys
import sqlite3
import bs4
import logging
import requests
import os.path

db_file = 'bing_detector.db'

currdir = os.path.dirname(sys.argv[0])
os.chdir(currdir)

# only send message to user if the last message was sent N or more days ago
days_rest = 10

cookies = {}

def osm_auth():
    global cookies
    logging.debug('Authenticating..')
    r = requests.get('https://www.openstreetmap.org/')
    cookies = r.cookies
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    token = soup.find('meta', attrs={'name': 'csrf-token'})['content']

    data = {'username': senderlogin,
            'password': senderpass,
            'authenticity_token': token
            }
    r = requests.post('https://www.openstreetmap.org/login',
                      data=data, cookies=cookies)
    logging.debug('OSM cookies: %s' % cookies)
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    token = soup.find('meta', attrs={'name': 'csrf-token'})['content']
    if token:
        return token
    else:
        raise Exception("token could not be obtained")


def osm_send(token, subject, message, rcpt):
    global cookies
    data = {'authenticity_token': token,
            'message[title]': subject,
            'display_name': rcpt,
            'message[body]': message,
            'commit': 'Odoslať'
            }
    r = requests.post('https://www.openstreetmap.org/messages',
                      data=data, cookies=cookies)
    r.raise_for_status()

parser = argparse.ArgumentParser(description='Send notification to user if iD editor was used without Ortofotomozaika imagery') 
parser.add_argument('-d',
                    help='debug mode',
                    action='store_true',
                    dest='debug')

parser.add_argument('-n',
                    help='do not send message',
                    action='store_true',
                    dest='no_message')

options = parser.parse_args()

if options.debug:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

config = configparser.RawConfigParser()
config.read(os.path.join(currdir, '.bing_detector'))

senderlogin = config.get('Auth', 'username')
senderpass = config.get('Auth', 'password')
message_template = config.get('Messages', 'message')

token = osm_auth()
logging.debug('OSM token is %s' % token)

con = sqlite3.connect(db_file, timeout=120)
cur = con.cursor()

for changesets, user, message_sent, last_message_sent_when, message_sent_days_ago \
   in cur.execute('''SELECT COUNT(changeset_id) AS changesets_count,
                            changesets.user,
                            message_sent,
                            datetime(last_message_sent_when) AS last_message_sent_when,
                            CAST(julianday('now') - julianday(last_message_sent_when) AS INTEGER) AS message_sent_days_ago
                      from changesets LEFT OUTER JOIN sent_messages
                      ON changesets.user == sent_messages.user
                      WHERE message_sent = 0 AND ( (julianday('now') - julianday(last_message_sent_when)) > :days OR (last_message_sent_when IS NULL))
                      GROUP BY changesets.user
                      ;''', {'days': days_rest}).fetchall():

    logging.info(f'Sending message to user {user}, found {changesets} matching changesets')
    message = message_template.replace('%', ' ').replace('<nick>', user)
    if options.no_message:
        print(message)
    else:
        osm_send(token, 'Ortofotomozaika SR', message, user)
        cur.execute('''UPDATE changesets SET message_sent = 1 WHERE user == ? AND message_sent == 0''', (user,))
        cur.execute('''INSERT OR REPLACE INTO sent_messages VALUES ( ?, julianday('now') ) ''', (user,))
        con.commit()
