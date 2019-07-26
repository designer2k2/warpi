# Menue for the wigle/replacement device
# https://www.designer2k2.at 2019
#
# Libs:
# gpsd https://github.com/MartijnBraam/gpsd-py3
# kismet_rest with pip3
# kismet site conf must be correct! 

#fake cpuinfo and ensure RTC is read in:
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
fontbig = ImageFont.truetype('/home/pi/Minecraftia.ttf', 24)

# set country code
# call("iw reg set AT", shell=True)

gpsrun = False
life = True
sleeptime = 1

def startservice():
    call("gpsd /dev/serial0", shell=True)
    #call("monstart", shell=True)
    call("sleep 1", shell=True)
    call('screen -dm bash -c "kismet"', shell=True)
    #call('screen -dm bash -c "kismet -c wlan0mon -c wlan2 -c wlan4"', shell=True)
    global gpsrun
    gpsrun = True
	
def stopservice():
    global gpsrun
    gpsrun = False
    call("killall gpsd", shell=True)
    call("killall kismet", shell=True)
    #call("monstop", shell=True)

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
    ct = 0 #psutil.sensors_temperatures()['cpu-thermal'][0]._asdict()['current']
	
    draw.text((0, 0),'CPU:  {:>3.0%}   M: {:>3.0%} T: {:>3}°C'.format(cpu/100,mem/100, int(ct)),font=font, fill=255)
    draw.text((0, 54),strftime("%Y-%m-%d   %H:%M:%S", localtime()),font=font, fill=255)	

    if gpsrun:
        gpsd.connect()
        packet = gpsd.get_current()		
        draw.text((0, 10),'GPS:  ' + str(packet.mode) + '  SAT:  ' + str(packet.sats) + '  USED:  ' + str(packet.sats_valid),font=font, fill=255)
        conn = kismet_rest.KismetConnector(username='root',password='toor')
        devices = conn.system_status()['kismet.system.devices.count']
        draw.text((0, 20),'D {:>7}'.format(devices),font=fontbig, fill=255)
	
    if button_U.value: # button is released
        a = 1
        #draw.polygon([(90, 20), (95, 10), (100, 20)], outline=255, fill=0)  #Up
    else: # button is pressed:
        #draw.polygon([(90, 20), (95, 10), (100, 20)], outline=255, fill=1)  #Up filled
        #disp.show()
        stopservice()

    #if button_L.value: # button is released
        #draw.polygon([(0, 30), (18, 21), (18, 41)], outline=255, fill=0)  #left
    #else: # button is pressed:
        #draw.polygon([(0, 30), (18, 21), (18, 41)], outline=255, fill=1)  #left filled

    #if button_R.value: # button is released
        #draw.polygon([(60, 30), (42, 21), (42, 41)], outline=255, fill=0) #right
    #else: # button is pressed:
        #draw.polygon([(60, 30), (42, 21), (42, 41)], outline=255, fill=1) #right filled

    if button_D.value: # button is released
        #draw.polygon([(95, 60), (100, 42), (90, 42)], outline=255, fill=0) #down
        a = 1
    else: # button is pressed:
        #draw.polygon([(95, 60), (100, 42), (90, 42)], outline=255, fill=1) #down filled
        #disp.show()
        startservice()

    if button_C.value: # button is released
        #draw.rectangle((20, 22, 40, 40), outline=255, fill=0) #center
        a = 1
    else: # button is pressed:
        #draw.rectangle((20, 22, 40, 40), outline=255, fill=1) #center filled
        call("hwclock -s", shell=True)
        print("time should be adjusted now")

    if button_A.value: # button is released
        a = 1
        #draw.ellipse((100, 40, 110, 60), outline=255, fill=0) #A button
    else: # button is pressed:
        #draw.ellipse((100, 40, 110, 60), outline=255, fill=1) #A button filled
        disp.fill(0)
        disp.show()
        call("reboot", shell=True)
        quit()


    if button_B.value: # button is released
	    a=1
        #draw.ellipse((110, 20, 120, 40), outline=125, fill=0) #B button
    else: # button is pressed:
        #draw.ellipse((110, 20, 120, 40), outline=125, fill=1) #B button filled
        disp.fill(0)
        disp.show()
        call("sudo shutdown -h now", shell=True)
        quit()

    disp.image(image)

    disp.show()

    sleep(sleeptime)

