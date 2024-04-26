import RPi.GPIO as GPIO

SWITCH_PIN = 3

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(SWITCH_PIN, GPIO.OUT)
GPIO.output(SWITCH_PIN, 0)
# GPIO.output(SWITCH_PIN, 1)

result = GPIO.input(SWITCH_PIN) # ピンの値を読み取る(HIGH or LOWの1 or 0)
print(result)