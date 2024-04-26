import asyncio
import picamera
import cv2
import numpy as np
import datetime
from mavsdk import System
from logger import logger_info, logger_debug

altitude = 4
mode = None

async def run():

    drone = System()

    print("Waiting for drone to connect...")
    # await drone.connect(system_address="udp://:14540")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")

    
    logger_info.info("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            logger_info.info("-- Connected to drone!")
            break

    print("waiting for pixhawk to hold")
    arm_takeoff_task = asyncio.create_task(arm_takeoff(drone))
    await arm_takeoff_task

async def arm_takeoff(drone):
    logger_info.info("-- Arming")
    await drone.action.arm()
    logger_info.info("-- Armed")
    logger_info.info("-- Taking off")
    await drone.action.set_takeoff_altitude(altitude)
    await drone.action.takeoff()

    await asyncio.sleep(10)

    camera = picamera.PiCamera()
    logger_info.info('キャメラ初期化完了')

    file_path = '/home/pi/ARLISS_IBISIB/IB/Images/arliss_{}.jpg'.format(datetime.datetime.now())

    logger_info.info("taking pic...: {}".format(file_path))
    await asyncio.sleep(10)
    take_pic(camera,file_path) # 写真を撮る

    file_path = '/home/pi/ARLISS_IBIS/IB/Images/arliss_{}.jpg'.format(datetime.datetime.now())

    logger_info.info("taking pic...: {}".format(file_path))
    await asyncio.sleep(10)
    take_pic(camera,file_path) 
    
    file_path = '/home/pi/ARLISS_IBIS/IB/Images/arliss_{}.jpg'.format(datetime.datetime.now())

    logger_info.info("taking pic...: {}".format(file_path))
    await asyncio.sleep(10)
    take_pic(camera,file_path)

    await asyncio.sleep(60)
    await drone.action.land()

    

def take_pic(camera,file_path):
    camera.capture(file_path)



if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())




