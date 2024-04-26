#!/usr/bin/env python3

import asyncio
from mavsdk import System

latitude = 47.397606
longitude = 8.543060
altitude = 20

async def run():
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    # await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    # print("Waiting for drone to have a global position estimate...")
    # async for health in drone.telemetry.health():
    #     if health.is_global_position_ok and health.is_home_position_ok:
    #         print("-- Global position state is good enough for flying.")
    #         break

    # print("Fetching amsl altitude at home location....")
    # async for terrain_info in drone.telemetry.home():
    #     absolute_altitude = terrain_info.absolute_altitude_m
    #     break

    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    await drone.action.takeoff()

    await asyncio.sleep(1)
    # To fly drone 20m above the ground plane
    # flying_alt = absolute_altitude + 20.0
    # goto_location() takes Absolute MSL altitude
    await drone.action.goto_location(latitude, longitude, altitude+5, 0)
    print("-- goto始まったよ")
    await drone.action.land()
    
    while True:
        # print("Staying connected, press Ctrl-C to exit")
        async for flight_mode in drone.telemetry.flight_mode():
            print("FlightMode:", flight_mode)
        
        async for position in drone.telemetry.position():
            print("Altitude:",round(position.relative_altitude_m))

        
        



        await asyncio.sleep(1)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
