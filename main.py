import serial 
import time
import subprocess


#for justin's personal testing use.
# result = subprocess.run(args = ['java', '-jar', 'out/artifacts/wordhunthack_jar/wordhunthack.jar', grid],
#                         universal_newlines = True,
#                         stdout=subprocess.PIPE)

#for standard file structure

#com port should be changed based on usb port used.
#most likely error is that the com port is not updated
ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200)


ser.write(b"\r\n\r\n") # Wake up microcontroller
time.sleep(1)
ser.reset_input_buffer()

init_cmds = ["G28","M220 S1500", "M204 P6000 T6000", "M205 X30.0 Y30.0", "G0 X124.0 Y103.5 Z4.0"]
for command in init_cmds:
    if command.strip().startswith(';') or command.isspace() or len(command) <=0:
        continue
    else:
        ser.write((command+'\n').encode())
        while(1): # Wait untile the former gcode has been completed.
            if ser.readline().startswith(b'ok'):
                print("recieved ok")
                break


print("input grid")
grid = input();

result = subprocess.run(args = ['java', '-jar', 'wordhunthack.jar', grid],
                        universal_newlines = True,
                        stdout=subprocess.PIPE)

codeLines = result.stdout.splitlines()


wordCounter = 0
start = time.time()
for command in codeLines:
    if command.strip().startswith(';') or (time.time() - start) > 60 or command.isspace() or len(command) <=0:
        continue
    else:
        ser.write((command+'\n').encode())
        while(1): # Wait untile the former gcode has been completed.
            if ser.readline().startswith(b'ok'):
                print("recieved ok")
                break
        
                

ser.close() 
