#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 by Satoshi Takahashi, all right reserved.
# https://s-taka.org/
# BSD 2-clause license

import re
import serial
import sys
import threading
import time

device='/dev/ttyS0'                # Raspberry Pi

while True:
    try:
        ser = serial.Serial(device,19200,timeout=1)
    except:
        print ("Serial port error. Waiting.")
        time.sleep(5)
    else:
        break
print ("Serial port OK. Waiting for reset.")

class reception(threading.Thread):
    def __init__(self):
        super(reception, self).__init__()
        self.stop_event = threading.Event()
        self.setDaemon(True)
    def stop(self):
        self.stop_event.set()
    def run(self):
        while True:
            buf = ser.readline()
            if buf == b'': continue
            if buf.decode().find('send failed bacause now sending packet\r\n')!=-1:
                print("データ送信中です。")
            elif buf.decode().find('carrier sense failed\r\n')!=-1:
                print("キャリヤセンスに失敗しました。")
            elif buf.decode().find('send data length too long\r\n')!=-1:
                print("送信文字列が長すぎます。")
            else:
                m=re.search(r"(-[0-9.]+).*Data\((.*)\)", buf.decode());
                if m: print("receive: " + m.group(2))

while True:
    buf = ser.readline()
    if buf == b'': continue
    print (buf.decode('utf-8','replace').strip())
    if buf == b'Select Mode [1.terminal or 2.processor]\r\n': break
ser.write(b'1\r\n')

while True:
    buf = ser.readline()
    if buf == b'': continue
    print (buf.decode().strip())
    if buf.decode().find('LORA')!=-1: break
ser.write(b'z\r\n')

while True:
    buf = ser.readline()
    if buf == b'': break
    print (buf.decode().strip())

thread=reception()
thread.start()

print("Ready.")

while True:
    buf = input()
    ser.write((buf+'\r\n').encode())
    if buf == 'quit':
        print("Bye.")
        break

thread.stop()
ser.close()

# EOF