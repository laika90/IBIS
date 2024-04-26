import spidev     
import asyncio          
import time                         
import sys    
import RPi.GPIO as GPIO
import picamera
from mavsdk import System
import serial
import datetime


fuse_Pin = 3
lora_power_pin = 4
light_threshold = 400

lora_sleep_time = 3
fuse_time = 3.0
stored_timelimit = 15
stored_judge_time = 5
released_timelimit = 15
released_judge_time = 5
land_timelimit = 15

is_landed = False 


async def drone_connect():
    
    drone = System()
    print("-- Waiting for drone to be connected...")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("-- Connected to drone!")
            break
    
    return drone
    
    
async def serial_connect():
    
    connect_counter = 0
    while True:
        try:
            lora = serial.Serial('/dev/ttyS0', 115200, timeout=1)
        except:
            print("Serial port error. Waiting.")
            connect_counter += 1
            if connect_counter >= 100:
                break
            await asyncio.sleep(3)
        else:
            break
    print("Serial port OK.")
    operation_write(lora)
    await write(lora, ("Lora start").encode())
    print("Lora READY")
    return lora


async def write(lora, message: str):
    
    msg_send = str(message) + "\r\n"
    lora.write(msg_send.encode("ascii"))
    time.sleep(lora_sleep_time)
    
    
def operation_write(lora):
    
    lora.write(b'2\r\n')
    time.sleep(1)
    lora.write(b'z\r\n')
    time.sleep(1)
    
    
def get_light_val():
    
    resp = spi.xfer2([0x68, 0x00])                 
    value = ((resp[0] << 8) + resp[1]) & 0x3FF    
    return value


async def stored_judge(lora):
    
    await write(lora, "stored judge start")
    print("######################\n# stored judge start #\n######################")

    start_time = time.perf_counter()
    duration_start_time = time.perf_counter()
    is_continue = False

    while True:


        light_val = get_light_val()
        time_stamp = time.perf_counter() - duration_start_time
        print("{:5.1f}| 光センサ:{:>3d}, 継続:{}".format(time_stamp, light_val, is_continue))

        if is_continue:
            if light_val >= light_threshold:
                is_continue = False
                continue

            duration_time = time.perf_counter() - duration_start_time

            if duration_time > stored_judge_time:
                print("-- Light Judge")
                break
        
        elif light_val < light_threshold:
            is_continue = True
            duration_start_time = time.perf_counter()
        
        elapsed_time = time.perf_counter() - start_time

        if elapsed_time > stored_timelimit:
            print("-- Timer Judge")
            break

    await write(lora, "stored judge finish")
    print("#######################\n# stored judge finish #\n#######################")


async def released_judge(lora):
    
    await write(lora, "released judge start")
    print("########################\n# released judge start #\n########################")

    start_time = time.perf_counter()
    duration_start_time = time.perf_counter()
    is_continue = False


    while True:

        light_val = get_light_val()
        time_stamp = time.perf_counter() - duration_start_time
        print("{:5.1f}| 光センサ:{:>3d}, 継続:{}".format(time_stamp, light_val, is_continue))

        if is_continue:
            if light_val <= light_threshold:
                is_continue = False
                continue

            duration_time = time.perf_counter() - duration_start_time

            if duration_time > released_judge_time:
                print("-- Light Judge")
                break
        
        elif light_val > light_threshold:
            is_continue = True
            duration_start_time = time.perf_counter()
        
        elapsed_time = time.perf_counter() - start_time

        if elapsed_time > released_timelimit:
            print("-- Timer Judge")
            break

    await write(lora, "released judge finish")
    print("#########################\n# released judge finish #\n#########################")


async def land_judge(lora, drone):
    
    await write(lora, "land judge start")
    global is_landed
    print("#########################\n# land judge start #\n#########################")
    start_time = time.time()
    while True:
        time_now = time.time()
        if time_now-start_time < land_timelimit:
            true_dist = IQR_removal(await alt_list(drone))
            try:
                ave = sum(true_dist)/len(true_dist)
            except ZeroDivisionError as e:
                print(e)
                continue
            
            if await is_low_alt(ave):
                for distance in true_dist:
                    if abs(ave-distance) > 0.01:
                        print("-- Moving")
                        break
                else:
                    is_landed = True
                    print("-- Lidar Judge")
            else:
                print("-- Over 1m")
                
        else:
            is_landed = True
            print("-- Timer Judge")
            
        if is_landed:
            print("-- Landed")
            break
    
    await write(lora, "land judge finish")
    print("#########################\n# land judge finish #\n#########################")
    
        
async def is_low_alt(alt):
    
    return alt < 1
        
        
async def alt_list(drone):
    
    distance_list = []
    iter = 0
    while True:
        try:
            distance = await asyncio.wait_for(get_distance_alt(drone), timeout = 0.8)
        except asyncio.TimeoutError:
            print("Too high or lidar error")
            distance_list = []
            return distance_list
        iter += 1
        print("altitude:{}".format(distance))
        distance_list.append(distance)
        await asyncio.sleep(0)
        if iter >= 30:
            break
    return distance_list


def IQR_removal(data):
    
    try:
        data.sort()
        quartile_25 = data[7]
        quartile_75 = data[23]
        IQR = quartile_75-quartile_25
        true_data = [i for i in data if quartile_25-1.5*IQR <= i <= quartile_75+1.5*IQR]
    except IndexError as e:
        print(e)
        true_data= []
    return true_data


async def get_distance_alt(drone):
    
    async for distance in drone.telemetry.distance_sensor():
        return distance.current_distance_m


async def fusing():
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(fuse_Pin, GPIO.OUT, initial=GPIO.HIGH)
        print("-- Fuse start")

        GPIO.output(fuse_Pin, 0)
        print("-- Fusing")

        await asyncio.sleep(fuse_time)
        print("-- Fused! Please Fly")

        GPIO.output(fuse_Pin, 1)
    
    except:
        GPIO.output(fuse_Pin, 1)

    
class Camera:
    
    def __init__(self):
        self.camera = picamera.PiCamera()
        print('キャメラ初期化完了')
    
    def take_pic(self, file_path):
        self.camera.capture(file_path)
        
    
async def camera_check():
    camera = Camera()
    
    file_path = '/home/pi/ARLISS_IBIS/IB/Images/image_test{}.jpg'.format(datetime.datetime.now())

    print("taking pic...: {}".format(file_path))
    camera.take_pic(file_path) # 写真を撮る
    

async def unit_test():
    
    drone = await drone_connect()
    lora = await serial_connect()
    
    await stored_judge(lora)
    await released_judge(lora)
    await land_judge(lora, drone)
    await fusing()
    await camera_check()
    
    
if __name__ == "__main__":
    
    spi = spidev.SpiDev()     
    spi.open(0, 0)                    
    spi.max_speed_hz = 1000000 
    
    asyncio.run(unit_test())
    
    spi.close()
    sys.exit()