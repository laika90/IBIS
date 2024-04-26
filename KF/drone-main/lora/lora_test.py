#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 by Satoshi Takahashi, all right reserved.
# https://s-taka.org/
# BSD 2-clause license

import re
import serial
import time

device='/dev/ttyAMA0'            # Raspberry Pi

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
    buf = ser.readline()
    if buf == b'': 
        # print("nanimonaiyo")
        continue
    print (buf.decode('utf-8','replace').strip())
    if buf == b"Select Mode [1.terminal or 2.processor]\r\n": 
        break
ser.write(b'1\r\n')


while True:
    buf = ser.readline()
    if buf == b'': 
        continue
    print (buf.decode().strip())
    if buf.decode().find('LORA')!=-1: 
        break
ser.write(b'z\r\n')

while True:
    buf = ser.readline()
    if buf == b'': break
    print (buf.decode().strip())

print("Ready.")

while True:
    
    bufw=input()
    ser.write((bufw+"\r\n").encode())

    # bufr = ser.readline()
    # if bufr == b'': 
    #     continue
    # print(bufr)

# while True:
#     buf = ser.readline()
#     if buf == b'': 
#         continue
#     m=re.search(r"(-[0-9.]+).*Data\((.*)\)", buf.decode());
#     if m:
#         time.sleep(0.1)
#         buf=m.group(2) + " (" + m.group(1) + " dBm)"
#         print("send: " + buf)
#         ser.write((buf+"\r\n").encode())
#         if m.group(2) == 'quit':
#             print("Bye.")
#             break

# ser.close()

# EOF