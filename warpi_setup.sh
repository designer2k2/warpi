#!/bin/bash
# setup some needed parts for the warpi
echo "Start warpi needed program install"
apt update
apt -y install kismet
apt -y install python3-smbus
apt -y install i2c-tools
apt -y install gpsd gpsd-clients
apt -y install realtek-rtl88xxau-dkms
apt -y install ntfs-3g
apt -y install exfat-fuse
apt -y install python3-pip
echo "remove large not needed programs"
apt -y remove metasploit-framework firefox-esr exploitdb powershell-empire
apt -y autoremove
echo "upgrade all to have the latest and greatest"
apt -y upgrade
echo "Download warpi script"
wget https://github.com/designer2k2/warpi/raw/master/warpigui.py
wget https://github.com/designer2k2/warpi/raw/master/requirements.txt
wget https://github.com/designer2k2/warpi/raw/master/PixeloidSans.ttf
echo "Install warpi python requirements"
pip3 install -r requirements.txt
echo "finished"