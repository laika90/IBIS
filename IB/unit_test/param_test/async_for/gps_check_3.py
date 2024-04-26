import asyncio
from mavsdk import System


async def print_gps():
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    # print("Waiting for drone to connect...")
    # async for state in drone.core.connection_state():
    #     if state.is_connected:
    #         print("-- Connected to drone!")
    #         break
    asyncio.ensure_future(print_position(drone))
    while True:
        await asyncio.sleep(1)

async def print_position(drone):
    async for position in drone.telemetry.position():
            print("b")
            print(position)
            
asyncio.run(print_gps())