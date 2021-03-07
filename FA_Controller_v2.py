# Controller for FortiusANT from https://github.com/WouterJD/FortiusANT
# Uses headless Raspberry Pi with Adafruit miniPiTFT 240x240 display (https://www.adafruit.com/product/4484)
# Tested on RPi3B+ and Tacx Fortius running Bluetooth connection with CTP (Cycle Traning Program)

#-------------------------------------------------------------------------------
# Version info
#-------------------------------------------------------------------------------
# 2021-02-27    v1.0: First version
# 2021-03-01    v1.1: Separated delete logfiles from shutdown function; stopped checking logfile once trainer starts;
#                     separated out test of lower button 23 as function
# 2021-03-05    v2.0: Updated to run in parallel with FortiusAnt.py (rather than calling it)
#-------------------------------------------------------------------------------
# Assumptions/Dependencies/Requirements:
# 1. Controller is filed in Home directory along with jpg image for opening screen
# 2. When RPi starts it automatically executes FortiusANT.sh (tested using ~/.bashrc)
# 3. FortiusANT.sh starts this Controller and FortiusAnt.py in parallel
# 4. FortiusANT.py must start with -d1 (or greater) argument to produce logfile which is read by Controller
# 5. Logfile(s) is/are deleted at close to prevent uncontrolled growth in number of old files
# 6. Tacx Fortius startup involves calibration which is tracked on display. Need to modify to handle other trainers
# 7. FortiusANT.py runs from /home/pi/FortiusANT/pythoncode/ and log file is stored in same directory
#-------------------------------------------------------------------------------

import glob
import os
import digitalio
import board
import time
import adafruit_rgb_display.st7789 as st7789


from subprocess import call
from PIL import Image, ImageDraw, ImageFont

def td(y,txt,fill_colour): # draw line of text
    draw.text((x,y),txt,font=font, fill=fill_colour)

def w6(): # write 6 lines of text
    # draw a black filled box to clear the image
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
    # draw each of 6 lines in turn
    td(L1[0], L1[1], L1[2])
    td(L2[0], L2[1], L2[2])
    td(L3[0], L3[1], L3[2])
    td(L4[0], L4[1], L4[2])
    td(L5[0], L5[1], L5[2])
    td(L6[0], L6[1], L6[2])
    # display text
    disp.image(image, rotation)
    time.sleep(1.5)

def read_log():
    global readfile
    global filename
    global f
    for filename in glob.glob(latest_file):
        with open(filename, "r") as f:
            readfile = f.read()

def button23(): # check if lower button (23) pressed and start shutdown sequence
    if buttonB.value and not buttonA.value:  # lower button (23) pressed to command shutdown
        # grey out text other than shutdown
        L1[2] = GREY
        L2[2] = GREY
        L3[2] = GREY
        L4[2] = GREY
        L5[2] = GREY
        L6[2] = AMBER
        
        L6[1] = SHUT_txt[1]
        w6()
        
        # shutdown safely:
        FA_shut()
      
def FA_shut(): # shut down process initiated by lower button (23)
    # delete logfiles
    # start with main logfile
    global list_of_files
    global latest_file
    list_of_files = glob.glob('/home/pi/FortiusANT/pythoncode/FortiusAnt.*.log')
    latest_file = max(list_of_files, key=os.path.getctime)
    while len(list_of_files) != 0:
        os.remove(latest_file) #delete main logfile
        list_of_files = glob.glob('/home/pi/FortiusANT/pythoncode/FortiusAnt.*.log')
        if len(list_of_files) == 0:
            continue
        latest_file = max(list_of_files, key=os.path.getctime)
        
    # then look for GUI logfiles - note that these are generated by FortiusANT with -g argument
    # find latest GUI logfile
    list_of_GUI_files = glob.glob('/home/pi/FortiusANT/pythoncode/FortiusAntGUI.*.log')
    if len(list_of_GUI_files) != 0:
        latest_GUI_file = max(list_of_GUI_files, key=os.path.getctime)
    while len(list_of_GUI_files) != 0:
        os.remove(latest_GUI_file) #delete GUI logfile
        list_of_GUI_files = glob.glob('/home/pi/FortiusANT/pythoncode/FortiusAntGUI.*.log')
        if len(list_of_GUI_files) == 0:
            continue
        latest_GUI_file = max(list_of_GUI_files, key=os.path.getctime)
    
    # then empty Wastebasket to stop it filling up with (large) log files
    # keep a sensible number in case needed for fault finding
    # define number of files (in this case log files) to retain in Wastebasket (empty files from trash & info subdirectories)
    retain = 4

    list_of_files = glob.glob('/home/pi/.local/share/Trash/files/*.*')
    latest_file = max(list_of_files, key=os.path.getctime)
    list_of_info = glob.glob('/home/pi/.local/share/Trash/info/*.*')
    latest_info = max(list_of_info, key=os.path.getctime)

    while len(list_of_files) != retain:
        os.remove(latest_file) #delete oldest file in trash subdirectory
        list_of_files = glob.glob('/home/pi/.local/share/Trash/files/*.*')
        if len(list_of_files) == retain:
            continue
        latest_file = max(list_of_files, key=os.path.getctime)
    while len(list_of_info) != retain:
        os.remove(latest_info) #delete oldest file in info subdirectory
        list_of_info = glob.glob('/home/pi/.local/share/Trash/info/*.*')
        if len(list_of_info) == retain:
            continue
        latest_info = max(list_of_info, key=os.path.getctime)
        
    # show instruction to disconnect power:
    L6[1] = SHUT_txt[2]
    L6[2] = GREEN
    w6()
        
    call("sudo shutdown -h now", shell=True)
    # call("reboot", shell=True) to reboot instead
    
#-------------------------------------------------------------------------------
# SET UP DISPLAY - see https://learn.adafruit.com/adafruit-mini-pitft-135x240-color-tft-add-on-for-raspberry-pi/python-setup
# Part 1: define display and produce startup image
# configure CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# configuration for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# setup SPI bus using hardware SPI:
spi = board.SPI()

# create the ST7789 display (this is 240x240 version):
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=240,
    height=240,
    x_offset=0,
    y_offset=80,
)

# swap height/width to rotate it to landscape:
width = disp.width  
height = disp.height
    
image = Image.new("RGB", (width, height))

# get drawing object to draw on image:
draw = ImageDraw.Draw(image)

# draw a black filled box to clear the image:
##draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
##disp.image(image)

# define startup image:
image = Image.open("/home/pi/Fortius.jpg")

# scale the image to the smaller screen dimension:
image_ratio = image.width / image.height
screen_ratio = width / height
if screen_ratio < image_ratio:
    scaled_width = image.width * height // image.height
    scaled_height = height
else:
    scaled_width = width
    scaled_height = image.height * width // image.width
image = image.resize((scaled_width, scaled_height), Image.BICUBIC)

# crop and center the image:
x_jpg = scaled_width // 2 - width // 2
y_jpg = scaled_height // 2 - height // 2
image = image.crop((x_jpg, y_jpg, x_jpg + width, y_jpg + height))

# display image:
disp.image(image)
time.sleep(3.0)

#-------------------------------------------------------------------------------
# Part 2: display control text
# create blank image for drawing with mode 'RGB' for full color:
image = Image.new("RGB", (width, height))
rotation = 0

# get drawing object to draw on image:
draw = ImageDraw.Draw(image)

# draw a black filled box to clear the image:
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)

# define constants to allow easy resizing of shapes:
padding = -2
top = padding
bottom = height - padding
# move left to right keeping track of the current x position for drawing shapes:
x = 0

# load a TTF font - other good fonts available from: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)

# turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# define text to use and y position:
FA_txt = ("FortiusANT","FortiusAnt\n -waiting to start", "FortiusAnt-started",top)
CLOSE_txt = ("FortiusANT\n - already running", top)
TACX_txt = ("USB Connection", "USB connected", 50)
CAL_txt = ("Calibration","Calibration-start\n >turn pedals","Calibrating\n - don't pedal","Calibration\n - completed",75)
BLE_txt = ("Bluetooth","Bluetooth On","Bluetooth Off",125)
RUN_txt = ("Trainer","Trainer Running","Trainer stopped",150)
SHUT_txt = ("Shutdown\n> Press button 23","Shutting down\n please wait", "OK to cut power\nwhen green LED off",175)

# define colours to use:
WHITE = "#FFFFFF"
GREY = "#7A7A7A"
AMBER = "#fc8106"
GREEN = "#00EE00"
RED = "#FF3030"
BLACK = "#000000"

# initialise text by line (line 1 is L1 etc.)- lower 5 greyed out:
L1 = [FA_txt[3], FA_txt[0], WHITE]
L2 = [TACX_txt[2], TACX_txt[0], GREY]
L3 = [CAL_txt[4], CAL_txt[0], GREY]
L4 = [BLE_txt[3], BLE_txt[0], GREY]
L5 = [RUN_txt[3], RUN_txt[0], GREY]
L6 = [SHUT_txt[3], SHUT_txt[0], GREY]
w6()

# define buttons (button 24 is "upper" and button 23 is "lower"):
buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input()
buttonB.switch_to_input()

# define text to search for in log file to drive display:
log_txt = ["FortiusANT started",
          "Connected to Tacx Trainer T1932",
          "G I V E   A   P E D A L   K I C K",
          "C A L I B R A T I N G",
          "FortiusANT exchanges data with a bluetooth",
          "BLE-devices are activated",
          "Target=100W",
          "Stopped",
          "BLE-devices are deactivated"]
#-------------------------------------------------------------------------------
# MONITOR FORTIUSANT
# FortiusANT started separately in script (/home/pi/FortiusANT.sh). Monitor using log file in home/pi/FortiusANT/pythoncode.
# update display
L1[1] = FA_txt[1]
L1[2] = AMBER
L2[2] = GREY
L3[2] = GREY
L4[2] = GREY
L5[2] = GREY
L6[2] = GREY
w6()

# check if shutdown commanded
button23()

# define logfile to search for status information and keep looking until it is found
# look for specific FortiusAnt log file to ensure GUI log file (if present) not used
list_of_files = glob.glob('/home/pi/FortiusANT/pythoncode/FortiusAnt.*.log')
# wait for log file to be created while FortiusANT starts;
while len(list_of_files) == 0:
    lof = len(list_of_files)
    time.sleep(1.0)
    list_of_files = glob.glob('/home/pi/FortiusANT/pythoncode/FortiusAnt.*.log')
latest_file = max(list_of_files, key=os.path.getctime)

# get initial logfile data - use "with" to ensure the file closes after being read
for filename in glob.glob(latest_file):
    with open(filename, "r") as f:
        readfile = f.read()

# use i as counter
i = 0
# set refresh time (seconds)
t = 0.5

# Check for text in log file 
# FortiusANT started - check for specific text in log file
# update file, read contents as f and close file:
read_log()

while i == 0 and log_txt[i] not in readfile: # for i=0
    time.sleep(t)
    read_log()
    button23()
else:
    L1[1] = FA_txt[2]
    L1[2] = GREEN
    L2[2] = WHITE
    w6()
    button23()
    i += 1
# Tacx trainer connected loop - check if text found:
while i == 1 and log_txt[i] not in readfile: # for i=1
    time.sleep(t)
    read_log()
    button23()
else:
    L2[1] = TACX_txt[1]
    L2[2] = GREEN
    L3[2] = WHITE
    w6()
    button23()
    i += 1
# Calibration loop - check if text found:
while i == 2 and log_txt[i] not in readfile: # for i=2
    time.sleep(t)
    read_log()
    button23()
else:
    L3[1] = CAL_txt[1]
    L3[2] = AMBER
    L4[1] = BLE_txt[0]
    w6()
    button23()
    i += 1
while i == 3 and log_txt[i] not in readfile: # for i=3
    time.sleep(t)
    read_log()
    button23()
else:
    L3[1] = CAL_txt[2]
    L3[2] = AMBER
    w6()
    button23()
    i += 1
while i == 4 and log_txt[i] not in readfile: # for i=4
    time.sleep(t)
    read_log()
    button23()
else:
    L3[1] = CAL_txt[3]
    L3[2] = GREEN
    L4[2] = WHITE
    w6()
    button23()
    i += 1
# Bluetooth loop - check if text found
while i == 5 and log_txt[i] not in readfile: # for i=5
    time.sleep(t)
    read_log()
    button23()
else:
    L4[1] = BLE_txt[1]
    L4[2] = GREEN
    w6()
    button23()
    i += 1
# trainer running loop - check if text found
while i ==6 and log_txt[i] not in readfile: # for i=6
    time.sleep(t)
    read_log()
    button23()
else:
    L5[1] = RUN_txt[1]
    L5[2] = GREEN
    w6()
    button23()
    i += 1
while i == 7 and log_txt[i] not in readfile: # for i=7
    time.sleep(t)
    read_log()
    button23()
else:
    L4[1] = BLE_txt[2]
    L4[2] = RED
    w6()
    button23()
    i += 1
while i ==8 and log_txt[i] not in readfile: # for i=8
    time.sleep(t)
    read_log()
    button23()
else:
    L5[1] = RUN_txt[2]
    L5[2] = RED
    w6()
    button23()
    i += 1
# wait for shutdown command from button 23()
while True:
    button23()
    time.sleep(2.0)