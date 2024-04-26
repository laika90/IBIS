import asyncio
import os
import sys

import aiorun

sys.path.append(os.getcwd())

from humnavi.pixhawk import Pixhawk



async def arm():
    await pixhawk.arm()
    await asyncio.sleep(1)
    await pixhawk.kill()


async def main():
    main_coroutines = [
        pixhawk.cycle_armed(),
        pixhawk.cycle_flight_mode(),
        pixhawk.cycle_status_text(),
        pixhawk.cycle_odometry(),
        pixhawk.cycle_lidar(),
        pixhawk.cycle_gps_info(),
        pixhawk.cycle_gps_position(),
        pixhawk.cycle_attitude(),
        pixhawk.cycle_is_landed(),
        pixhawk.cycle_time(),
        pixhawk.cycle_show(),
        pixhawk.cycle_record_log(),
        pixhawk.cycle_health(),
        arm(),
    ]
    await pixhawk.connect(SYSTEM_ADDRESS)
    await asyncio.gather(*main_coroutines)


if __name__ == "__main__":
    print("pixhawk or gazebo options: usb, pin, gazebo")
    drone = input()
    if drone == "usb":
        SYSTEM_ADDRESS = "serial:///dev/ttyACM0:115200"
    elif drone == "pin":
        SYSTEM_ADDRESS = "serial:///dev/serial0:921600"
    elif drone == "gazebo":
        SYSTEM_ADDRESS = "udp://:14540"
    pixhawk = Pixhawk()
    print("initialized!")
    aiorun.run(main())
