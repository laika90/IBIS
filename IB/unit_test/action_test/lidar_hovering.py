#lidarがわからないと無理そう

import asyncio
import time
from mavsdk import System

#Lidar関係
RX = 23
pi = pigpio.pi()
pi.set_mode(RX, pigpio.INPUT)
pi.bb_serial_read_open(RX, 115200) 

#高さ指定
hovering_hight = 2.5
                
                
async def run():

    drone = System()
    
    print("Waiting for drone to connect...")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")

    status_text_task = asyncio.ensure_future(print_status_text(drone))

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print("-- Arming....")
    await drone.action.arm()
    print("-- Armed")

    print("-- Taking off")
    await drone.action.takeoff()

    await asyncio.sleep(5)
    
    print("-- Fetching amsl altitude at home location....")
    async for terrain_info in drone.telemetry.home():
        absolute_altitude = terrain_info.absolute_altitude_m
        break
    
    async for position in drone.telemetry.position():
        lati_deg, long_deg = position.latitude_deg, position.longitude_deg
        
    await drone.action.goto_location(lati_deg, long_deg, hovering_hight, 0)
    print("-- Reached the hovering hight")
    
    await asyncio.sleep(5)

    print("-- Landing....")
    await drone.action.land()
    
    status_text_task.cancel()
    
async def print_status_text(drone):
    try:
        async for status_text in drone.telemetry.status_text():
            print(f"Status: {status_text.type}: {status_text.text}")
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())