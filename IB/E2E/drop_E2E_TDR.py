import asyncio
from mavsdk import System
import time
import RPi.GPIO as GPIO
from logger_E2E import logger_info

is_landed = False
PIN = 5

# 審査会でGPS取れるなら
async def run():
    drone = System()
    logger_info.info("-- Waiting for drone to be connected...")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    
    async for state in drone.core.connection_state():
        if state.is_connected:
            logger_info.info("-- Connected to drone!")
            break
        
    # alt_task = asyncio.create_task(print_alt(drone))
    # land_judge_task = asyncio.create_task(land_judge(drone))
    
    logger_info.info("-- Throw the viecle")
    time.sleep(5)
    
    # await alt_task
    # await land_judge_task
    await land_judge(drone)
    
    fusing()


async def land_judge(drone):
    global is_landed
    logger_info.info("####### Land judge start #######")
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
    
    logger_info.info("####### Land judge finish #######")

        
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


# async def print_alt(drone):
#     while True:
#         if is_landed:
#             return
#         else:
#             try:
#                 await asyncio.wait_for(positin_alt(drone), timeout = 0.8)
#             except asyncio.TimeoutError:
#                 pass
#             logger_info.info("altitude:{}".format(position))
#             break
#         await asyncio.sleep(0)


async def get_distance_alt(drone):
    async for distance in drone.telemetry.distance_sensor():
        return distance.current_distance_m


# async def get_position_alt(drone):
#     async for position in drone.telemetry.position():
#         return position.absolute_altitude


def fusing():
    try:
        logger_info.info("-- Fuse start")
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(PIN, GPIO.OUT)

        GPIO.output(PIN, 0)
        logger_info.info("-- Fusing")

        time.sleep(5.0)
        logger_info.info("-- Fused! Please Fly")

        GPIO.output(PIN, 1)
    
    except:
        GPIO.output(PIN, 1)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())
