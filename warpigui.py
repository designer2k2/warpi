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
# kismet conf must be correct! 
# gpsd will be called, check that it works with UART

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M',
					filename='/media/usb/warpi.log')

logging.info('Startup')

#fake cpuinfo:
import subprocess
subprocess.call("sudo mount -v --bind /root/fake-cpuinfo /proc/cpuinfo", shell=True)
subprocess.run(["hwclock", "-s"])

logging.debug('HW Clock synced')

import board
import busio
import Adafruit_GPIO.Platform as Platform
import Adafruit_GPIO.I2C as I2C
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from time import sleep, localtime, strftime
import gpsd
import kismet_rest
import psutil 
from os import listdir
import os
import signal
import RPi.GPIO as GPIO  

#the konverter tool:
import kismettowigle

logging.debug('All imports done')

#Turn some logger to only show warnings:
logging.getLogger("gpsd").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)


# Create the SSD1306 OLED class.
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

#flip screen that the usb ports from the rpi are on top
disp.rotation = 2

# Input Pin:
GPIO.setmode(GPIO.BCM) 

logging.debug('IO Setup')

# Interrupts:
Counter = 0
def InterruptLeft(channel):
    global Counter
    # Counter um eins erhoehen und ausgeben
    Counter = Counter + 1
    print("Counter " + str(Counter))

def InterruptB(channel):
    fshutdown()

def InterruptA(channel):
    freboot()	

def InterruptUp(channel):
    startservice()

def InterruptDown(channel):
    stopservice()
	
#6 button A reboot
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)  
GPIO.add_event_detect(5, GPIO.RISING, callback=InterruptA, bouncetime=300) 
	
#6 button B shutdown
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP)  
GPIO.add_event_detect(6, GPIO.RISING, callback=InterruptB, bouncetime=300) 

#Up dir button start
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)  
GPIO.add_event_detect(22, GPIO.RISING, callback=InterruptUp, bouncetime=300)

#Down dir button stop
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  
GPIO.add_event_detect(17, GPIO.RISING, callback=InterruptDown, bouncetime=300)

#Left dir button (only to check)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)  
GPIO.add_event_detect(23, GPIO.RISING, callback=InterruptLeft, bouncetime=300)


logging.debug('GPIO Setup done')

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

logging.debug('Display setup done')

# set country code
# call("iw reg set AT", shell=True)

gpsrun = False
life = True
sleeptime = 1

#globals for the log:
kisuselog = open("/media/usb/kisuselog.log","w")    # new everytime
kiserrlog = open("/media/usb/kiserrlog.log","a+")  # append
kissubproc = 0

#this delay will be waited, then it starts automatically
autostart = 10
autostarted = False

def startservice():
    logging.info("Starting GPSD / Kismet")
    #call("gpsd /dev/serial0", shell=True)
    subprocess.Popen(["gpsd", "/dev/serial0"])
    #call('screen -dm bash -c "kismet"', shell=True)
    global kisuselog, kiserrlog, gpsrun, kissubproc
    kissubproc = subprocess.Popen(["kismet"],stdout=kisuselog,stderr=kiserrlog)
    gpsrun = True
	
def stopservice():
    logging.info("Stopping GPSD / Kismet")
    global gpsrun, kissubproc	
    gpsrun = False
    #call("killall kismet", shell=True)
    #Send a polite INT (CTRL+C)
    kissubproc.send_signal(signal.SIGINT)
    try:
        kissubproc.wait(10)  #wait max 10sec to close
    except subprocess.TimeoutExpired:
        logging.debug("timeout during kill kismet happened")
    try:
        subprocess.run(["killall", "gpsd", "--verbose", "--wait", "--signal", "QUIT"],timeout=5)
    except subprocess.TimeoutExpired:
        logging.debug("timeout during kill gpsd happened")
	
	
def freboot():
    logging.info("Rebooting")
    global looping
    looping = False
    disp.fill(0)
    disp.show()
    subprocess.Popen(["reboot"])
    quit()

def fshutdown():
    global looping,kisuselog, kiserrlog
    looping = False
    logging.info("Shutdown")
    stopservice()
    kisuselog.close()
    kiserrlog.close()
    #call("killall kismet", shell=True)
    #call("sleep 1", shell=True)
    logging.debug("Kismet shutdown")
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.text((0, 20),'Convert',font=fontbig, fill=255)	
    disp.image(image)	
    disp.show()
    convertall()
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.text((0, 20),'Shutdown',font=fontbig, fill=255)	
    disp.image(image)	
    disp.show()
    logging.debug("LCD Black")
    subprocess.call("sudo shutdown -h now", shell=True)
    logging.debug("shutdown -h triggered")
    quit()
		
def list_files1(directory, extension):
    return (f for f in listdir(directory) if f.endswith('.' + extension))
	
def convertall():
    logging.debug("Convert kismets")
    #only do this when the kismet it not running
    if not gpsrun:
        list = list_files1('/media/usb/kismet/','kismet')
        
        for them in list:
            #print(them)
            csvfilename = (''.join(them.split('.')[:-1])) + ('.CSV')
            #print(csvfilename)
            if not os.path.exists('/media/usb/kismet/'+csvfilename):
                logging.debug("CSV from Kismet not found, create it "+str(csvfilename))
                kismettowigle.main('/media/usb/kismet/'+them)
    logging.debug("Convert from all done")

logging.debug('All setup, go into loop')

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
    mem = dict(psutil.virtual_memory()._asdict())['percent']
    swp = dict(psutil.swap_memory()._asdict())['percent']
    ct = 0 #psutil.sensors_temperatures()['cpu-thermal'][0]._asdict()['current']
    
    if cpu > 50:
        subprocess.call("ps aux | sort -nrk 3,3 | head -n 10 >> /media/usb/highcpu.log", shell=True)
        logging.debug("High CPU: " + str(cpu))
        sleeptime = 3
    else:
        sleeptime = 1
	
    draw.text((0, 0),'CPU:  {:>3.0%}   M: {:>3.0%} Swp: {:>3.0%}'.format(cpu/100,mem/100, swp/100),font=font, fill=255)
    draw.text((0, 54),strftime("%Y-%m-%d   %H:%M:%S", localtime()),font=font, fill=255)	

    if gpsrun:
        try:
            gpsd.connect()
            packet = gpsd.get_current()		
            draw.text((0, 10),'GPS:  ' + str(packet.mode) + '  SAT:  ' + str(packet.sats) + '  Use:  ' + str(packet.sats_valid),font=font, fill=255)
            if packet.mode == 0:
                draw.rectangle((115, 20, width-2, 10), outline=0, fill=0)
            if packet.mode == 1:
                draw.rectangle((120, 18, width-4, 14), outline=255, fill=0)
            if packet.mode == 2:
                draw.rectangle((120, 18, width-4, 14), outline=255, fill=1)			
            if packet.mode == 3:
                draw.rectangle((115, 20, width-2, 10), outline=255, fill=1)		
            conn = kismet_rest.KismetConnector(username='root',password='toor')
            devices = conn.system_status()['kismet.system.devices.count']
            kismetmemory = conn.system_status()['kismet.system.memory.rss']
            draw.text((0, 20),'D {:>7}'.format(devices),font=fontbig, fill=255)
            draw.text((0, 44),'Kismet mem: {:>4.0f}mb'.format(kismetmemory/1000),font=font, fill=255)
        except Exception as e:
            logging.error("An exception occurred " + str(e)) 
	
    if not autostarted:	
        if autostart > 0:
            autostart =	autostart -1
        else:
            autostarted = True
            if not gpsrun:
                startservice()

	#draw the screen:
    disp.image(image)
    disp.show()

	#wait a bit:
    sleep(sleeptime)


while True:
    sleep(10)
