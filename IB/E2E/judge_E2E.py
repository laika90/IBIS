import spidev               
import time                         
import sys    
import RPi.GPIO as GPIO
import asyncio
from mavsdk import System
from logger_E2E import logger_info
 
 
light_threshold = 250
is_landed = False
fuse_Pin = 3
fuse_time = 5.0
store_timelimit = 100
release_timelimit = 100
land_timelimit = 100


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

        if elapsed_time > store_timelimit:
            print("stored judge case 2")
            break

    print("#######################\n# stored judge finish #\n#######################")


def released_judge():
    print("########################\n# released judge start #\n########################")

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
            if light_val <= light_threshold:
                is_continue = False
                continue

            # 光の継続時間
            duration_time = time.perf_counter() - duration_start_time

            if duration_time > 10:
                print("released judge case 1")
                break
        
        elif light_val > light_threshold:
            is_continue = True
            duration_start_time = time.perf_counter()
        
        elapsed_time = time.perf_counter() - start_time

        if elapsed_time > release_timelimit:
            print("released judge case 2")
            break

    print("#########################\n# released judge finish #\n#########################")


async def connect_pixhawk():
    drone = System()
    logger_info.info("-- Waiting for drone to be connected...")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    
    async for state in drone.core.connection_state():
        if state.is_connected:
            logger_info.info("-- Connected to drone!")
            break
    
    logger_info.info("-- Throw the viecle")
    time.sleep(5)
    
    return drone


async def land_judge(drone):
    global is_landed
    logger_info.info("#########################\n# land judge start #\n#########################")
    start_time = time.time()
    while True:
        time_now = time.time()
        if time_now-start_time < 30:
            true_dist = IQR_removal(await alt_list(drone))
            try:
                ave = sum(true_dist)/len(true_dist)
            except ZeroDivisionError as e:
                logger_info.info(e)
                continue
            
            if await is_low_alt(ave):
                for distance in true_dist:
                    if abs(ave-distance) > 0.01:
                        logger_info.info("-- Moving")
                        break
                else:
                    is_landed = True
                    logger_info.info("-- Lidar Judge")
            else:
                logger_info.info("-- Over 1m")
                
        else:
            is_landed = True
            logger_info.info("-- Timer Judge")
            
        if is_landed:
            logger_info.info("-- Landed")
            break
    
    logger_info.info("#########################\n# land judge finish #\n#########################")
        
        
async def is_low_alt(alt):
    return alt < 1
        
        
async def alt_list(drone):
    distance_list = []
    iter = 0
    while True:
        try:
            distance = await asyncio.wait_for(get_distance_alt(drone), timeout = 0.8)
        except asyncio.TimeoutError:
            logger_info.info("Too high or lidar error")
            distance_list = []
            return distance_list
        iter += 1
        logger_info.info("altitude:{}".format(distance))
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
        logger_info.info(e)
        true_data= []
    return true_data


async def get_distance_alt(drone):
    async for distance in drone.telemetry.distance_sensor():
        return distance.current_distance_m


def fusing():
    try:
        logger_info.info("-- Fuse start")
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(fuse_Pin, GPIO.OUT)

        GPIO.output(fuse_Pin, 0)
        logger_info.info("-- Fusing")

        time.sleep(fuse_time)
        logger_info.info("-- Fused! Please Fly")

        GPIO.output(fuse_Pin, 1)
    
    except:
        GPIO.output(fuse_Pin, 1)


def run():

    drone = asyncio.get_event_loop().run_until_complete(connect_pixhawk())
    stored_judge()
    released_judge()
    asyncio.get_event_loop().run_until_complete(land_judge(drone))
    fusing()

    
    
if __name__ == "__main__":
    # SPI
    spi = spidev.SpiDev()     
    spi.open(0, 0)                    
    spi.max_speed_hz = 1000000 
    run()
    spi.close()
    sys.exit()