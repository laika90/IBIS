#!/usr/bin/env python3

import asyncio
from mavsdk import System


async def run():
    # Init the drone
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    print("connected")

    # Start the tasks
    asyncio.ensure_future(print_position(drone))

    while True:
        await asyncio.sleep(1)


async def print_position(drone):
    async for position in drone.telemetry.position():
        print("lat_deg:{} lng_deg:{} abs_alt_m:{} rel_alt_m:{}".format(position.latitude_deg,position.longitude_deg,position.absolute_altitude_m,position.relative_altitude_m))


if __name__ == "__main__":
    # Start the main function
    asyncio.run(run())
