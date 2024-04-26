import asyncio
import csv
import datetime
from mavsdk import System
from logger import logger_info, logger_debug
import atexit

latitude_list = []
longitude_list = []
lidar_list = []
alt_list = []
center_lat_deg = 0
center_lng_deg = 0
center_abs_alt = 0

async def run():
    
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")

    print("Waiting for drone to connect...")
    logger_info.info("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            logger_info.info("-- Connected to drone!")
            break
    task1=asyncio.create_task(get_position(drone))
    task2=asyncio.create_task(get_csv_list(drone))
    await task1
    asyncio.sleep(1)
    await task2
async def get_position(drone):
    async for position in drone.telemetry.position():
        global center_lat_deg,center_lng_deg,center_abs_alt
        center_lat_deg = position.latitude_deg
        center_lng_deg = position.longitude_deg
        center_abs_alt = position.absolute_altitude_m
        break
    
async def get_csv_list(drone):
     while True:
        async for position in drone.telemetry.position():
            latitude_list.append(position.latitude_deg)
            longitude_list.append(position.longitude_deg)
            abs_alt = position.absolute_altitude_m
            rel_alt = abs_alt - center_abs_alt
            alt_list.append(rel_alt)
            break
        async for distance in drone.telemetry.distance_sensor():
            lidar_list.append(distance.current_distance_m)
            break

@atexit.register
def get_csv():
    dt_now = datetime.datetime.now()
    with open(f"/home/pi/ARLISS_IBIS/log/log_csv/goto_2_waypoints {dt_now}.csv","w") as file:
        writer = csv.writer(file)
        writer.writerow(latitude_list)
        writer.writerow(longitude_list)
        writer.writerow(alt_list)
        writer.writerow(lidar_list)
asyncio.run(run())