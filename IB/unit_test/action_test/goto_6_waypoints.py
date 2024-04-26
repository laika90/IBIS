#!/usr/bin/env python3
import asyncio
import csv
import datetime
from mavsdk import System
from logger import logger_info, logger_debug
import atexit
import math as m

side_length = 5
lat_deg_per_m = 0.000008983148616
lng_deg_per_m = 0.000008983668124
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

    get_log_task = asyncio.ensure_future(get_log(drone))
    get_gps_list_task = asyncio.ensure_future(get_csv_list(drone,latitude_list,longitude_list))
    
    print("Waiting for drone to have a global position estimate...")
    logger_info.info("Waiting for drone to have a global position estimate...")
    
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            logger_info.info("-- Global position estimate OK")
            break
    
    async for position in drone.telemetry.position():
        center_lat_deg = position.latitude_deg
        center_lng_deg = position.longitude_deg
        center_abs_alt = position.absolute_altitude_m
        break
    
    center = [center_lat_deg, center_lng_deg]
    waypoint1 = [center[0] + lat_deg_per_m * side_length, center[1]]
    waypoint2 = [center[0] - lat_deg_per_m * side_length * m.cos(36*m.pi/180),center[1] + lng_deg_per_m * side_length * m.sin(36*m.pi/180)]
    waypoint3 = [center[0] + lat_deg_per_m * side_length * m.sin(18*m.pi/180),center[1] - lng_deg_per_m * side_length * m.cos(18*m.pi/180)]
    waypoint4 = [center[0] + lat_deg_per_m * side_length * m.sin(18*m.pi/180),center[1] + lng_deg_per_m * side_length * m.cos(18*m.pi/180)]
    waypoint5 = [center[0] - lat_deg_per_m * side_length * m.cos(36*m.pi/180),center[1] - lng_deg_per_m * side_length * m.sin(36*m.pi/180)]
    waypoint6 = [center[0] + lat_deg_per_m * side_length, center[1]]

    if center == [0, 0]:
        print("No center GPS")
    else:
        print(f"center GPS:{center}")
    
    print("-- Arming")
    logger_info.info("-- Arming")
    await drone.action.arm()

    await get_log_task
    await get_gps_list_task

    print("-- Taking off")
    logger_info.info("-- Taking off")
    # await drone.action.set_takeoff_altitude(3)
    await drone.action.takeoff()
    await asyncio.sleep(2)

    

    
    
    
    
    await drone.action.goto_location(waypoint1[0], waypoint1[1],center_abs_alt+4,162)
    print("-- reached 1st. waypoint")
    logger_info.info("-- reached 1st. waypoint")
    await drone.action.goto_location(waypoint2[0], waypoint2[1],center_abs_alt+5,306)
    print("-- reached 2nd. waypoint")
    logger_info.info("-- reached 2nd. waypoint")
    await drone.action.goto_location(waypoint3[0], waypoint3[1],center_abs_alt+4,90)
    print("-- reached 3rd. waypoint")
    logger_info.info("-- reached 3rd. waypoint")
    await drone.action.set_maximum_speed(5)
    await drone.action.goto_location(waypoint4[0], waypoint4[1],center_abs_alt+5,234)
    print("-- reached 4th. waypoint")
    logger_info.info("-- reached 4th. waypoint")
    await drone.action.goto_location(waypoint5[0], waypoint5[1],center_abs_alt+4,18)
    print("-- reached 5th. waypoint")
    logger_info.info("-- reached 5th. waypoint")
    await drone.action.goto_location(waypoint6[0], waypoint6[1],center_abs_alt+5,18)
    print("-- reached 6th. waypoint")
    logger_info.info("-- reached 6th. waypoint")
    print("-- Landing")
    logger_info.info("-- Landing")
    await drone.action.land()


async def observe_is_in_air(drone, running_tasks):
    """ Monitors whether the drone is flying or not and
    returns after landing """

    was_in_air = False
    async for is_in_air in drone.telemetry.in_air():
        if is_in_air:
            was_in_air = is_in_air

        if was_in_air and not is_in_air:
            for task in running_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            await asyncio.get_event_loop().shutdown_asyncgens()

            return
    
async def get_log(drone):
    async for flight_mode in drone.telemetry.flight_mode():
        mode = flight_mode
        break
    async for distance in drone.telemetry.distance_sensor():
        lidar = distance.current_distance_m
        break
    async for position in drone.telemetry.position():
        abs_alt = position.absolute_altitude_m
        rel_alt = position.relative_altitude_m
        break
    async for speed in drone.action.get_maxium_speed():
        max_speed  = speed
        break
    while True:
        log_txt = (
            + " mode:"
            + str(mode)
            + " lidar: "
            + str(lidar)
            + "m"
            + " abs_alt:"
            + str(abs_alt)
            + "m"
            + " rel_alt:"
            + str(rel_alt)
            + "m"
            + " max_speed:"
            +str(max_speed)
            + "m/s"
            )
        logger_info.info(str(log_txt))
        await asyncio.sleep(0.3)

async def get_csv_list(drone,latitude_list,longitude_list,lidar_list,alt_list):
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
    with open(f"/home/pi/ARLISS_IBIS/log/log_csv/goto_6_waypoints {dt_now}.csv","w") as file:
        writer = csv.writer(file)
        writer.writerow(latitude_list)
        writer.writerow(longitude_list)
        writer.writerow(alt_list)
        writer.writerow(lidar_list)

