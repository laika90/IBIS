import asyncio
from mavsdk import System


async def run():

    drone = System()
    print("HEY")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    # await drone.connect(system_address="udp://:14540")

    

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    await drone.action.land()






if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
