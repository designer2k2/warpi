#!/usr/bin/python3
#encoding=utf-8

# converts a kismet db to wigle csv
# this uses the devices table, no packets needed
# it handles WIFI and Bluetooth devices

# Warning:
# it only checks if the given file exists, not if its valid!
# the Kismet DB would provide a version, but its not checked here.

# Stephan Martin 2019
# https//www.designer2k2.at

import sys
import os
import json
import sqlite3
from datetime import datetime
import logging
import errno

logger = logging.getLogger(__name__)

def main(fname):

	logger.info("Processing: %s" % fname)
	
	if not os.path.exists(fname):
		logger.error("Kismet DB not found!! "+str(fname))
		raise FileNotFoundError(
			errno.ENOENT, os.strerror(errno.ENOENT), fname)

	conn = sqlite3.connect(fname)
	c = conn.cursor()
	
	# first clean up: (this takes forever on slow media(usb sticks)
	# c.execute('VACUUM')

	# first lets see what we have:
	c.execute('SELECT * FROM KISMET')
	logger.debug (c.fetchone())

	c.execute('SELECT device,avg_lat,avg_lon FROM devices WHERE phyname="IEEE802.11" AND type="Wi-Fi AP" AND min_lat != 0')

	dataextract = c.fetchall()
	
	outfilename = (''.join(fname.split('.')[:-1])) + ('.CSV')
	logger.debug("saving to %s" % outfilename)

	outfile = open(outfilename, 'w')
		
	lines = 0
		
	# header:
	outfile.write('WigleWifi-1.4,appRelease=20190201,model=Kismet,release=2019.02.01.6,device=kismet,display=kismet,board=kismet,brand=kismet\n')
	outfile.write('MAC,SSID,AuthMode,FirstSeen,Channel,RSSI,CurrentLatitude,CurrentLongitude,AltitudeMeters,AccuracyMeters,Type\n')

	# first the wifi:
	for row in dataextract:
		jsonextract = json.loads(row[0])

		# lets find the interesting things:

		mac = jsonextract['kismet.device.base.macaddr']
		ssid = jsonextract['kismet.device.base.name']
		auth = '['+jsonextract['kismet.device.base.crypt']+']'
		first = str(datetime.fromtimestamp(jsonextract['kismet.device.base.first_time']))
		chan = jsonextract['kismet.device.base.channel']
		rssi = jsonextract['kismet.device.base.signal']['kismet.common.signal.max_signal']
		lat = row[1]
		lon = row[2]
		alt = jsonextract['kismet.device.base.location']['kismet.common.location.avg_loc']['kismet.common.location.alt']

		# write a line
		outfile.write(mac+','+ssid+','+auth+','+first+','+str(chan)+','+str(rssi)+','+str(lat)+','+str(lon)+','+str(alt)+',0,WIFI\n')
		lines = lines + 1

	# clear memory
	dataextract = None
		
	# now the bluetooth:

	c.execute('SELECT device,avg_lat,avg_lon FROM devices WHERE phyname="Bluetooth" AND min_lat != 0')

	dataextract = c.fetchall()
	
	lines2 = 0

	for row in dataextract:
		jsonextract = json.loads(row[0])

		# lets find the interesting things:

		mac = jsonextract['kismet.device.base.macaddr']
		ssid = jsonextract['kismet.device.base.name']
		auth = ''
		first = str(datetime.fromtimestamp(jsonextract['kismet.device.base.first_time']))
		chan = 10
		rssi = 0
		lat = row[1]
		lon = row[2]
		alt = jsonextract['kismet.device.base.location']['kismet.common.location.avg_loc']['kismet.common.location.alt']
		what = jsonextract['kismet.device.base.type']
		
		if what == "BTLE":
			what = "BLE"
		if what == "BR/EDR":
			what = "BT"

		# write a line
		outfile.write(mac+','+ssid+','+auth+','+first+','+str(chan)+','+str(rssi)+','+str(lat)+','+str(lon)+','+str(alt)+',0,'+what+'\n')
		lines2 = lines2 + 1


	outfile.close()

	logger.debug("File done. " + str(lines) + " WIFI Devices, " + str(lines2) + " Bluetooth Devices.")


def print_usage():
	print("Usage: *.kismet *.kismet *.kismet... ")
	print("Description: ")
	print("Converts Kismetdb logfile with WIFI and Bluetooth devices to WiGLE.csv")


if __name__ == "__main__":
	print("Kismet DB to Wigle CSV converter\n")

	if sys.version_info[0] < 3:
		print("This script requires Python 3")
		sys.exit(-1)

	if len(sys.argv) < 2:
		print_usage()
		sys.exit(-1)
	else:
				
		for p in sys.argv[1:]:
			if p[0] != "-":
				if not os.path.exists(p):
					print("File not found: %s" % p)
					continue

				r = main(p)
