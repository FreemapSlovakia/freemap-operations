#!/usr/bin/env python3
from datetime import datetime
from glob import glob
from jinja2 import Environment, FileSystemLoader
from os import chdir, path, stat
import json
import locale
import re
import time
import unicodedata
import yaml

locale.setlocale(locale.LC_ALL, 'sk_SK.utf8')

with open('config.yaml') as f:
    config_data = yaml.safe_load(f)

webroot = config_data['webroot']

inputdir = webroot
outfile = path.join(inputdir, 'obce.json')
htmlout = path.join(inputdir, 'index2.html')
indexpage = path.join(inputdir, 'index.html')

env = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("index.html")
today = datetime.today().strftime('%c')
# január/február.. => ..a
today = re.sub(r'([rljn])\s', lambda n: f'{n.group(1)}a ', today, re.U)
# september/október/november => ..ra
today = re.sub('er\s', 'ra ', today, re.U)
# marec => ..ca
today = re.sub('ec\s', 'ca ', today, re.U)

data = list()
obce = list()

chdir(inputdir)
for obec in glob('*'):
    ascii_name = unicodedata.normalize('NFD', obec).encode('ascii', 'ignore').decode()
    filtered_csv = glob(path.join(obec, '*_filtered.csv'))
    if not filtered_csv: continue
    filtered_csv = filtered_csv[0]
    if not filtered_csv: continue
    with open(filtered_csv) as f:
        row = f.readline()
        row = f.readline()
    kraj, okres = row.split(',')[2:4]
    generated = time.strftime("%Y-%m-%d", time.localtime(stat(filtered_csv).st_mtime))
    print(obec, generated)

    index_html = glob(path.join(obec, 'index.html'))
    if not index_html: continue
    index_html = index_html[0]
    if not index_html: continue
    obce.append((obec, okres, kraj))
    if 'Prekrývajúce' in open(index_html).read():
        color = '#FF0000'
    else:
        color = '#00FF00'

    if ascii_name != obec:
        obec = f'{obec} ({ascii_name})'

    data.append({'Obec': obec,
        'Okres': okres,
        'Kraj': kraj,
        'Generované': generated,
        'Budovy': color,
        'Výsledok': 'JOSM',
        })

with open(htmlout, 'w') as f:
    f.write('<br>'.join([f'<a href="{obec}">{obec} ({okres}, {kraj})</a>' for obec, okres, kraj in sorted(obce)]))

with open(outfile, 'w') as f:
    f.write(json.dumps(data))

with open(indexpage, 'w') as f:
    f.write(template.render(**locals()))

print(f'Uložené informácie o {len(obce)} obciach')
