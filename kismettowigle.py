#!/usr/bin/python3
# encoding=utf-8

# converts a kismet db to wigle csv
# this uses the devices table, no packets needed
# it handles WIFI AP´s and Bluetooth devices

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

    logger.info(f"Processing: {fname}")

    if not os.path.exists(fname):
        logger.error(f"Kismet DB not found!! {fname}")
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), fname)

    outfilename = csvname(fname)
    logger.debug(f"saving to {outfilename}")

    if os.path.exists(outfilename):
        logger.error(f"CSV already exists, exit. {outfilename}")
        raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), outfilename)

    # open the csv:
    outfile = open(outfilename, "w")

    # connect to the kismet db file:
    conn = sqlite3.connect(fname)
    c = conn.cursor()

    # first clean up: (this takes forever on slow media(old usb sticks)
    c.execute("VACUUM")

    # first lets see what we have:
    c.execute("SELECT * FROM KISMET")
    logger.debug(c.fetchone())

    c.execute(
        'SELECT device,avg_lat,avg_lon FROM devices WHERE phyname="IEEE802.11" AND type="Wi-Fi AP" AND min_lat != 0'
    )

    dataextract = c.fetchall()

    lines = 0

    # header:
    outfile.write(
        "WigleWifi-1.4,appRelease=20190201,model=Kismet,release=2019.02.01.6,device=kismet,display=kismet,"
        "board=kismet,brand=kismet\n"
    )
    outfile.write(
        "MAC,SSID,AuthMode,FirstSeen,Channel,RSSI,CurrentLatitude,CurrentLongitude,AltitudeMeters,AccuracyMeters,Type\n"
    )

    # first the wifi ap´s:
    for row in dataextract:
        jsonextract = json.loads(row[0])

        # lets find the interesting things:

        mac = jsonextract["kismet.device.base.macaddr"]
        ssid = jsonextract["kismet.device.base.name"]
        auth = "[" + jsonextract["kismet.device.base.crypt"] + "]"
        first = str(datetime.fromtimestamp(jsonextract["kismet.device.base.first_time"]))
        chan = jsonextract["kismet.device.base.channel"]
        rssi = jsonextract["kismet.device.base.signal"]["kismet.common.signal.max_signal"]
        lat = row[1]
        lon = row[2]
        alt = jsonextract["kismet.device.base.location"][
            "kismet.common.location.avg_loc"
        ]["kismet.common.location.alt"]

        # write a line
        outfile.write(f"{mac},{ssid},{auth},{first},{chan},{rssi},{lat},{lon},{alt},0,WIFI\n")
        lines = lines + 1

    # now bluetooth:
    c.execute('SELECT device,avg_lat,avg_lon FROM devices WHERE phyname="Bluetooth" AND min_lat != 0')

    dataextract = c.fetchall()

    lines2 = 0

    for row in dataextract:
        jsonextract = json.loads(row[0])

        # lets find the interesting things:

        mac = jsonextract["kismet.device.base.macaddr"]
        ssid = jsonextract["kismet.device.base.name"]
        first = str(datetime.fromtimestamp(jsonextract["kismet.device.base.first_time"]))
        lat = row[1]
        lon = row[2]
        alt = jsonextract["kismet.device.base.location"][
            "kismet.common.location.avg_loc"
        ]["kismet.common.location.alt"]
        what = jsonextract["kismet.device.base.type"]

        if what == "BTLE":
            what = "BLE"
        if what == "BR/EDR":
            what = "BT"

        # write a line
        outfile.write(f"{mac},{ssid},,{first},10,0,{lat},{lon},{alt},0,{what}\n")
        lines2 = lines2 + 1

    outfile.close()

    logger.debug(f"File done. {lines} WIFI AP´s, {lines2} Bluetooth Devices.")


def csvname(kismetdbname: str) -> str:
    outfilename = ("".join(kismetdbname.split(".")[:-1])) + ".CSV"
    return outfilename


def print_usage():
    print(f"Usage: *.kismet *.kismet *.kismet... ")
    print(f"Description:")
    print(f"Converts Kismetdb logfile with WIFI AP´s and Bluetooth devices to WiGLE.csv")


if __name__ == "__main__":
    print(f"Kismet DB to Wigle CSV converter\n")

    if sys.version_info[0] < 3:
        print(f"This script requires Python 3")
        sys.exit(-1)

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(-1)
    else:
        for p in sys.argv[1:]:
            if p[0] != "-":
                if not os.path.exists(p):
                    print(f"File not found: {p}")
                    continue
                r = main(p)
