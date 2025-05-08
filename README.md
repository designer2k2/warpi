# warpi
"GUI" script running on a Raspberry Pi 5, 4 and 3b, handling the startup, conversion and shutdown procedure.

It is a user interface to run [Kismet](https://www.kismetwireless.net/) for [Wardriving](https://en.wikipedia.org/wiki/Wardriving).

## Setup:

See the article on my website on how to setup the complete system: [designer2k2.at Wardriving setup](https://www.designer2k2.at/de/mods/elektronik/156-raspberry-pi-wardriving-setup)

![warpi in action](https://www.designer2k2.at/images/stories/rpiwarpiinaction.jpg)

## User interface:

![User Interface](https://github.com/designer2k2/warpi/raw/master/warpi_gui.png)

* Blue button: Shutdown. Stops Kismet, converts the file and then powers down the raspberry pi.
* Red button: Reboot. Reboot from the raspberry pi without file conversion.
* Yellow push direction: Stop. Stops Kismet. Useful to reload the config.
* Green push direction: Start. Starts Kismet. Useful after it has been stopped.
* Left arrow: switch between screens.

## Screen information:

![Screen](https://github.com/designer2k2/warpi/raw/master/warpi_screen.png)

First line: CPU Load in % / Memory usage in % / CPU Temperature in °C  
Second line: GPS Status (3=3D lock, 2=2D lock, 1=No lock) / Satellites in View / Satellites used / Status  
Third line: Devices found by Kismet  
Fourth line: Memory used by Kismet  
Fifth line: Current time / Live blink  
