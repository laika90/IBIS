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
    
    print(drone.telemetry.get_gps_grobal_origin())

if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())