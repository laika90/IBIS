import re
import serial
import time
import RPi.GPIO as GPIO

lorapin = 4

GPIO.setmode(GPIO.BCM)

GPIO.setup(lorapin, GPIO.OUT)

GPIO.output(lorapin, 1)
        
while True:
    try:
        ser = serial.Serial('/dev/ttyS0', 115200, timeout=3)
    except:
        print ("Serial port error. Waiting.")
        time.sleep(5)
    else:
        break
print ("Serial port OK.")

ser.write(b'2\r\n')
time.sleep(1)
ser.write(b'z\r\n')
time.sleep(1)

ser.write(("Let's GO\r\n").encode())

print("READY")

while True:
    
    bufw=input()
    ser.write((bufw+"\r\n").encode())
