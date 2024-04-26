from mavsdk import System
import asyncio

            
async def get_alt(drone):
    while True:
        async for distance in drone.telemetry.distance_sensor():
            print("lidar:{}".format(distance))
            break
        await asyncio.sleep(0)
        
        
async def run():
    drone = System()
    print("Connecting")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Connected")
            break
    try:
        await asyncio.wait_for(get_alt(drone), timeout = 3)
    except asyncio.TimeoutError as e:
        print("timeout")
    
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())