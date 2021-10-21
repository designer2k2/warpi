# warpi
"GUI" script running on a Raspberry Pi 4, handling the startup, conversion and shutdown procedure.


## Setup:

See the article on my website on how to setup the complete system: [designer2k2.at Wardriving setup](https://www.designer2k2.at/de/mods/elektronik/156-raspberry-pi-wardriving-setup)

![warpi in action](https://www.designer2k2.at/images/stories/rpiwarpiinaction.jpg)

## User interface:

![User Interface](https://github.com/designer2k2/warpi/raw/master/warpi_gui.png)

* Blue button: Shutdown. Stops Kismet, converts the file and then powers down the raspberry pi.
* Red button: Reboot. Direct reboot from the raspberry pi.
* Yellow push direction: Stop. Stops Kismet. Usefull to reload the config.
* Green push direction: Start. Starts Kismet. Usefull after it has been stopped.

## Screen informations:

![Screen](https://github.com/designer2k2/warpi/raw/master/warpi_screen.png)

First line: CPU Load in % / Memory usage in % / CPU Temperature in °C  
Second line: GPS Status (3=3D lock, 2=2D lock, 1=No lock) / Satellites in View / Satellites used / Status  
Third line: Devices found by kismet  
Fourth line: Memory used by kismet  
Firth line: Current time / Live blink  
