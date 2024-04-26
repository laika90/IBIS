import asyncio
import os
import sys

import aiorun
import mavsdk

sys.path.append(os.getcwd())

from humnavi.pixhawk import Pixhawk
from humnavi.light import LightSensor

SYSTEM_ADDRESS = "serial:///dev/serial0:921600"

async def light_timer():
    await asyncio.sleep(240)
    print("1 min left")
    await asyncio.sleep(30)
    print("30 sec left")
    await asyncio.sleep(20)
    print("10 sec left")
    await asyncio.sleep(10)
    print("time up")
    await pixhawk.arm()
    await asyncio.sleep(3)
    await pixhawk.kill()
    print("hold wait test done!")

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
        pixhawk.task_hold_wait(),
        pixhawk.wait_arm_open(light),
        light_timer(),
    ]
    await pixhawk.connect(SYSTEM_ADDRESS)
    await asyncio.gather(*main_coroutines)


if __name__ == "__main__":
    print("pixhawk or gazebo options: pixhawk, gazebo")
    drone = input()
    if drone == "pixhawk":
        SYSTEM_ADDRESS = "serial:///dev/ttyACM0:115200"
    elif drone == "gazebo":
        SYSTEM_ADDRESS = "udp://:14540"
    pixhawk = Pixhawk()
    light = LightSensor()
    light.is_armopen = False
    print("initialized!")
    aiorun.run(main())
