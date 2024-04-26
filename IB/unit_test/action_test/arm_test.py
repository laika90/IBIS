import asyncio
from mavsdk import System


async def run():

    drone = System()
    print("HEY")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("-- Connected to drone!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        print(health.is_global_position_ok)
        print(health.is_home_position_ok)
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print("-- arming")
    await drone.action.arm()
    
    print("-- Armed")

if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())
