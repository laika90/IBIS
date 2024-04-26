import asyncio
import os
import sys

import aiorun

sys.path.append(os.getcwd())

from humnavi.pixhawk import Pixhawk

SYSTEM_ADDRESS = "serial:///dev/serial0:921600"


async def takeoff_and_land(takeoff_altitude):
    await pixhawk.hold()
    await asyncio.sleep(3)
    await pixhawk.arm()
    await asyncio.sleep(1)
    await pixhawk.set_takeoff_altitude(takeoff_altitude)
    await pixhawk.takeoff()
    await asyncio.sleep(10)
    await pixhawk.land()


async def main(takeoff_altitude):
    await pixhawk.connect(SYSTEM_ADDRESS)
    print("drone connected!")
    main_coroutines = [
        pixhawk.cycle_armed(),
        pixhawk.cycle_flight_mode(),
        pixhawk.cycle_odometry(),
        pixhawk.cycle_gps_info(),
        pixhawk.cycle_gps_position(),
        pixhawk.cycle_attitude(),
        pixhawk.cycle_lidar(),
        pixhawk.cycle_is_landed(),
        pixhawk.cycle_time(),
        pixhawk.cycle_show(),
        pixhawk.cycle_record_log(),
        takeoff_and_land(takeoff_altitude),
    ]
    await asyncio.gather(*main_coroutines)


print("pixhawk or gazebo options: usb, pin, gazebo")
drone = input()
if drone == "usb":
    SYSTEM_ADDRESS = "serial:///dev/ttyACM0:115200"
elif drone == "pin":
    SYSTEM_ADDRESS = "serial:///dev/serial0:921600"
elif drone == "gazebo":
    SYSTEM_ADDRESS = "udp://:14540"
print("set takeoff altitude (relative) in float")
takeoff_altitude = float(input())
pixhawk = Pixhawk()
aiorun.run(main(takeoff_altitude))
