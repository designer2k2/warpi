#!/usr/bin/python3
# encoding=utf-8

# Menue for the wigle/replacement device
# https://www.designer2k2.at 2021
#
# This is working on a rpi4
#
# Libs:
# gpsd https://github.com/MartijnBraam/gpsd-py3
#
#
# kismet conf must be correct!
# gpsd will be called, check that it works with UART
#
# it expects a USB drive on /media/usb/ with the folder kismet there.
# Logs will be written to /media/usb/
#
# Warning:
# there are only some failsafes, it will stop working on error!

# The username and password must match with kismet_site.conf
httpd_username = "root"
httpd_password = "toor"

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M",
    filename="/media/usb/warpi.log",
)

logging.info("Startup")

# Sync HW Clock::
import subprocess

subprocess.run(["hwclock", "-s"])

logging.debug(f"HW Clock synced")

import board
import busio
from digitalio import DigitalInOut, Direction, Pull
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from time import sleep, localtime, strftime
import gpsd
import psutil
from os import listdir
import os
import signal
import RPi.GPIO as GPIO
import json
import requests

# the konverter tool:
import kismettowigle

logging.debug(f"All imports done")

# Turn some logger to only show warnings:
logging.getLogger("gpsd").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

# Create the SSD1306 OLED class.
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# flip screen that the usb ports from the rpi are on top
disp.rotation = 2

# Input Pin:
GPIO.setmode(GPIO.BCM)

logging.debug(f"IO Setup")

# Interrupts:
Counter = 0


def InterruptLeft(channel):
    global Counter
    # Count one up and print it
    Counter = Counter + 1
    print(f"Counter: {Counter}")


def InterruptB(channel):
    fshutdown()


def InterruptA(channel):
    freboot()


def InterruptUp(channel):
    startservice()


def InterruptDown(channel):
    stopservice()


# 5 button A reboot
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(5, GPIO.RISING, callback=InterruptA, bouncetime=300)

# 6 button B shutdown
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(6, GPIO.RISING, callback=InterruptB, bouncetime=300)

# Up dir button start
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(22, GPIO.RISING, callback=InterruptUp, bouncetime=300)

# Down dir button stop
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(17, GPIO.RISING, callback=InterruptDown, bouncetime=300)

# Left dir button (only to check)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(23, GPIO.RISING, callback=InterruptLeft, bouncetime=300)


logging.debug(f"GPIO Setup done")

# Clear display.
disp.fill(0)
disp.show()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new("1", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Load a font
font = ImageFont.truetype("/home/kali/Minecraftia.ttf", 8)
fontbig = ImageFont.truetype("/home/kali/arial.ttf", 24)

logging.debug(f"Display setup done")

# set country code
# call("iw reg set AT", shell=True)

gpsrun = False
life = True
sleeptime = 1

# globals for the log:
kisuselog = open("/media/usb/kisuselog.log", "w")  # new everytime
kiserrlog = open("/media/usb/kiserrlog.log", "a+")  # append
kissubproc = 0

# this delay will be waited, then it starts automatically
autostart = 10
autostarted = False


def startservice():
    logging.info(f"Starting GPSD / Kismet")
    subprocess.Popen(["gpsd", "/dev/serial0", "-s", "9600"])
    global kisuselog, kiserrlog, gpsrun, kissubproc
    kissubproc = subprocess.Popen(["kismet"], stdout=kisuselog, stderr=kiserrlog)
    gpsrun = True


def stopservice():
    logging.info(f"Stopping GPSD / Kismet")
    global gpsrun, kissubproc
    gpsrun = False
    # Send a polite INT (CTRL+C)
    kissubproc.send_signal(signal.SIGINT)
    try:
        kissubproc.wait(10)  # wait max 10sec to close
    except subprocess.TimeoutExpired:
        logging.debug(f"timeout during kill kismet happened")
    try:
        subprocess.run(
            ["killall", "gpsd", "--verbose", "--wait", "--signal", "QUIT"], timeout=5
        )
    except subprocess.TimeoutExpired:
        logging.debug(f"timeout during kill gpsd happened")


def freboot():
    logging.info(f"Rebooting")
    global looping
    looping = False
    disp.fill(0)
    disp.show()
    subprocess.Popen(["reboot"])
    quit()


def fshutdown():
    global looping, kisuselog, kiserrlog
    looping = False
    logging.info(f"Shutdown")
    stopservice()
    kisuselog.close()
    kiserrlog.close()
    logging.debug(f"Kismet shutdown")
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.text((0, 20), f"Convert", font=fontbig, fill=255)
    disp.image(image)
    disp.show()
    convertall()
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.text((0, 20), f"Shutdown", font=fontbig, fill=255)
    disp.image(image)
    disp.show()
    logging.debug(f"LCD Black")
    subprocess.call("sudo shutdown -h now", shell=True)
    logging.debug(f"shutdown -h triggered")
    quit()


def list_files1(directory, extension):
    return (f for f in listdir(directory) if f.endswith("." + extension))


def convertall():
    logging.debug(f"Convert kismets")
    # only do this when the kismet it not running
    if not gpsrun:
        list = list_files1("/media/usb/kismet/", "kismet")

        for them in list:
            # print(them)
            csvfilename = kismettowigle.csvname(them)
            # print(csvfilename)
            if not os.path.exists("/media/usb/kismet/" + csvfilename):
                logging.debug(f"CSV from Kismet not found, create: {csvfilename}")
                kismettowigle.main("/media/usb/kismet/" + them)
    logging.debug(f"Convert from all done")


logging.debug(f"All setup, go into loop")

looping = True

while looping:
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    if life:
        draw.rectangle((120, 56, width, height), outline=0, fill=255)
        life = False
    else:
        draw.rectangle((120, 56, width, height), outline=0, fill=0)
        life = True

    cpu = psutil.cpu_percent()
    mem = dict(psutil.virtual_memory()._asdict())["percent"]
    swp = dict(psutil.swap_memory()._asdict())["percent"]
    f = open("/sys/class/thermal/thermal_zone0/temp")
    t = f.read()
    f.close()
    ct = int(t) / 1000.0

    if cpu > 50:
        subprocess.call(
            "ps aux | sort -nrk 3,3 | head -n 10 >> /media/usb/highcpu.log", shell=True
        )
        logging.debug(f"High CPU: {cpu}")
        sleeptime = 3
    else:
        sleeptime = 1

    draw.text(
        (0, 0),
        f"CPU: {cpu / 100:>4.0%}  M: {mem / 100:>4.0%} T: {ct:5.1f}",
        font=font,
        fill=255,
    )
    draw.text(
        (0, 54), strftime("%Y-%m-%d   %H:%M:%S", localtime()), font=font, fill=255
    )

    if gpsrun:
        try:
            gpsd.connect()
            packet = gpsd.get_current()
            draw.text(
                (0, 10),
                f"GPS: {packet.mode}  SAT: {packet.sats:>3}  Use: {packet.sats_valid:>3}",
                font=font,
                fill=255,
            )
            if packet.mode == 0:
                draw.rectangle((115, 20, width - 2, 10), outline=0, fill=0)
            if packet.mode == 1:
                draw.rectangle((120, 18, width - 4, 14), outline=255, fill=0)
            if packet.mode == 2:
                draw.rectangle((120, 18, width - 4, 14), outline=255, fill=1)
            if packet.mode == 3:
                draw.rectangle((115, 20, width - 2, 10), outline=255, fill=1)
            resp = requests.get(
                "http://127.0.0.1:2501/system/status.json", auth=(httpd_username, httpd_password)
            )
            data = resp.json()
            devices = data["kismet.system.devices.count"]
            kismetmemory = data["kismet.system.memory.rss"] / 1024
            draw.text((0, 20), f"D {devices:>7}", font=fontbig, fill=255)
            draw.text(
                (0, 44),
                f"Kismet mem: {kismetmemory:>4.0f}mb",
                font=font,
                fill=255,
            )
        except Exception as e:
            logging.error(f"An exception occurred {e}")

    if not autostarted:
        if autostart > 0:
            autostart = autostart - 1
        else:
            autostarted = True
            if not gpsrun:
                startservice()

    # draw the screen:
    disp.image(image)
    disp.show()

    # wait a bit:
    sleep(sleeptime)


while True:
    sleep(10)
