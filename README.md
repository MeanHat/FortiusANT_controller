# FortiusANT_controller
MiniTFT controller for running FortiusANT on a Raspberry Pi

Controller for FortiusANT from https://github.com/WouterJD/FortiusANT.
Uses headless Raspberry Pi with Adafruit miniPiTFT 240x240 display (https://www.adafruit.com/product/4484).
Tested on RPi3B+ and Tacx Fortius running Bluetooth connection with CTP (Cycle Traning Program) (Zwift in this case).

Assumptions/Dependencies/Requirements:
1. Controller is filed in Home directory along with jpg image for opening screen
2. When RPi starts it automatically executes Controller (tested using ~/.bashrc)
3. Controller starts FortiusANT using .sh script
4. FortiusANT must start with -d1 (or greater) argument to produce logfile which is read by Controller
5. Logfile(s) is/are deleted at close to prevent uncontrolled growth in number of old files
6. Tacx Fortius startup involves calibration which is tracked on display. Need to modify to handle other trainers
7. FortiusANT runs from /home/pi/FortiusANT/pythoncode/ - this is also where log file is stored
