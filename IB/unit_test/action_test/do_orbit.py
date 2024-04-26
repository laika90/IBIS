import asyncio
from mavsdk import System
from mavsdk.action import OrbitYawBehavior


orbit_height = 5
orbit_radius = 5


async def run():
    global orbit_height
    drone = System()
    
    print("Waiting for drone to connect...")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")

    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone discovered!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break
    
    position = await drone.telemetry.position().__aiter__().__anext__()
    orbit_height += position.absolute_altitude_m
    yaw_behavior = OrbitYawBehavior.HOLD_FRONT_TO_CIRCLE_CENTER
    
    async for position in drone.telemetry.position():
        lati_deg, long_deg = position.latitude_deg, position.longitude_deg
        

    print("-- Arming")
    await drone.action.arm()

    print("--- Taking Off")
    await drone.action.takeoff()
    await asyncio.sleep(10)

    print('Do orbit at {}m height from the ground'.format(orbit_height))
    await drone.action.do_orbit(radius_m=orbit_radius,
                                velocity_ms=2,
                                yaw_behavior=yaw_behavior,
                                latitude_deg=lati_deg,
                                longitude_deg=long_deg,
                                absolute_altitude_m=orbit_height)
    await asyncio.sleep(5)

    await drone.action.return_to_launch()
    print("--- Landing")

if __name__ == "__main__":
    asyncio.run(run())