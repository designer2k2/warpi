#!/bin/bash
# setup some needed parts for the warpi
echo "Start warpi needed program install"
apt update
apt -y install kismet
apt -y install python3-smbus
apt -y install i2c-tools
apt -y install gpsd gpsd-clients
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
echo "Install warpi python in venv with requirements"
VENV_DIR="venvwarpi"
REQUIREMENTS_FILE="requirements.txt"
# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment '$VENV_DIR'..."
    python3 -m venv --system-site-packages "$VENV_DIR" || { echo "Failed to create virtual environment."; exit 1; }
    echo "Virtual environment '$VENV_DIR' created."
fi

# Install requirements
if [ -f "$REQUIREMENTS_FILE" ] && [ -s "$REQUIREMENTS_FILE" ]; then
    echo "Installing packages from '$REQUIREMENTS_FILE'..."
    "$VENV_DIR/bin/pip" install -U -r "$REQUIREMENTS_FILE" || echo "Failed to install requirements from '$REQUIREMENTS_FILE'."
else
    echo "No '$REQUIREMENTS_FILE' found or it is empty. Skipping package installation."
fi
echo "finished"
# apt -y install realtek-rtl88xxau-dkms
