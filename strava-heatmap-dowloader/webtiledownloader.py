#!/usr/bin/env python
# original script by:
# (c) BikeCityGuide
# WTFPL
#
# Mon Mar 11 22:33:46 CET 2013
# (c) Michael Maier
# GPL v3 or later

import re
import argparse
import urllib2
import sqlite3
import os, os.path
import sys
# import Image
import ctypes
from StringIO import StringIO
import time
import subprocess
# import MySQLdb
# from shapely.geometry import Polygon,box
from collections import namedtuple

parser = argparse.ArgumentParser(description="""
Takes a rectangle as input, calculates tile numbers from it and downloads them.
Copied from tiledownloader.py and adapted for Finnder tiles:
* directory structure
* no sqlite file creation
* take bounds from DB, not cmdline
""")

#parser.add_argument("-c", "--city-code", help="city-code", required=True)

#parser.add_argument("--db-host", help="The database host", default="")
#parser.add_argument("--db-user", help="The database user", default="")
#parser.add_argument("--db-password", help="The database user password", default="") #, required=True)
#parser.add_argument("--db-name", help="The database name", default="")

parser.add_argument("--min-zoom", type=int, default=1)
parser.add_argument("--max-zoom", type=int, default=16)

# center param has no effect
parser.add_argument("--center-lat", type=float)
parser.add_argument("--center-lon", type=float)

#top=46.78 bottom=46.610 left=15.3 right=15.66
parser.add_argument("--top", type=float, default=49.62)
parser.add_argument("--bottom", type=float, default=47.72)
parser.add_argument("--left", type=float, default=16.83)
parser.add_argument("--right", type=float, default=22.57)

parser.add_argument("--url", default="https://heatmap-external-b.strava.com/tiles-auth/both/bluered")

parser.add_argument("--optimize-png", action="store_true", help="if true, the png's will be optimized with pngcrush. Must be installed")

parser.add_argument("-f", "--force-download", action="store_true", help="if set, the tiles are downloaded, no matter if they already exist")

parser.add_argument("--print-only", action="store_true", help="just print the tile numbers and exit")
parser.add_argument("--check-only", action="store_true", help="just check if the sqlite-file is complete")
parser.add_argument("-o", "--output", default="web_tiles", help="destination directory")

parser.add_argument("--tile-side-len", type=int, default=256)

opts = parser.parse_args()

if opts.min_zoom > opts.max_zoom:
	print "max-zoom is not > min-zoom"
	sys.exit(1)

if opts.max_zoom > 18:
	print "max-zoom can't be > 18"
	sys.exit(1)

if opts.min_zoom < 1:
	print "min-zoom < 1"
	sys.exit(1)

if opts.left > opts.right:
	print " left > right, exchanging"
	tmp = opts.left
	opts.left = opts.right
	opts.right = tmp

if opts.top < opts.bottom:
	print " top < bottom, exchanging"
	tmp = opts.top
	opts.top = opts.bottom
	opts.bottom = tmp


# from http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Python
import math
def deg2num(lat_deg, lon_deg, zoom):
	lat_rad = math.radians(lat_deg)
	n = 2.0 ** zoom
	xtile = int((lon_deg + 180.0) / 360.0 * n)
	ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
	return (xtile, ytile)


def download(rect_bounds):
	output_dir = "%s" % os.path.basename(opts.output)
	if os.path.exists(output_dir):
		# TODO: refresh instead
		print "IMPORTANT! A dir named %s already exists. In order to download everything from scratch, remove this directory first" % output_dir
	else:
		os.makedirs(output_dir)

	total_download_size = 0
	total_optimized_size = 0
	for zoom in range(opts.min_zoom, opts.max_zoom+1):
		processed_cnt = 0
		download_cnt = 0
		sum_size = 0
		failed_cnt = 0
		(min_x, min_y) = deg2num(rect_bounds.top, rect_bounds.left, zoom)
		(max_x, max_y) = deg2num(rect_bounds.bottom, rect_bounds.right, zoom)
		print "zoom=%d - min_x=%d, min_y=%d, max_x=%d, max_y=%d" % (zoom, min_x, min_y, max_x, max_y)

		for y_index in range(min_y, max_y+1):
			for x_index in range(min_x, max_x+1):
				processed_cnt += 1
				tile_url = opts.url + "/%d/%d/%d.png?px=256" % (zoom, x_index, y_index)
				#print tile_url

				if opts.print_only:
					continue

				path = "%s/%d/%d" % (output_dir, zoom, x_index)
				filename = path + "/%d.png" % y_index
				if not os.path.exists(path):
					os.makedirs(path)

				data = None
				if not os.path.exists(filename) or opts.force_download:
#					need_retry = False
					webFile = None

					# low zoom-levels take long to render. Give more time (more retries possible)
					max_retries = 2 ** (15 - zoom)
					if max_retries < 1:
						max_retries = 1

					download_succeeded = False
					for try_nr in range(1, max_retries+2): # +1 for starting with 1, +1 bcs range goes to n-1 and we want min 1 retry
				#	for try_nr in range(1, 2):
						try:
							#print "trying %s" % tile_url
							opener = urllib2.build_opener()
							opener.addheaders.append(('Cookie', '_strava4_session=3gvqjm67kjd6a0l3qjejuaj8jkjkbbpo; CloudFront-Policy=eyJTdGF0ZW1lbnQiOiBbeyJSZXNvdXJjZSI6Imh0dHBzOi8vaGVhdG1hcC1leHRlcm5hbC0qLnN0cmF2YS5jb20vKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTU5NTU3OTMyMn0sIkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNTk0MzU1MzIyfX19XX0_; CloudFront-Key-Pair-Id=APKAIDPUN4QMG7VUQPSA; CloudFront-Signature=jNeGRa~vZsQ7pO3EJ6DMFkOp0B7Y2MYEHv0n03io401iAtXuTHqe2ksNMbnDAX330we-bO1KBcbN3j0tvwvT2HyuEZyFp~bT4UbtUV6MKQuSLqajeU8ErKcwOU7dHYr3olCtTeJ8JFrVfk008~stuhGmyEXRlQRajyZHtrphLkKSxKVTsuay-AhVEPre0cJC3YXpeqexnMstmdqskLJINdOMcI66DFYX~UhndQuujmREjbj6Q92NyKMxb2rFyAUJ7vnaxer8vzcCZ2kj~cYgtFVFfqEY0DP39EyfM79DtKZxCjDN8PEKbRhI2V1-zMr4~CMzdZ~eBH3d3EEWPknpMg__'))
							webFile = opener.open(tile_url)
							data = webFile.read()
							download_cnt += 1
							download_succeeded = True
							break
						except Exception, e:
							print e
							print "%s failed on try nr %d" % (tile_url, try_nr)
#							need_retry = True
							# give the server some time, maybe that helps
							time.sleep(7)

					if not download_succeeded:
						continue;

					try:
						localFile = open(filename, 'w')
						localFile.write(data)
						webFile.close()
						localFile.close()

						total_download_size += os.path.getsize(filename)

						if opts.optimize_png:
							tmpfile = "%s/pngcrush_tmp.png" % output_dir
							cmd = "pngcrush -q " + filename + " " + tmpfile
							retcode = subprocess.call(cmd.split(" "))
							if retcode != 0:
								print "ERROR: pngcrush returned %d" % retcode
							else:
								# replacing the downloaded file with the optimized one
								os.unlink(filename)
								os.rename(tmpfile, filename)
								total_optimized_size += os.path.getsize(filename)

						sum_size += len(data)

					except Exception, e:
						os.unlink(filename)
						failed_cnt += 1
						print e
						print "ERROR for %s" % tile_url
						continue


		success_cnt = processed_cnt - failed_cnt
		avg_size = 0
		# avoid possible division by zero
		if success_cnt != 0:
			avg_size = sum_size / success_cnt

		print "processed %d tiles - downloaded: %d, failed: %d, avg size: %d" % (processed_cnt, download_cnt, failed_cnt, avg_size)

	print "total download size: %d, total optimized size: %d" % (total_download_size, total_optimized_size)


def get_tile_bounds(zoom, x_index, y_index):
	n = 2.0 ** zoom
	lon_min = x_index / n * 360.0 - 180.0
	lat_min_rad = math.atan(math.sinh(math.pi * (1 - 2 * y_index / n)))
	lat_min = math.degrees(lat_min_rad)

	lon_max = (x_index+1) / n * 360.0 - 180.0
	lat_max_rad = math.atan(math.sinh(math.pi * (1 - 2 * (y_index+1) / n)))
	lat_max = math.degrees(lat_max_rad)

	#print "lat_min %f, lat_max %f, lon_min %f, lon_max %f" % (lat_min, lat_max, lon_min, lon_max)
	return lat_min, lat_max, lon_min, lon_max

# RectBounds = namedtuple('RectBounds', ['top', 'left', 'bottom', 'right'])
rect_bounds = namedtuple('RectBounds', ['top', 'left', 'bottom', 'right'])

# returns tuple (top, left, bottom, right)
def get_bounds():
	db = MySQLdb.connect(host=opts.db_host, user=opts.db_user, passwd=opts.db_password, db=opts.db_name)
	db.set_character_set('utf8')
	c = db.cursor()

	sql = '' # rm'd to not expose DB structure
	c.execute(sql % opts.city_code)
#	(top, left) = c.fetchone()
#	tup = (top, left)
	rect_bounds = RectBounds._make(c.fetchone())
#	rect_bounds = c.fetchone()
	return rect_bounds


# ================================

# get bounds
#rect_bounds = get_bounds()
rect_bounds.top = opts.top
rect_bounds.bottom = opts.bottom
rect_bounds.right = opts.right
rect_bounds.left = opts.left

# download
download(rect_bounds)
