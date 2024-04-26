import asyncio
from mavsdk import System
import time

altitude = 2.5
mode = None

async def run():
    
    drone = System()
    print("Waiting for drone to connect...")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break
        
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print_altitude_task = asyncio.create_task(print_altitude(drone))
    print_flight_mode_task = asyncio.create_task(print_flight_mode(drone))
    arm_takeoff_task = asyncio.create_task(arm_takeoff(drone))
    await print_altitude_task
    await print_flight_mode_task
    await arm_takeoff_task
    

async def arm_takeoff(drone):
    print("-- Arming")
    await drone.action.arm()
    print("-- Armed")
    print("-- Taking off")
    await drone.action.set_takeoff_altitude(altitude)
    await drone.action.takeoff()
    await asyncio.sleep(20)

    print("-- Landing")
    await drone.action.land()


async def print_altitude(drone):
    previous_altitude = 0.0
    
    async for distance in drone.telemetry.distance_sensor():
        altitude_now = distance.current_distance_m
        print("difference : {}".format(altitude_now - previous_altitude))
        if abs(previous_altitude - altitude_now) >= 0.1:
            previous_altitude = altitude_now
            print(f"Altitude: {altitude_now}")

       
        if altitude_now > 0.3:
            print("over 0.3")
            await drone.action.land()


async def print_flight_mode(drone):
    async for flight_mode in drone.telemetry.flight_mode():
        mode = flight_mode
        
        
if __name__ == "__main__":
    while True:
        asyncio.get_event_loop().run_until_complete(run())
        time.sleep(3)