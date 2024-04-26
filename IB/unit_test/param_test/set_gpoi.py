# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO

SWITCH_PIN = 3 # ピン番号

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
# GPIO.setup(SWITCH_PIN, GPIO.OUT, initial=GPIO.HIGH)   # プルアップの場合
# GPIO.setup(SWITCH_PIN, GPIO.OUT, initial=GPIO.LOW)  # プルダウンの場合
GPIO.setup(SWITCH_PIN, GPIO.OUT)  # デフォルトを見たい場合

result = GPIO.input(SWITCH_PIN) # ピンの値を読み取る(HIGH or LOWの1 or 0)
print(result)