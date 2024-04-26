import asyncio
import time
from mavsdk import System

                
                
async def run():

    print("Hey")
    drone = System()
    
    print("Waiting for drone to connect...")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")


    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break
        
    async for distance in drone.telemetry.distance_sensor():
        print(distance)

if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())