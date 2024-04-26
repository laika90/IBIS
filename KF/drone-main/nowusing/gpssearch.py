#!/usr/bin/env python3

import asyncio
from mavsdk import System


async def run():
    # Init the drone
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    # await drone.connect(system_address="udp://:14540")
    print("waiting")
    async for state in drone.core.connection_state():
        if state.is_connected : 
            print("connected!")
            break

    # Start the tasks
    # asyncio.ensure_future(print_battery(drone))
    # asyncio.ensure_future(print_in_air(drone))
    asyncio.ensure_future(print_altitude(drone)) #ensure_future:コルーチンオブジェクトの実行をスケジュール(福田)
    asyncio.ensure_future(print_position(drone))

# async def print_battery(drone):
#     async for battery in drone.telemetry.battery():
#         print(f"Battery: {battery.remaining_percent}")



#高度を取得（福田）
async def print_altitude(drone):
    async for terrain_info in drone.telemetry.home():
        print("absolute")
        print(terrain_info.absolute_altitude_m)

# async def print_in_air(drone):
#     async for in_air in drone.telemetry.in_air():
#         print(f"In air: {in_air}")

#現在地を取得(福田)
async def print_position(drone):
    async for position in drone.telemetry.position():
        print("position")
        print(position)



if __name__ == "__main__":
    # Start the main function
    asyncio.ensure_future(run())

    # Runs the event loop until the program is canceled with e.g. CTRL-C
    asyncio.get_event_loop().run_forever()
