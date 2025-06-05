import cv2
import pytesseract
import numpy as np
from statistics import median
import imutils
from picamera2 import Picamera2
import serial 
import time
import subprocess

# For button and LCD screen
from gpiozero import OutputDevice
from gpiozero import Button
from time import sleep

LCD_RS = OutputDevice(25)
LCD_E = OutputDevice(24)
LCD_D4 = OutputDevice(23)
LCD_D5 = OutputDevice(18)
LCD_D6 = OutputDevice(15)
LCD_D7 = OutputDevice(14)
button = Button(4, pull_up=False)

LCD_WIDTH = 16
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0

E_PULSE = 0.0005
E_DELAY = 0.0005

# Functions for button and LCD display
def lcd_init():
	lcd_byte(0x33, LCD_CMD)
	lcd_byte(0x32, LCD_CMD)
	lcd_byte(0x28, LCD_CMD)
	lcd_byte(0x0C, LCD_CMD)
	lcd_byte(0x06, LCD_CMD)
	lcd_byte(0x01, LCD_CMD)
	sleep(E_DELAY)
	
def lcd_byte(bits, mode):
	LCD_RS.value = mode
	
	LCD_D4.off()
	LCD_D5.off()
	LCD_D6.off()
	LCD_D7.off()
	
	if bits & 0x10:
		LCD_D4.on()
	if bits & 0x20:
		LCD_D5.on()
	if bits & 0x40:
		LCD_D6.on()
	if bits & 0x80:
		LCD_D7.on()
	
	lcd_toggle_enable()
	
	LCD_D4.off()
	LCD_D5.off()
	LCD_D6.off()
	LCD_D7.off()
	
	if bits & 0x01:
		LCD_D4.on()
	if bits & 0x02:
		LCD_D5.on()
	if bits & 0x04:
		LCD_D6.on()
	if bits & 0x08:
		LCD_D7.on()
	
	lcd_toggle_enable()

def lcd_toggle_enable():
	sleep(E_DELAY)
	LCD_E.on()
	sleep(E_PULSE)
	LCD_E.off()
	sleep(E_DELAY)

def lcd_string(message, line):
	message = message.ljust(LCD_WIDTH, " ")
	
	lcd_byte(line, LCD_CMD)
	
	for i in range(LCD_WIDTH):
		lcd_byte(ord(message[i]), LCD_CHR)

# Start of WordHunt code
ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200)


ser.write(b"\r\n\r\n") # Wake up microcontroller
time.sleep(1)
ser.reset_input_buffer()

init_cmds = ["G28","M220 S2000", "M204 P13000 T13000", "M205 X40.0 Y40.0", "G0 Z2.0", "G0 X130.0 Y98.0", "G0 Z26.0"]
for command in init_cmds:
    if command.strip().startswith(';') or command.isspace() or len(command) <=0:
        continue
    else:
        ser.write((command+'\n').encode())
        while(1): # Wait untile the former gcode has been completed.
            if ser.readline().startswith(b'ok'):
                print("recieved ok")
                break

# time.sleep(7)

button.wait_for_press()
print("Button pressed")

print("should be relocated")

picam2 = Picamera2()

picam2.start()
image = picam2.capture_array()

start = time.time()

print("Picture taken")
lcd_init()
# Convert to YCrCb color space
ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)

# Define the lower and upper bounds for the color mask
lower_scalar = np.array([94.9, 0.0, 100.6])
upper_scalar = np.array([233.8, 249.3, 192.7])

# mask
# mask = cv2.inRange(ycrcb, lower_scalar, upper_scalar)
thresh = cv2.inRange(ycrcb, lower_scalar, upper_scalar)

# --------------------------------------------------------------------------

img = image.copy()
# contours, _ = cv2.findContours(...) # Your call to find the contours using OpenCV 2.4.x
contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) # Your call to find the contours

filt_cont = []

for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    # Calculate the aspect ratio
    area = cv2.contourArea(contour)
    perim = cv2.arcLength(contour, True)


    if perim == 0:  # Avoid division by zero
            continue
    
    circ = (4 * np.pi * area) / (perim ** 2)
    aspect_ratio = w / float(h)
    # Filter for square-like contours based on aspect ratio and size
    if 0.90<= aspect_ratio <= 1.1 and w > 65 and circ < 9.0:
        filt_cont.append(contour)

cv2.drawContours(img, filt_cont, -1, (255,0,0), 7)

filt_cont.reverse()
print(len(filt_cont))

final_string = ""
box_index = 1

data = []

for minibox in filt_cont:
    x,y,w,h = cv2.boundingRect(minibox)
    print(x, y, w, h)
    avg_side = (w + h)/2
    modif = int(avg_side * .1)
    crop_img = thresh[(y+modif):(y+h-modif), (x+modif):(x+w-modif)]
    #cv2.imshow("crop_img", crop_img)
    letter_detect = pytesseract.image_to_string(crop_img, config='--psm 10 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    if len(letter_detect) == 0:
        letter_detect ='?'
    else:
        letter_detect = letter_detect[0]
        if letter_detect == '|':
            letter_detect = 'I'
        elif letter_detect == '0':
            letter_detect = 'O'
    #cv2.imwrite("letterIMGs/letter" + str(box_index) +".jpg", crop_img)
    #cv2.waitKey(0)
    box_index += 1 
    data.append([letter_detect, x, y]) 
    
data.sort(key=lambda x: x[2])

sorted_data = []
for i in range(0, 16, 4):
    group = data[i:i +4]
    group.sort(key=lambda x:x[1])
    sorted_data.extend(group)

for thr in sorted_data:
    final_string = final_string + thr[0]
    
print(final_string)

lcd_string(final_string, LCD_LINE_1)
lcd_string("choose mode", LCD_LINE_2)
mode = input()
if mode == "2":
	pointer = "^"
	lcd_string(final_string, LCD_LINE_1)
	lcd_string(pointer, LCD_LINE_2)
	while True:
		inpt = input()
		print(inpt)
		if inpt == "":
			break
		elif inpt == '>':
			pointer = " " + pointer
		elif inpt == '<' and len(pointer) > 1:
			pointer = pointer[1:]
		elif '<' in inpt:
			continue
		elif '>' in inpt:
			continue
		else:
			idx = len(pointer)-1
			final_string = final_string[:idx] + inpt + final_string[idx + 1:]

		lcd_string(final_string, LCD_LINE_1)
		lcd_string(pointer, LCD_LINE_2)
		
elif mode == "1":
	lcd_string(final_string, LCD_LINE_1)
	lcd_string("", LCD_LINE_2)
	while True:
		inpt = input()
		print(inpt)
		if inpt == "":
			break
		else:
			idx = final_string.index("?")
			final_string = final_string[:idx] + inpt + final_string[idx + 1:]

		lcd_string(final_string, LCD_LINE_1)

result = subprocess.run(args = ['java', '-jar', 'wordhunthack.jar', final_string],
                        universal_newlines = True,
                        stdout=subprocess.PIPE)

codeLines = result.stdout.splitlines()


ser.write(('G0 X124.0 Y103.0 Z1.5\n').encode())
time.sleep(5.47)


wordCounter = -1

for command in codeLines:
    if command.strip().startswith(';') or time.time()-start > 85 or command.isspace() or len(command) <=0:
        continue
    elif ';' in command:
        arr = command.split('; ')
        lcd_string(arr[1], LCD_LINE_1)
        lcd_string("Words: " + str(int(wordCounter)), LCD_LINE_2)
        wordCounter += 0.5
        print(arr)
        ser.write((command+'\n').encode())
        while(1): # Wait untile the former gcode has been completed.
            if ser.readline().startswith(b'ok'):
                print("recieved ok")
                break
    else:
        ser.write((command+'\n').encode())
        while(1):# Wait untile the former gcode has been completed.
            if ser.readline().startswith(b'ok'):
                print("recieved ok")
                break
                
print("End of commands")
for command in codeLines:
    print(str(command) + "\n")

print("if it gets here something went wrong")
ser.close() 
