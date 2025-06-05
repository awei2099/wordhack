from gpiozero import OutputDevice, Button, RotaryEncoder
import RPi.GPIO as GPIO
from time import sleep

LCD_RS = OutputDevice(25)
LCD_E = OutputDevice(24)
LCD_D4 = OutputDevice(23)
LCD_D5 = OutputDevice(18)
LCD_D6 = OutputDevice(15)
LCD_D7 = OutputDevice(14)
button = Button(4, pull_up=False)


alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
current_index = 0
mode_index = 0
modes = '123'


rotor = RotaryEncoder(16,20, max_steps=25)
def update_letter(delta):
	global current_index
	if rotor.steps > 0:
		current_index = (current_index + 1) % len(alphabet)
	elif rotor.steps <0 :
		current_index = (current_index - 1) % len(alphabet)
	rotor.steps = 0
	
def update_mode(delta):
	global mode_index
	if rotor.steps > 0:
		mode_index = (mode_index + 1) % len(modes)
	elif rotor.steps < 0:
		mode_index = (mode_index - 1) % len(modes)
	rotor.steps = 0
LCD_WIDTH = 16
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0

E_PULSE = 0.0005
E_DELAY = 0.0005

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

lcd_init()
final_string = "AU??AE??AE??AE??"
lcd_string(final_string, LCD_LINE_1)



mode_str = 'choose mode'
lcd_string(mode_str, LCD_LINE_2)

rotor.when_rotated = update_mode
button.wait_for_press()
mode = modes[mode_index]
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
	final_string = "AU??AE??AE??AE??"
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


	
	
