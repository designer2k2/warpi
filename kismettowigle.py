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

    # Get all WIFI AP´s where a GPS position is known:
    c.execute('SELECT device,avg_lat,avg_lon FROM devices WHERE type="Wi-Fi AP" AND min_lat != 0')

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
        try:
            auth = WifiCryptToString(jsonextract["dot11.device"][
                                         "dot11.device.last_beaconed_ssid_record"]["dot11.advertisedssid.crypt_set"])
        except KeyError:
            auth = f'[{jsonextract["kismet.device.base.crypt"]}]'
        first = str(datetime.fromtimestamp(jsonextract["kismet.device.base.first_time"]))
        chan = jsonextract["kismet.device.base.channel"]
        rssi = jsonextract["kismet.device.base.signal"]["kismet.common.signal.max_signal"]
        lat = row[1]
        lon = row[2]
        alt = jsonextract["kismet.device.base.location"][
            "kismet.common.location.avg_loc"]["kismet.common.location.alt"]

        # write a line
        outfile.write(f"{mac},{ssid},{auth},{first},{chan},{rssi},{lat},{lon},{alt},0,WIFI\n")
        lines = lines + 1

    # now bluetooth devices where a GPS position is known:
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
            "kismet.common.location.avg_loc"]["kismet.common.location.alt"]
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


# taken from kismet kismetdb_to_wiglecsv.cc:
def WifiCryptToString(cryptset):
    crypt_wps = (1 << 26)
    crypt_protectmask = 0xFFFFF
    crypt_wep = (1 << 1)
    crypt_wpa = (1 << 6)
    crypt_tkip = (1 << 5)
    crypt_aes_ccm = (1 << 9)
    crypt_psk = (1 << 7)
    crypt_eap = (1 << 11)
    crypt_wpa_owe = (1 << 17)
    crypt_version_wpa = (1 << 27)
    crypt_version_wpa2 = (1 << 28)
    crypt_version_wpa3 = (1 << 29)

    ss = ""
    if cryptset & crypt_wps:
        ss = "[WPS]"

    if (cryptset & crypt_protectmask) == crypt_wep:
        ss += "[WEP]"

    if cryptset & crypt_wpa:
        cryptver = ""

        if cryptset & crypt_tkip:
            if cryptset & crypt_aes_ccm:
                cryptver = "CCMP+TKIP"
            else:
                cryptver = "TKIP"
        elif cryptset & crypt_aes_ccm:
            cryptver = "CCMP"

        if cryptset & crypt_psk:
            authver = "PSK"
        elif cryptset & crypt_eap:
            authver = "EAP"
        elif cryptset & crypt_wpa_owe:
            authver = "OWE"
        else:
            authver = "UNKNOWN"     # This is sometimes on WPA2?

        if (cryptset & crypt_version_wpa) and (cryptset & crypt_version_wpa2):
            ss += f"[WPA-{authver}-{cryptver}]"
            ss += f"[WPA2-{authver}-{cryptver}]"
        elif cryptset & crypt_version_wpa2:
            ss += f"[WPA2-{authver}-{cryptver}]"
        elif (cryptset & crypt_version_wpa3) or (cryptset & crypt_wpa_owe):
            ss += f"[WPA3-{authver}-{cryptver}]"
        else:
            ss += f"[WPA-{authver}-{cryptver}]"
    return ss


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
