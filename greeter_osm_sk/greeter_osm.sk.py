#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
greeter_osmsk.py 0.8
 skript, ktory sleduje newusers rss feed a ked objavi
 novacika editujuceho slovensko, posle mu uvitaciu spravu

historia
 0.1 - prvy "release"
 0.2 - doplneny link - definicia changesetu
     - odkaz na uvodne stranky pre zaciatocnikov
 0.3 - moznost poslat jednorazovu spravu vybranemu uzivatelovi (specifikovanemu
       ako prvy argument skriptu)
 0.4 - skript prepisany do pythonu bez zavislosti na rsstail
     - oddeleny kod a konfiguracia (.greeterrc)
 0.5 - pridana moznost logovania do suboru (prepinac -l)
     - upraveny sposob autentizacie
 0.6 - PEP8
     - neposielaj spravu o chybajucom source tagu pre changeset ak bol pouzity
       editor iD
 0.7 - oprava posielania po zmene URL na osm
 0.8 - osm auth/send: vymena beautifulsoup + requests za mechanize (po vzore https://github.com/osmcz/greeter-osm)
       oprava deprecation warnings (bs4)

"""

import argparse
import bs4
import configparser
import logging
import mechanize
import os
import requests
import sys
import urllib

rssurl = 'http://resultmaps.neis-one.org/newestosmcountryfeed.php?c=Slovakia'

parser = argparse.ArgumentParser(description='send OSM welcome message to '
                                 'a user with the first changeset '
                                 'made in Slovakia')
parser.add_argument('-d',
                    help='debug mode',
                    action='store_true',
                    dest='debug')
parser.add_argument('-l',
                    metavar='logfile',
                    help='log to file (implies -d)',
                    nargs=1,
                    type=str)
parser.add_argument('-n',
                    help='do NOT send the actual message',
                    action='store_true',
                    dest='nosend')
parser.add_argument('-u',
                    metavar='user',
                    help='send message to USER',
                    nargs=1,
                    type=str)
options = parser.parse_args()

if options.l:
    logging.basicConfig(level=logging.DEBUG, filename=options.l[0])
    logging.getLogger("requests").setLevel(logging.INFO)
elif options.debug:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.INFO)


def osm_auth():
    logging.debug('Authenticating..')
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    browser.addheaders = [('User-agent', 'https://github.com/FreemapSlovakia/freemap-operations/tree/master/greeter_osm_sk')]
    browser.open("https://www.openstreetmap.org/login/")
    browser.select_form(id="login_form")
    browser["username"] = senderlogin
    browser["password"] = senderpass
    browser.submit()
    return browser

def osm_send(browser, subject, message, rcpt):
    logging.debug(f'Sending {subject}: {message}\n to {rcpt}')
    browser.open(f"https://www.openstreetmap.org/messages/new/{rcpt}")
    browser.select_form(id="new_message")
    browser["message[title]"] = subject
    browser["message[body]"] = message
    browser.submit()

config = configparser.RawConfigParser()
currdir = os.path.dirname(sys.argv[0])
config.read(os.path.join(currdir, '.greeterrc'))

os.chdir(currdir)

senderlogin = config.get('Auth', 'username')
senderpass = config.get('Auth', 'password')

browser = osm_auth()

if not options.u:
    r = requests.get(rssurl)
    r.raise_for_status()
    if r.status_code != 200:
        raise Exception('Error getting %s' % rssurl)
    soup = bs4.BeautifulSoup(r.text, 'xml')
    userurls = [x.get_text() for x in soup.find_all('id')]
    userurls = [x for x in userurls if x.startswith('https://')]
    userurls.reverse()
    statusfile = config.get('Files', 'statusfile')
    logging.debug('Status file: %s' % statusfile)

    try:
        lastsent = open(statusfile, encoding='utf-8').read().strip()
    except IOError:
        lastsent = ''

    try:
        ind = userurls.index(lastsent)
    except ValueError:
        ind = 0

    logging.debug('we left off at %s' % lastsent)
else:
    # user may give already encoded value, try to guess it
    # not bulletproof, see https://stackoverflow.com/questions/2295223/how-to-find-out-if-string-has-already-been-url-encoded
    param = options.u[0]
    param_dec = urllib.parse.unquote(param)
    if (param == param_dec): # not encoded
        param = urllib.parse.quote(param)
    userurls = ['xxx/%s' % param]
    ind = -1

mainmessage = config.get('Messages', 'mainmessage')
nosourcemessage = config.get('Messages', 'nosourcemessage')
nocommentmessage = config.get('Messages', 'nocommentmessage')
ideditormessage = config.get('Messages', 'ideditormessage')

for user in userurls[ind+1:]:
    rcpt_quoted = user.split('/')[-1]
    rcpt = urllib.parse.unquote(rcpt_quoted)

    message = mainmessage.replace('%', ' ').replace('<nick>', rcpt)

    r = requests.get('https://www.openstreetmap.org/user/%s/history' % rcpt_quoted)
    if r.status_code == 404:
        logging.debug("User '%s' does not exist, probably was renamed in the meantime" % rcpt)
        continue

    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    changeset = soup.find_all('a')[0]['href']

    logging.debug("Last changeset id: %s" % changeset)

    r = requests.get('https://www.openstreetmap.org/api/0.6%s' % changeset)
    soup = bs4.BeautifulSoup(r.text, 'xml')

    tags = {k['k']: k['v'] for k in soup.find_all('tag')}
    logging.debug('changeset tags: %s' % tags)

    if not tags.get('source'):
        logging.debug('no source tag used for changeset')
        # only add text if user is not using iD
        if 'iD' not in tags.get('created_by'):
            message += '\n\n' + nosourcemessage

    if not tags.get('comment'):
        logging.debug('no comment tag used for changeset')
        message += '\n\n' + nocommentmessage

    if 'iD' in tags.get('created_by'):
        logging.debug('iD editor detected')
        message += '\n\n' + ideditormessage

    if not options.nosend:
        logging.debug('sending message to user %s' % rcpt)
        osm_send(browser, 'Privitanie', message, rcpt_quoted)
    else:
        logging.debug('NOT sending (because you said so) the message to user %s' % rcpt)
    if not options.u and not options.nosend:
        with open(statusfile, 'w', encoding='utf-8') as f:
            f.write(user)
