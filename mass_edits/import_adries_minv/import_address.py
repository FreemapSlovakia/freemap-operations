#!/usr/bin/env python3
"""
Skript pre generovanie html stranok a OSM suborov na https://minvskaddress.b3das.com/data/

Zavislosti:
 Vstupne data:
   - http://proxy.freemap.sk/minvskaddress/adresy.zip - Dodkom (ircdodko) pravidelne aktualizovany subor
                                                        s adresami ako csv subor v kodovani utf-8
   - hranice obci ZSJ

 Kniznice:
   - geopandas - spracovanie geodat
   - overpass - stahovanie dat z OSM (verzia 0.7 vyzaduje patch pre obce s hranicami definovanymi ako
                                      multipolygon: https://github.com/mvexel/overpass-api-python-wrapper/issues/135)
   - jinja2 - generovanie stranok zo sablony

 TODO:
 - colorschema na parne/neparne cisla
 - address checker v JOSM

Pomocne tagy generovane skriptom:

dont_tag_buildings  - v zdrojovych datach sa viackrat opakuje to iste supisne cislo (napr. vchody budov), preto
                      sa tieto adresy nemaju parovat s budovami, iba s existujucimi bodmi
dont_tag_buildings2 - adresa nema byt umiestnena na budovu, pretoze na ploche budovy v OSM sa nachadza viac
                      ako jeden existuci adresny bod.

Popis niektorych GeoDataFrame objektov:

city_gdf      - adresy z datasetu minvskaddress v ramci hranic obce
buildings_gdf - polygony budov z OSM db, stiahnute pomocou overpass (query: way["building"]["building"!="roof"]), ohranicene
                uzemim obce
addrnodes_gdf - adresne body z OSM db, stiahnute pomocou overpass (query: node["addr:housenumber"][!amenity][!shop]),
                ohranicene uzemim obce, poznamka: obchod s adresou NIE je adresny bod (preto ich pomocou !amenity a !shop
                vylucujem)
z1            - prienik budov z OSM (buildings_gdf) a adresnych bodov z OSM (addrnodes_gdf)
z2            - prienik budov z OSM (buildings_gdf) a adresnych bodov z MINV (city_gdf)

"""

from collections import defaultdict
from datetime import datetime
from geojson import dump
from io import StringIO
from jinja2 import Environment, FileSystemLoader
from logging import info
from lxml import etree as ET
from overpass import API
from shapely.geometry import Point, mapping
from streetname_map import streetname_map
from time import sleep
import argparse
import fiona
import geopandas as gpd
import json
import logging
import numpy as np
import os
import pandas as pd
import re
import requests
import shapely
import shlex
import socket
import subprocess
import sys
import yaml
import zipfile

# tolerancia s akou sa zjednodusia hranice obce
tolerance = 0.001

config_data = {}
if os.path.isfile('config.yaml'):
    with open('config.yaml') as f:
        config_data = yaml.safe_load(f)

webroot = config_data.get('webroot')
url_template = config_data.get('url_template', '%s')

logging.basicConfig(level=logging.INFO)
env = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("city.html")

minv_url = "http://proxy.freemap.sk/minvskaddress/adresy.zip"
replacement_map = streetname_map.replacement_map
muni_replacement_map = streetname_map.muni_replacement_map


def save_html(**kwargs):
    """vyrenderuje a uloz stranku obce do html suboru"""
    with open(f"{citycode}/index.html", "w") as f:
        f.write(template.render(kwargs))


def create_housenumber(n):
    """vrati housenumber ako conscriptionnumber/streetnumber alebo conscriptionnumber,
       ak streetnumber neexistuje"""
    if n["addr:streetnumber"]:
        return n["addr:conscriptionnumber"] + "/" + n["addr:streetnumber"]
    return n["addr:conscriptionnumber"]


def get_minv_data():
    """stiahne najnovsie data (ak su k dispozicii) MINV"""
    size_on_server = int(requests.head(minv_url, allow_redirects=True).headers["Content-Length"])
    if os.path.exists("adresy.zip"):
        local_size = os.stat("adresy.zip").st_size
    else:
        local_size = 0
    if size_on_server != local_size:
        info("Zistena potreba stahovania - ziskavam adresy.zip..")
        r = requests.get(minv_url)
        with open("adresy.zip", "wb") as f:
            f.write(r.content)


def to_int_or_zero(i):
    """pomocna funkcia pre pandas import"""
    return 0 if not i else int(i)


def to_float_or_na(i):
    """pomocna funkcia pre pandas import"""
    return np.float32(i.replace(",", ".")) if i else np.nan


def to_str_or_empty(i):
    """pomocna funkcia pre pandas import"""
    return "" if i == "None" else str(i)


def to_str_or_zero(i):
    """pomocna funkcia pre pandas import"""
    return "0" if i == "" else str(i)


class Boundary:
    def __init__(self):
        info("Nacitam hranice obci (ZSJ)..")
        gdf = gpd.read_file(os.path.join(os.path.dirname(__file__), "zsj84"), encoding="utf8")
        gdf2 = gdf.loc[:, ("kod_zuj", "naz_zuj", "geometry")]
        kod_nazovobce = gdf2.loc[:, ("kod_zuj", "naz_zuj")].drop_duplicates()
        self.hranice_obci = gpd.GeoDataFrame(
            gdf2.groupby("kod_zuj").geometry.agg(shapely.ops.unary_union).reset_index(),
            geometry="geometry",
        )
        self.hranice_obci = self.hranice_obci.merge(
            kod_nazovobce, on="kod_zuj", how="left"
        )
        self.hranice_obci.set_index("kod_zuj", inplace=True)
        #self.hranice_obci.index = self.hranice_obci.index.to_series().apply(
            #lambda n: n.replace(" - mestská časť ", "-")
        #)

    def poly(self, municipality=None):
        if not isinstance(municipality, list):
            municipality = [municipality]
        municipalities = pd.Index(municipality)
        return self.hranice_obci.loc[
            self.hranice_obci.index.intersection(municipalities)
        ]


def normalize_streetname(streetname):
    """oprav nazov ulice `streetname` podla kluca nizsie"""
    norm_name = streetname
    # vyhod ul./ulica na konci nazvu ulice
    norm_name = re.sub(r"(.*) ([uU]l\.|[uU]lica)(\b|$)", r"\1", norm_name)
    # za medzeru patri vzdy a prave jedna medzera
    norm_name = re.sub(r"\.(?=[^ ])", ". ", norm_name)
    # vyhod medzery na zaciatku a konci
    norm_name = norm_name.strip()
    # rozsir nam. na namestie
    norm_name = re.sub(r"([nN])ám\.", r"\1ámestie", norm_name)
    # vyhod ul./ulica na zaciatku nazvu ulice a prve pismeno zmen na velke
    norm_name = re.sub(
        r"^([uU]l\. *|[uU]lica )(.*)",
        lambda n: n.group(2)[0].upper() + n.group(2)[1:],
        norm_name,
    )
    # 2 a viac medzier vymen za jednu
    norm_name = re.sub(r"  *", " ", norm_name)
    # Nam/Namestie/Mieru/Partizán/Slobody/Rad/Cesta/Park/Gen./Kpt./Detí/Vrch/
    # Ihrisk/Mládeže/Hrdinov/Lúky/Aleja/Koniec/Majer/Rieke/Háj/Vodami/Budovateľ/
    # Brehu/Dolin/Kameni/Stanicu/Osada/Bitúnku/Dobrovoľníkov/Strana/Dedina/
    # Bojovníkov/Trh/Humnami/Strelnic/Trieda/Jama/Zábava/Kúpele/Kameň/Kríž/Potok/
    # Sad/Riadok/Hora/Veža/Kopanice/Armády/Nábr/Skala/Pažiť/Pole/Priekop/Les
    # je velkym zaciatocnym pismenom len na zaciatku nazvu
    norm_name = re.sub(
        r" ("
        "Aleja|"
        "Nár.*Pov|"
        "Amfiteát|"
        "Armády|"
        "Baštou|"
        "Bitúnku|"
        "Záhrad|"
        "Stráňa|"
        "Bojovníkov|"
        "Pionierov|"
        "Brán(a|ou)|"
        "Rybník|"
        "Rybníčkoch|"
        "Brázdach|"
        "Brehu*|"
        "Budovateľ|"
        "Cechy|"
        "Cesta|"
        "Colnici|"
        "Dedina|"
        "Detí|"
        "Diaľnic|"
        "Doba|"
        "Dobrovoľníkov|"
        "Dolin(e|a|y)|"
        "Dolnom Konci|"
        "Dubu|"
        "Dukelských|"
        "Dvor|"
        "Gen\.|"
        "Háj|"
        "Hámor|"
        "Hora|"
        "Hôrkami|"
        "Hostinci|"
        "Hradbami|"
        "Hrádzou|"
        "Hrbe|"
        "Hraničiarov|"
        "Hrdinov|"
        "Hrebienkom|"
        "Humnami|"
        "Chrbát|"
        "Ihrisk|"
        "Jama|"
        "Jark(om|y)|"
        "Jaskyni|"
        "Jazdiarni|"
        "Jazero|"
        "Kameň|"
        "Kameni|"
        "Kanálom|"
        "Kláštorom|"
        "Kockách|"
        "Kolíske|"
        "Koniec|"
        "Kopanice|"
        "Kope$|"
        "Kpt\.|"  # noqa: W608
        "Kríž|"
        "Kúpele|"
        "Kúriou|"
        "Kút|"
        "Kúte|"
        "Kútoch|"
        "Laz|"
        "Lehote|"
        "Les|"
        "Lodenici|"
        "Lúčka|"
        "Lúky|"
        "Majer(\b|i|$)|"
        "Martýrov|"
        "Mestom|"
        "Mieru|"
        "Mládeže|"
        "Mlyn|"
        "Motorest|"
        "Múrom|"
        "Nábr|"
        "Nádvor|"
        "Nám(\.|estie)|"
        "Nivy|"
        "Ohradami|"
        "Ohrade|"
        "Okolie|"
        "Okruhliak|"
        "Osada|"
        "Ostrovy|"
        "Panoráme|"
        "Park|"
        "Partizán|"
        "Paseka|"
        "Pasienkoch|"
        "Paž[ií][ťt]|"
        "Peci|"
        "Pílu|"
        "Pleso|"
        "Plynárni|"
        "Pole|"
        "Polícii|"
        "Pošte|"
        "Potočky|"
        "Potok|"
        "Povst|"
        "Prameni|"
        "Predmest|"
        "Priekop|"
        "Pustatina|"
        "Rad$|"
        "Rašelin|"
        "Riadk(och|u)|"
        "Riadok|"
        "Riek(e|ou)|"
        "Rodiny|"
        "Roh$|"
        "Role|"
        "Rovn|"
        "Rožku|"
        "Ruže|"
        "Sad|"
        "Salaši|"
        "Skala|"
        "Skalám|"
        "Skalke|"
        "Slobody|"
        # Smrečine  (Smrečina = fabrika)
        "Splave|"
        "Stanicu|"
        "Strana|"
        "Stráňami|"
        "Stráňou|"
        "Strelnic|"
        "Studn|"
        "Studničke|"
        "Tehelňu|"
        "Terasy|"
        "Trh(\b|$)|"
        "Trieda|"
        "Ulička|"
        "Uličkou|"
        "Veža|"
        "Vila|"
        "Vinic|"
        "Vinohradoch|"
        "Vinohrady|"
        "Vodami|"
        "Vrch|"
        "Vŕškami|"
        "Vŕšku|"
        "Vršky|"
        "Zábava|"
        "Záhumenice|"
        "Zámočku"
        ")",
        lambda n: n.group(0).lower(),
        norm_name,
    )
    # Sv/Svateho je velkym zaciatocnym pismenom len na zaciatku nazvu
    norm_name = re.sub(r" Sv(\.|ät)", r" sv\1", norm_name)
    # zaciatocne pismeno je vzdy velke
    norm_name = re.sub(r"^(.)", lambda n: n.group(0).upper(), norm_name)
    # nazvy mesiacov za bodkou su malym (11. marca, 8. maja..)
    norm_name = re.sub(r"\. (Mája|Marca)", lambda n: n.group(0).lower(), norm_name)

    # zname chyby a preklepy oprav podla pomocnej mapy
    if norm_name in replacement_map.keys():
        norm_name = replacement_map[norm_name]
    return norm_name


def normalize_streetnames(g):
    info("Normalizujem nazvy ulic napriec datasetom..")
    g["nstreet"] = g["addr:street"].apply(normalize_streetname)

    info("Normalizujem nazvy ulic v ramci jednotlivych obci..")
    for muni in muni_replacement_map.keys():
        for bad_name, good_name in muni_replacement_map[muni].items():
            for x in g.loc[(g.city == muni) & (g.nstreet == bad_name)].index:
                g.at[x, "nstreet"] = good_name


def cut(g, citycode):
    """vyrez body podla hranic obce/obci (str alebo list)"""
    global boundary
    poly = boundary.poly(citycode)
    poly.loc[:, "group"] = "default"
    poly = poly.dissolve(by="group")
    return g[g.intersects(poly.geometry["default"])]


def dropped_points(g, citycode):
    """zobrazi odrezane body"""
    global boundary
    poly = boundary.poly(citycode)
    poly.loc[:, "group"] = "default"
    poly = poly.dissolve(by="group")
    return g[~g.intersects(poly.geometry["default"])]


def validate_osm_addresses2(x):
    ret = defaultdict(gpd.GeoDataFrame)
    if "addr:streetnumber" not in x.columns:
        return ret
    ret["mismatching_addresses"] = x[
        (x["addr:housenumber"].str.contains("/", na=False))
        & (
            x["addr:conscriptionnumber"] + "/" + x["addr:streetnumber"]
            != x["addr:housenumber"]
        )
    ]
    ret["incomplete_addresses"] = x[
        (~x["addr:housenumber"].str.contains("/", na=True))
        & (x["addr:conscriptionnumber"] != x["addr:housenumber"])
        & (x["addr:streetnumber"] != x["addr:housenumber"])
    ]
    return ret


def validate_minv_addresses(x):
    ret = {}
    info("Zistujem adresy bez lokacie..")
    no_location_address = x[x.lat.isnull()].loc[
        :, ("city", "addr:street", "addr:conscriptionnumber", "addr:streetnumber")
    ]
    ret["no_location_address"] = no_location_address
    info("Zistujem adresy s rovnakou lokaciou..")
    # konverzia na retazec kvoli vyssiemu vykonu
    duplicate_locations = x[x.geometry.apply(lambda n: str(n)).duplicated()]
    duplicate_locations = duplicate_locations.loc[
        :, ("nstreet", "addr:conscriptionnumber", "addr:streetnumber", "lat", "lon")
    ]
    # odstranenie duplicit bez poloh
    duplicate_locations = duplicate_locations[~duplicate_locations.lat.isnull()]
    ret["duplicate_locations"] = duplicate_locations
    return ret


def crosscheck_addresses(minv, osm):
    """
    porovna adresy medzi minv a osm. vracia slovnik obsahujuci GeoDataFrame pre 2 kluce.
    """
    ret = defaultdict(gpd.GeoDataFrame)
    if "addr:streetnumber" not in osm.columns:
        return ret
    minv = minv.drop_duplicates()
    merged = minv.merge(osm, on=("addr:conscriptionnumber", "addr:streetnumber"))
    ret["bad_street"] = merged[
        (~merged["addr:street_y"].isnull())
        & (merged["nstreet"] != "")
        & (merged["nstreet"] != merged["addr:street_y"])
    ]

    merged = minv.merge(
        osm,
        left_on=("addr:streetnumber", "nstreet"),
        right_on=("addr:streetnumber", "addr:street"),
    )
    ret["bad_conscriptionnumber"] = merged[
        (~merged["addr:conscriptionnumber_y"].isnull())
        & (merged["addr:conscriptionnumber_x"] != merged["addr:conscriptionnumber_y"])
    ]
    return ret


def validate_osm_addresses():
    """
    skontroluje uplnost adries v suboru ``source_osm'', vracia dict s nasledovnymi klucmi:
      - incomplete_addresses - element ma vyplneny addr:housenumber, ale chyba supisne alebo orientacne cislo
                               alebo
                               element ma vyplneny addr:housenumber vo formate XX/YY, ale nie je pritomne aj supisne aj orientacne cislo
      - mismatching_addresses - addr:housenumber nezodpoveda "addr:conscriptionnumber/addr:streetnumber"

    """
    ret = defaultdict(list)
    xml_tree = ET.parse(source_osm)
    root_element = xml_tree.getroot()

    for element in root_element:
        housenumber = element.find('tag[@k="addr:housenumber"]')
        streetnumber = element.find('tag[@k="addr:streetnumber"]')
        conscriptionnumber = element.find('tag[@k="addr:conscriptionnumber"]')

        if housenumber is None:
            housenumber = ""
        else:
            housenumber = housenumber.get("v")

        if streetnumber is None:
            streetnumber = ""
        else:
            streetnumber = streetnumber.get("v")

        if conscriptionnumber is None:
            conscriptionnumber = ""
        else:
            conscriptionnumber = conscriptionnumber.get("v")

        if housenumber and not (streetnumber or conscriptionnumber):
            ret["incomplete_addresses"].append(element.tag[0] + element.get("id"))
            continue

        if "/" in housenumber and not (streetnumber and conscriptionnumber):
            ret["incomplete_addresses"].append(element.tag[0] + element.get("id"))
            continue

        if "/" in housenumber and housenumber != f"{conscriptionnumber}/{streetnumber}":
            ret["mismatching_addresses"].append(element.tag[0] + element.get("id"))

    return ret


def get_overpass_query(polygons):
    """vrati overpass query string pre ziskanie adries a budov z OSM v ramci polygonu (hranice obce)"""
    global overpass_query

    query = "( "
    for polygon in polygons:
        query += f"""way["building"](poly:"{" ".join(polygon)}");
nwr["addr:housenumber"](poly:"{" ".join(polygon)}");
node["addr:conscriptionnumber"](poly:"{" ".join(polygon)}");"""

    query += " ); (._;>;)"
    # query += " )"

    return query


def save_osm_city(query, ignored_ways):
    """stiahne OSM data o adresach pomocou zadanej overpass query, ulozi do suboru
    source_osm, ktory bude pouzity ako vstup do Conflatora,
    vracia pocet adries, cesty v ignored ways su preskocene
    """
    data = api.get(query=query, verbosity="meta", responseformat="xml")

    # with open(source_osm, "w") as f:
        # f.write(data)

    count = 0
    osm = ET.fromstring(data.encode())
    for element in osm:
        if element.tag == 'way' and int(element.get('id', 0)) in ignored_ways:
           element.getparent().remove(element)
           continue
        for tag in element:
            if tag.get("k") == "addr:housenumber":
                count += 1
    osm.getroottree().write(source_osm)

    return count


def get_osm_city(query):
    """stiahne OSM data o adresach pomocou zadanej overpass query, vrati geodataframe"""

    data = api.get(query=query, verbosity="geom", responseformat="geojson")
    to_keep = (
        "addr:conscriptionnumber",
        "addr:streetnumber",
        "addr:street",
        "building",
        "addr:housenumber",
        "object_id",
    )
    for feature in data["features"]:
        obj_id = str(feature["id"])
        geometry_type = feature["geometry"]["type"]
        if geometry_type == "Point":
            element_type = "n"
        elif geometry_type == "LineString":
            element_type = "w"
        else:
            element_type = "r"
        feature["properties"]["object_id"] = element_type + obj_id
        feature["properties"] = {
            x: feature["properties"][x] for x in feature["properties"] if x in to_keep
        }
    return gpd.read_file(str(data))


def save_osm_buildings(buildings_json, polygons):
    """stiahne OSM data o budovach pre dany polygon obce, ulozi do suboru
    buildings_json, ktory bude pouzity ako vstup do Conflatora. zaroven sa pouziva
    na doplnenie pomocnych tagov
    """
    global overpass_query
    query = "( "
    for polygon in polygons:
        query += f"""way["building"]["building"!="roof"](poly:"{" ".join(polygon)}");"""

    query += " ); (._;>;)"

    with open(buildings_json, "w") as f:
        data = api.get(query=query, verbosity="geom", responseformat="geojson")
        dump(data, f)


def save_osm_addrnodes(addrnodes_json, polygons):
    global overpass_query
    query = "( "
    for polygon in polygons:
        query += f"""node["addr:housenumber"][!amenity][!shop](poly:"{" ".join(polygon)}");"""

    query += " ); (._;>;)"

    with open(addrnodes_json, "w") as f:
        data = api.get(query=query, verbosity="geom", responseformat="geojson")
        dump(data, f)


def get_osm_streets(polygons):
    query = "( "
    for polygon in polygons:
        query += f"""nwr["addr:street"](poly:"{" ".join(polygon)}");
                   way[highway~"(residential|primary|secondary|tertiary|unclassified)"]["name"](poly:"{" ".join(polygon)}");
                   node["addr:conscriptionnumber"](poly:"{" ".join(polygon)}");"""

    query += " ); "

    ret = []

    streetnames_data = api.get(query=query, responseformat="json")
    for element in streetnames_data.get("elements"):
        tags = element.get("tags")
        street = tags.get("addr:street")
        street_name = tags.get("name")
        if street:
            ret.append(street)
            continue
        else:
            ret.append(street_name)
    return set([x for x in ret if x])


def check_overlapping_buildings(g, citycode):
    duplicates = g[g.index.duplicated()]
    if len(duplicates) > 0:
        info(duplicates.geometry)
    return (g[~g.index.duplicated()], duplicates.loc[:, ("lat", "lon")])


def to_datasource(g, citycode):
    result = []
    g = g.loc[
        :,
        (
            "lat",
            "lon",
            "addr:conscriptionnumber",
            "addr:streetnumber",
            "dont_tag_buildings",
            "dont_tag_buildings2",
            "addr:street",
            "geometry",
            "identifier",
            "addr:postcode",
            "addr:housenumber",
        ),
    ]
    g.drop_duplicates(inplace=True)
    for line in g.iterrows():
        (
            lat,
            lon,
            conscriptionnumber,
            streetnumber,
            dont_tag_buildings,
            dont_tag_buildings2,
            street,
            geometry,
            identifier,
            psc,
            housenumber,
        ) = line[1]
        result.append(
            {
                "id": identifier,
                "lat": lat,
                "lon": lon,
                "tags": {
                    "addr:conscriptionnumber": conscriptionnumber,
                    "addr:streetnumber": streetnumber,
                    "dont_tag_buildings": dont_tag_buildings,
                    "dont_tag_buildings2": dont_tag_buildings2,
                    "addr:postcode": psc,
                    "addr:street": street,
                    "addr:housenumber": housenumber,
                },
            }
        )
    with open(source_json, "w") as f:
        f.write(g.to_json())

    with open(result_json, "w") as f:
        json.dump(result, f)


    info(f"Zapísané do {source_json}")


def check_josm():
    # check if JOSM is running (remote connection must be available)
    s = socket.socket()
    s.settimeout(5)
    try:
        s.connect(("127.0.0.1", 8111))
        return True
    except socket.error:
        return False
    finally:
        s.close()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", type=str, dest='outdir', metavar='OUTDIR', help="cesta, kde bude vytvoreny adresar s nazvom obce, standardne: ak nie je definovany v config.yaml pouzije sa aktualny adresar (ak nie je definovany)", default=".")
    parser.add_argument("citycode", help="kod mesta/obce, ktore/a sa ma spracovat")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    citycode = args.citycode
    outdir = args.outdir
    if outdir != '.':
        print(f'Presuvam sa do adresara {outdir}')
        os.chdir(outdir)
    else:
        if webroot:
            outdir = webroot
            print(f'Presuvam sa do adresara {outdir}')
            os.chdir(outdir)

    buildings_json = f"{citycode}/buildings_{citycode}.geojson"
    addrnodes_json = f"{citycode}/addrnodes_{citycode}.geojson"
    date_generated = datetime.now().strftime("%d. %m. %Y o %H:%M")

    source_osm = f"{citycode}/source_{citycode}.osm"
    source_json = f"{citycode}/source_{citycode}.geojson"

    result_osm = f"{citycode}/result_{citycode}.osm"
    result_json = f"{citycode}/result_{citycode}.geojson"

    filtered_csv = f"{citycode}/{citycode}_filtered.csv"

    outside_buildings_json = f"{citycode}/outside_buildings_{citycode}.geojson"
    list_file = f"{citycode}/{citycode}_list.txt"

    outside_boundaries_json = f"{citycode}/{citycode}_outside_boundaries.geojson"

    original_city_boundary = f"{citycode}/{citycode}_original_boundary.geojson"
    simplified_city_boundary = f"{citycode}/{citycode}_simplified_boundary.geojson"

    overpass_query = ""

    if not os.path.exists(citycode):
        os.mkdir(citycode)

    info(f"Spusta sa spracovanie obce/mesta {citycode}..")

    info("Stahuju sa nove data z MINV, ak su k dispozicii..")
    get_minv_data()

    csv_file = zipfile.ZipFile("adresy.zip").namelist()[0]
    date_match = re.match(
        r"Adresy_(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})", csv_file
    )
    date_minv = "{}. {}. {}".format(*date_match.group("day", "month", "year"))

    boundary = Boundary()

    api = API(timeout=300, endpoint='https://overpassw.freemap.sk/api/interpreter')

    info("Zostavujem polygon(y) pre Overpass query..")
    polygon_geometry = boundary.poly(citycode).geometry[0]
    info("Ukladam povodne hranice obce do suboru..")

    with fiona.open(
        original_city_boundary,
        schema={"geometry": polygon_geometry.type, "properties": {}},
        driver="GeoJSON",
        mode="w",
    ) as boundary_file:
        boundary_file.write({"geometry": mapping(polygon_geometry), "properties": {}})

    polygon_geometry = polygon_geometry.simplify(tolerance)
    info("Ukladam zjednodusene hranice obce do suboru..")

    with fiona.open(
        simplified_city_boundary,
        schema={"geometry": polygon_geometry.type, "properties": {}},
        driver="GeoJSON",
        mode="w",
    ) as boundary_file:
        boundary_file.write({"geometry": mapping(polygon_geometry), "properties": {}})

    polygons = []

    for subarea in mapping(polygon_geometry)["coordinates"]:
        polygon_points = []
        subarea = subarea if len(subarea) > 2 else subarea[0]
        for coords in subarea:
            x, y = coords
            polygon_points.append(f"{y} {x}")
        polygons.append(polygon_points)

    overpass_query = get_overpass_query(polygons)
    # print(overpass_query); sys.exit()
    print(overpass_query)
    osm_city_gdf = get_osm_city(overpass_query)

    # validate
    # osm_city_gdf[(~osm_city_gdf['addr:housenumber'].isnull()) & (osm_city_gdf['addr:conscriptionnumber'] + '/' + osm_city_gdf['addr:streetnumber'] != osm_city_gdf['addr:housenumber'])]

    info(f"Nacitam .csv subor {csv_file}..")

    zipped_csv_file = zipfile.ZipFile("adresy.zip")
    filtered = []
    with zipped_csv_file.open(zipped_csv_file.namelist()[0]) as f:
        for line in f:
            line = line.decode("utf-8").strip()
            # are we sure this is safe?
            if citycode != line.split(',')[-1] and "ADRBOD_X" not in line:
                continue
            filtered.append(line)
    filtered = "\n".join(filtered)
    with open(filtered_csv, 'w') as f:
        f.write(filtered)

    adresy_df = pd.read_csv(
        filtered_csv,
        sep=",",
        converters={
            "ORIENTACNE_CISLO_CELE": to_str_or_empty,
            "SUPISNE_CISLO": to_str_or_empty,
            "PSC": to_str_or_empty,
            "ULICA": to_str_or_empty,
            "ADRBOD_X": to_float_or_na,
            "ADRBOD_Y": to_float_or_na,
        },
    )
    geom = [Point(xy) for xy in zip(adresy_df["ADRBOD_X"], adresy_df["ADRBOD_Y"])]

    info("Konvertujem do GeoDataFrame..")
    adresy_gdf = gpd.GeoDataFrame(adresy_df, geometry=geom)
    adresy_gdf.rename(
        columns={
            "SUPISNE_CISLO": "addr:conscriptionnumber",
            "OBEC": "city",
            "ULICA": "addr:street",
            "IDENTIFIKATOR": "identifier",
            "ORIENTACNE_CISLO_CELE": "addr:streetnumber",
            "PSC": "addr:postcode",
            "ADRBOD_X": "lon",
            "ADRBOD_Y": "lat",
        },
        inplace=True,
    )

    normalize_streetnames(adresy_gdf)

    city_gdf = adresy_gdf.loc[adresy_gdf.municipalityCode == citycode]
    city = city_gdf.city[0]

    info("Zistujem priemernu a max. vzdialenost bodov v ramci jednej adresy")
    suspicious_distances = pd.DataFrame(columns=["name", "ratio"])

    for street in set(city_gdf.nstreet):
        if not street:
            continue
        street_gdf = city_gdf[city_gdf.nstreet == street]
        desc = street_gdf.geometry.apply(
            lambda x: street_gdf.distance(x).nsmallest(3).max()
        ).describe()
        mean = desc["mean"]
        maximum = desc["max"]
        suspicious_distances = pd.concat([suspicious_distances,
            pd.DataFrame({"name": street, "ratio": maximum / mean}, index=[0])], ignore_index=True
        )

    suspicious_distances = suspicious_distances.dropna().sort_values(
        "ratio", ascending=False
    )

    info("Kontrolujem spravnost adries..")
    bad_addresses_osm = validate_osm_addresses2(osm_city_gdf)
    bad_addresses_minv = validate_minv_addresses(city_gdf)
    bad_addresses_crosschecked = crosscheck_addresses(city_gdf, osm_city_gdf)

    city_gdf = city_gdf[~city_gdf.lat.isnull()]
    city_gdf["addr:housenumber"] = city_gdf.apply(create_housenumber, axis=1)
    county = city_gdf.KRAJ.iloc[0]
    district = city_gdf.OKRES.iloc[0]

    osm_streets = get_osm_streets(polygons)
    minv_streets = set([x for x in city_gdf.nstreet if x])

    info("Orezavam body podla hranic obce")
    dropped_points = dropped_points(city_gdf, citycode)
    city_gdf = cut(city_gdf, citycode)

    info(f"Orezanych {len(dropped_points)} adresnych bodov")
    if not dropped_points.empty:
        with open(outside_boundaries_json, 'w') as f:
            f.write(dropped_points.to_json())

    city_gdf = city_gdf.assign(
        dont_tag_buildings=city_gdf.groupby("addr:conscriptionnumber")
        .transform("count")
        .KRAJ
        > 1
    )
    try:
        city_gdf = city_gdf.set_crs("EPSG:4326")
    except:
        pass
    bbox = city_gdf.total_bounds

    info(f"Stahujem budovy v ramci hranic obce ..")
    save_osm_buildings(buildings_json, polygons)

    info(f"Stahujem adresne body v ramci hranic obce ..")
    save_osm_addrnodes(addrnodes_json, polygons)

    info(
        "Robim prienik budov a adresnych bodov a pridavam pomocny tag (dont_tag_buildings2=true/false)"
    )
    buildings_gdf = gpd.read_file(buildings_json)
    buildings_gdf.set_index(pd.json_normalize(json.load(open(buildings_json))["features"])["id"].values, inplace=True)
    addrnodes_gdf = gpd.read_file(addrnodes_json)

    # keep only linestrings, then convert lines to polygons
    buildings_gdf = buildings_gdf[buildings_gdf.geometry.type == "LineString"]
    polygon_geometry_buildings = buildings_gdf.geometry.apply(shapely.geometry.Polygon)
    buildings_gdf = buildings_gdf.assign(polygon_geometry=polygon_geometry_buildings)
    buildings_gdf = buildings_gdf.set_geometry(polygon_geometry_buildings)

    # potrebujeme zoznam budov, ktore nebude import brat do uvahy, pretoze
    # sa na nich nachadza adresny bod, preto urobime ich prienik
    z1 = gpd.sjoin(
        buildings_gdf, addrnodes_gdf, how="inner", predicate="intersects", lsuffix="x", rsuffix="y"
    )

    osm_addr_count = save_osm_city(overpass_query, ignored_ways=set(z1.index))

    z2 = gpd.sjoin(
        buildings_gdf, city_gdf, how="right", predicate="intersects", lsuffix="x", rsuffix="y"
    )

    buildings_gdf.loc[:, ('geometry')].to_file('/tmp/buildings')
    z2 = z2.assign(dont_tag_buildings2=(z2.groupby(z2.index_x).transform("count").lon / 2) > 1)
    z2 = z2.rename(
        columns={
            "addr:streetnumber_y": "addr:streetnumber",
            "dont_tag_buildings": "dont_tag_buildings",
            "dont_tag_buildings2": "dont_tag_buildings2",
            "addr:street": "street_orig",
            "nstreet": "addr:street",
            "addr:postcode_y": "addr:postcode",
            "addr:housenumber_y": "addr:housenumber",
            "addr:conscriptionnumber_y": "addr:conscriptionnumber",
        }
    )

    z2, duplicates = check_overlapping_buildings(z2, citycode)
    to_datasource(z2, citycode)

    info("Hladam adresne body mimo budov..")
    # pouzivame metre a tak potrebujeme docasne zmenit projekciu
    address_outside_of_building = gpd.sjoin(
        buildings_gdf.to_crs(crs=3857),
        gpd.GeoDataFrame({"geometry": city_gdf.to_crs(crs=3857).buffer(9.00009)}),
        how="right",
        predicate="intersects",
    )
    address_outside_of_building = address_outside_of_building[
        address_outside_of_building.index_left.isnull()
    ]
    address_outside_of_building = address_outside_of_building.to_crs(crs=4326)
    open(outside_buildings_json, "w").write(address_outside_of_building.to_json())

    info("Spajam s datami z OSM..")
    profile = os.path.join(os.path.join(os.path.dirname(__file__), 'profile'))
    conflate_cmd = f'conflate -l "{list_file}" -vi "{result_json}" "{profile}" -o "{result_osm}" -c preview.json --osm "{source_osm}"'
    info(conflate_cmd)
    conflate = subprocess.Popen(
        shlex.split(conflate_cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    conflate_stdout, conflate_stderr = conflate.communicate()
    renamed_streets = city_gdf[city_gdf.nstreet != city_gdf["addr:street"]]
    renamed_streets = renamed_streets.loc[:, ("addr:street", "nstreet")]
    renamed_streets = renamed_streets.drop_duplicates().sort_values("addr:street")

    save_html(**locals())
