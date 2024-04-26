import asyncio
import sys
sys.path.append("/home/pi/ARLISS_IBIS/unit_test/log_test")
from mavsdk import System
from logger import logger_info, logger_debug


async def run():

    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")

    status_text_task = asyncio.ensure_future(print_status_text(drone))

    logger_info.info("Waiting for drone to connect...")
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():

        if state.is_connected:
            print(f"-- Connected to drone!")
            break
        
    logger_info.info("-- Arming")
    print("-- Arming")
    await drone.action.arm()
    logger_info.info("-- Armed")
    print("-- Armed")
    logger_info.info("-- Taking off")
    print("-- Taking off")
    await drone.action.takeoff()

    await asyncio.sleep(10)
    logger_info.info("-- Landing")
    print("-- Landing")
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
