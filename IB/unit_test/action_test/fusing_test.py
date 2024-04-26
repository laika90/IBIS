#timeモジュールをインポート
import time

#RPi.GPIOモジュールをインポート
import RPi.GPIO as GPIO

PIN = 3

def fusing():
    # BCM(GPIO番号)で指定する設定
    try:
        print("-- Start")
        time.sleep(3)
        GPIO.setmode(GPIO.BCM)

        # GPIO26を出力モード設定
        GPIO.setup(PIN, GPIO.OUT)

        # GPIO26の出力を1にして、LED点灯
        GPIO.output(PIN, 0)
        print("-- Fusing")

        # 0.5秒待つ
        time.sleep(5.0)
        print("-- Fused! Please Fly")

        # GPIO17の出力を0にして、LED消灯
        GPIO.output(PIN, 1)
        
        # GPIO.cleanup()
        
    
    except:
        # GPIO設定クリア
        GPIO.output(PIN, 1)

if __name__ == "__main__":
    fusing()