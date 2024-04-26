#!/usr/bin/env python3

import asyncio
import sys
from mavsdk import System
import time


async def run():
    # Init the drone
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    # await drone.connect(system_address="udp://:14540")
    print("waiting for conection...")
    async for state in drone.core.connection_state():
        if state.is_connected : 
            print("rpi<->pix connection : OK")
            break
    print("waiting for GPS health...")
    gps_time = time.process_time()
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("GPS health : OK")
            gps_time = time.process_time() - gps_time
            print("It took " + str(gps_time) + "sec to check GPS")
            break
    print("Everything is OK. Let's Fly!")

    # Start the tasks
    # asyncio.ensure_future(print_battery(drone))
    # asyncio.ensure_future(print_in_air(drone))

# async def print_battery(drone):
#     async for battery in drone.telemetry.battery():
#         print(f"Battery: {battery.remaining_percent}")



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    sys.exit()
