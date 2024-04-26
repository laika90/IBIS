from mavsdk import System
import asyncio

async def run():
    drone = System()
    
    print("-- Waiting for drone to connect...")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")


    async for state in drone.core.connection_state():
        if state.is_connected:
            print("-- Connected to drone!")
            break
        

    print("-- Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break


    print("-- Arming")
    await drone.action.arm()
    print("-- Armed")
    
    
    print("-- Killng the drone")
    await drone.action.kill()
    print("-- Killed!")
    

if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())
