#!/usr/bin/python3
#encoding=utf-8

# converts a kismet db to wigle csv
# this uses the devices table, no packets needed
# it handles WIFI and Bluetooth devices

# Stephan Martin 2019
# https//www.designer2k2.at

import sys
import os
import json
import sqlite3
from datetime import datetime

def main(fname):

	print("Processing: %s" % fname)

	conn = sqlite3.connect(fname)
	c = conn.cursor()
	
	#first clean up:
	c.execute('VACUUM')	

	#first lets see what we have:
	c.execute('SELECT * FROM KISMET')
	print (c.fetchone())

	c.execute('SELECT device FROM devices WHERE phyname="IEEE802.11" AND type="Wi-Fi AP" AND min_lat != 0')

	dataextract = c.fetchall()
	
	outfilename = (''.join(fname.split('.')[:-1])) + ('.CSV')
	print("saving to %s" % outfilename)

	outfile = open(outfilename, 'w')
		
	lines = 0
		
	#header:
	outfile.write('WigleWifi-1.4,appRelease=20190201,model=Kismet,release=2019.02.01.6,device=kismet,display=kismet,board=kismet,brand=kismet\n')
	outfile.write('MAC,SSID,AuthMode,FirstSeen,Channel,RSSI,CurrentLatitude,CurrentLongitude,AltitudeMeters,AccuracyMeters,Type\n')

	#first the wifi:
	for row in dataextract:
		jsonextract = json.loads(row[0])

		#lets find the interesting things:

		mac = jsonextract['kismet.device.base.macaddr']
		ssid = jsonextract['kismet.device.base.name']
		auth = '['+jsonextract['kismet.device.base.crypt']+']'
		first = str(datetime.fromtimestamp(jsonextract['kismet.device.base.first_time']))
		chan = jsonextract['kismet.device.base.channel']
		rssi = jsonextract['kismet.device.base.signal']['kismet.common.signal.max_signal']
		lat = jsonextract['kismet.device.base.location']['kismet.common.location.avg_loc']['kismet.common.location.lat']
		lon = jsonextract['kismet.device.base.location']['kismet.common.location.avg_loc']['kismet.common.location.lon']
		alt = jsonextract['kismet.device.base.location']['kismet.common.location.avg_loc']['kismet.common.location.alt']

		#write a line
		outfile.write(mac+','+ssid+','+auth+','+first+','+str(chan)+','+str(rssi)+','+str(lat)+','+str(lon)+','+str(alt)+',0,WIFI\n')
		lines = lines + 1

	#clear memory
	dataextract = None
		
	#now the bluetooth:

	c.execute('SELECT device FROM devices WHERE phyname="Bluetooth" AND min_lat != 0')

	dataextract = c.fetchall()

	for row in dataextract:
		jsonextract = json.loads(row[0])

		#lets find the interesting things:

		mac = jsonextract['kismet.device.base.macaddr']
		ssid = jsonextract['kismet.device.base.name']
		auth = ''
		first = str(datetime.fromtimestamp(jsonextract['kismet.device.base.first_time']))
		chan = 10
		rssi = 0
		lat = jsonextract['kismet.device.base.location']['kismet.common.location.avg_loc']['kismet.common.location.lat']
		lon = jsonextract['kismet.device.base.location']['kismet.common.location.avg_loc']['kismet.common.location.lon']
		alt = jsonextract['kismet.device.base.location']['kismet.common.location.avg_loc']['kismet.common.location.alt']
		what = jsonextract['kismet.device.base.type']
		
		if what == "BTLE":
			what = "BLE"
		if what == "BR/EDR":
			what = "BT"

		#write a line
		outfile.write(mac+','+ssid+','+auth+','+first+','+str(chan)+','+str(rssi)+','+str(lat)+','+str(lon)+','+str(alt)+',0,'+what+'\n')
		lines = lines + 1


	outfile.close()

	print("all done " + str(lines))
	
def print_usage():
	print("Usage: *.kismet *.kismet *.kismet... ")
	print("Description: ")
	print("Converts Kismetdb logfile with WIFI and Bluetooth devices to WiGLE.csv")
	
if __name__ == "__main__":
	print("Kismetdb to Wigle converter\n")

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
