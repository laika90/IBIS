import spidev               
import time                         
import sys    
import RPi.GPIO as GPIO
from logger import logger_info

PIN = 5
light_threshold = 250

# 連続して値を読み込む
def get_light_val():
    resp = spi.xfer2([0x68, 0x00])                 
    value = ((resp[0] << 8) + resp[1]) & 0x3FF    
    return value

def stored_judge():
    print("######################\n# stored judge start #\n######################")

    # 関数の開始時間
    start_time = time.perf_counter()
    # 光の継続時間
    duration_start_time = time.perf_counter()
    is_continue = False

    while True:


        light_val = get_light_val()
        time_stamp = time.perf_counter() - duration_start_time
        print("{:5.1f}| 光センサ:{:>3d}, 継続:{}".format(time_stamp, light_val, is_continue))

        if is_continue:
            # 光が途切れていた場合、やり直し
            if light_val >= light_threshold:
                is_continue = False
                continue

            # 光の継続時間
            duration_time = time.perf_counter() - duration_start_time

            if duration_time > 10:
                print("stored judge case 1")
                break
        
        elif light_val < light_threshold:
            is_continue = True
            duration_start_time = time.perf_counter()
        
        elapsed_time = time.perf_counter() - start_time

        if elapsed_time > 120:
            print("stored judge case 2")
            break

    print("#######################\n# stored judge finish #\n#######################")


def fusing():
    try:
        logger_info.info("-- Fuse start")
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(PIN, GPIO.OUT)

        GPIO.output(PIN, 1)
        logger_info.info("-- Fusing")

        time.sleep(2.0)
        logger_info.info("-- Fused! Please Fly")

        GPIO.output(PIN, 0)
    
    except:
        GPIO.output(PIN, 0)

        

if __name__ == "__main__":
    # SPI
    spi = spidev.SpiDev()     
    spi.open(0, 0)                    
    spi.max_speed_hz = 1000000 

    stored_judge()
    # fusing()

    spi.close()
    sys.exit()
    
    