#!/usr/bin/python3
#encoding=utf-8

# Menue for the wigle/replacement device
# https://www.designer2k2.at 2019
#
# Libs:
# gpsd https://github.com/MartijnBraam/gpsd-py3
# kismet_rest with pip
#
#
#
# kismet conf must be correct! 
# gpsd will be called, check that it works with UART

#fake cpuinfo:
from subprocess import call
call("sudo mount -v --bind /root/fake-cpuinfo /proc/cpuinfo", shell=True)
call("hwclock -s", shell=True)

import board
import busio
import Adafruit_GPIO.Platform as Platform
import Adafruit_GPIO.I2C as I2C
from digitalio import DigitalInOut, Direction, Pull
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from time import sleep, localtime, strftime
import gpsd
import kismet_rest
import psutil 
from os import listdir
import os

#the konverter tool:
import kismettowigle

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)


# Create the SSD1306 OLED class.
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

#flip screen that the usb ports from the rpi are on top
disp.rotation = 2

# Input pins:
button_A = DigitalInOut(board.D5)
button_A.direction = Direction.INPUT
button_A.pull = Pull.UP
 
button_B = DigitalInOut(board.D6)
button_B.direction = Direction.INPUT
button_B.pull = Pull.UP
 
button_L = DigitalInOut(board.D27)
button_L.direction = Direction.INPUT
button_L.pull = Pull.UP
 
button_R = DigitalInOut(board.D23)
button_R.direction = Direction.INPUT
button_R.pull = Pull.UP
 
button_U = DigitalInOut(board.D17)
button_U.direction = Direction.INPUT
button_U.pull = Pull.UP
 
button_D = DigitalInOut(board.D22)
button_D.direction = Direction.INPUT
button_D.pull = Pull.UP
 
button_C = DigitalInOut(board.D4)
button_C.direction = Direction.INPUT
button_C.pull = Pull.UP


# Clear display.
disp.fill(0)
disp.show()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Load a font
font = ImageFont.truetype('/home/pi/Minecraftia.ttf', 8)
fontbig = ImageFont.truetype('/home/pi/arial.ttf', 24)

# set country code
# call("iw reg set AT", shell=True)

gpsrun = False
life = True
sleeptime = 1

#this delay will be waited, then it starts automatically
autostart = 10
autostarted = False

def startservice():
    print("Starting GPSD / Kismet")
    call("gpsd /dev/serial0", shell=True)
    call("sleep 1", shell=True)
    call('screen -dm bash -c "kismet"', shell=True)
    global gpsrun
    gpsrun = True
	
def stopservice():
    print("Stopping GPSD / Kismet")
    global gpsrun
    gpsrun = False
    call("killall gpsd", shell=True)
    call("killall kismet", shell=True)
	
def list_files1(directory, extension):
    return (f for f in listdir(directory) if f.endswith('.' + extension))
	
def convertall():
    print("Convert kismets")
    #only do this when the kismet it not running
    if not gpsrun:
        list = list_files1('/','kismet')
        
        for them in list:
            #print(them)
            csvfilename = (''.join(them.split('.')[:-1])) + ('.CSV')
            #print(csvfilename)
            if not os.path.exists('/'+csvfilename):
                print("CSV not found, create it "+str(csvfilename))
                kismettowigle.main('/'+them)
    print("Convert from all done")

print("All setup, go into loop")

while True:

    draw.rectangle((0, 0, width, height), outline=0, fill=0)
	
    if life:
        draw.rectangle((120, 56, width, height), outline=0, fill=255)
        life = False
    else:
        draw.rectangle((120, 56, width, height), outline=0, fill=0)
        life = True
	
    cpu = psutil.cpu_percent()
    mem = dict(psutil.virtual_memory()._asdict())['percent']
    swp = dict(psutil.swap_memory()._asdict())['percent']
    ct = 0 #psutil.sensors_temperatures()['cpu-thermal'][0]._asdict()['current']
	
    draw.text((0, 0),'CPU:  {:>3.0%}   M: {:>3.0%} Swp: {:>3.0%}'.format(cpu/100,mem/100, swp/100),font=font, fill=255)
    draw.text((0, 54),strftime("%Y-%m-%d   %H:%M:%S", localtime()),font=font, fill=255)	

    if gpsrun:
        try:
            gpsd.connect()
            packet = gpsd.get_current()		
            draw.text((0, 10),'GPS:  ' + str(packet.mode) + '  SAT:  ' + str(packet.sats) + '  USED:  ' + str(packet.sats_valid),font=font, fill=255)
            conn = kismet_rest.KismetConnector(username='root',password='toor')
            devices = conn.system_status()['kismet.system.devices.count']
            kismetmemory = conn.system_status()['kismet.system.memory.rss']
            draw.text((0, 20),'D {:>7}'.format(devices),font=fontbig, fill=255)
            draw.text((0, 44),'Kismet mem: {:>4.0f}mb'.format(kismetmemory/1000),font=font, fill=255)
        except:
            print("An exception occurred " + str(gpsrun)) 
	
    if not autostarted:	
        if autostart > 0:
            autostart =	autostart -1
        else:
            autostarted = True
            if not gpsrun:
                startservice()
	
    if not button_U.value: # button is pressed
        stopservice()

	#this scans for *kismet files and corresponding .csv, walk all that have no csv
    if not button_L.value: # button is pressed
        convertall()

    #if button_R.value: # button is released
        #draw.polygon([(60, 30), (42, 21), (42, 41)], outline=255, fill=0) #right
    #else: # button is pressed:
        #draw.polygon([(60, 30), (42, 21), (42, 41)], outline=255, fill=1) #right filled

    if not button_D.value: # button is pressed
        startservice()

    if not button_C.value: # button is pressed
        call("hwclock -s", shell=True)
        print("time should be adjusted now")

    if not button_A.value: # button is pressed
        disp.fill(0)
        disp.show()
        call("reboot", shell=True)
        quit()


    if not button_B.value: # button is pressed
        convertall()
        disp.fill(0)
        disp.show()
        call("sudo shutdown -h now", shell=True)
        quit()

	#draw the screen:
    disp.image(image)
    disp.show()

	#wait a bit:
    sleep(sleeptime)
