import re
import serial
import time

device='/dev/ttyS0'            # Raspberry Pi

while True:
    try:
        ser = serial.Serial(device,19200,timeout=1)
    except:
        print ("Serial port error. Waiting.")
        time.sleep(5)
    else:
        break
print ("Serial port OK. Waiting for reset.")

while True:
    bf = ser.readline()
    print(bf.decode())