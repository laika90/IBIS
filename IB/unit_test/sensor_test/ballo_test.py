# import asyncio
# import time
# from mavsdk import System

                
                
# async def run():

#     print("Hey")
#     drone = System()
    
#     print("Waiting for drone to connect...")
#     await drone.connect(system_address="serial:///dev/ttyACM0:115200")


#     async for state in drone.core.connection_state():
#         if state.is_connected:
#             print(f"-- Connected to drone!")
#             break
        
#     asyncio.ensure_future(print_pressure(drone))
    
#     while True:
#         await asyncio.sleep(1)
        
# async def print_pressure(drone):
#     async for pressure in drone.telemetry.scaled_pressure():
#         print(pressure)

# if __name__ == "__main__":
#     # Run the asyncio loop
#     asyncio.run(run())

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
        
    print(drone.telemetry.scaled_pressure())
        
    async for pressure in drone.telemetry.scaled_pressure():
        print("a")
        print(pressure)

if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())