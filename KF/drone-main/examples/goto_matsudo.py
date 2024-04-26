#!/usr/bin/env python3

import asyncio
from mavsdk import System

latitude = 35.7962735
longitude = 139.8916912
altitude = 2.233000040

async def run():
    drone = System()
    # await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
         
        # if health.is_global_position_ok and health.is_home_position_ok:
        if health.is_global_position_ok:
            print("-- Global position state is good enough for flying.")
            break

    print("holdモードにするで")
    await drone.action.hold()

    # Start parallel tasks
    print_altitude_task = asyncio.ensure_future(print_altitude(drone))
    print_flight_mode_task = asyncio.ensure_future(print_flight_mode(drone))

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

    await drone.action.goto_location(latitude, longitude, altitude, 0)
    print("-- goto始まったよ")

    # await drone.action.land()



    print("finished")

async def print_altitude(drone):
    """ Prints the altitude when it changes """

    previous_altitude = 0.0

    async for position in drone.telemetry.position():
        altitude = position.relative_altitude_m
        if abs(previous_altitude - altitude) >= 0.1:
            previous_altitude = altitude
            print(f"Altitude: {altitude}")


async def print_flight_mode(drone):
    """ Prints the flight mode when it changes """

    previous_flight_mode = None

    async for flight_mode in drone.telemetry.flight_mode():
        if flight_mode != previous_flight_mode:
            previous_flight_mode = flight_mode
            print(f"Flight mode: {flight_mode}")
        
    # while True:
    #     # print("Staying connected, press Ctrl-C to exit")
    #     async for flight_mode in drone.telemetry.flight_mode():
    #         print("FlightMode:", flight_mode)
        
    #     async for position in drone.telemetry.position():
    #         print("Altitude:",round(position.relative_altitude_m))

        
        



    #     await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(run())
