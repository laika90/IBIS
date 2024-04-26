import asyncio
import os
import sys
import time

import aiorun

sys.path.append(os.getcwd())

from humnavi.pixhawk import Pixhawk

SYSTEM_ADDRESS = "serial:///dev/serial0:921600"


async def takeoff_and_kill(takeoff_altitude, arm_time, takeoff_time):
    await pixhawk.hold()
    await asyncio.sleep(3)
    await pixhawk.arm()
    start_arm_time = time.time()
    await asyncio.sleep(arm_time)
    await pixhawk.set_takeoff_altitude(takeoff_altitude)
    await pixhawk.takeoff()
    start_takeoff_time = time.time()
    print("takeoff after", start_takeoff_time - start_arm_time, "seconds arming")
    await asyncio.sleep(goto_time)
    start_goto_time = time.time()
    print("goto after", start_goto_time - start_takeoff_time, "seconds arming")
    await pixhawk.goto_location(pixhawk.latitude_deg, pixhawk.longitude_deg, pixhawk.absolute_altitude_m - 50, 0)
    await asyncio.sleep(takeoff_time - goto_time)
    kill_time = time.time()
    print("killed after", kill_time - start_takeoff_time, "seconds takeoff")
    print("whole time: from arm starting to kill took", kill_time - start_arm_time, "seconds")
    await pixhawk.kill()


async def main(takeoff_altitude, arm_time, takeoff_time):
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
        # pixhawk.cycle_show(),
        pixhawk.cycle_record_log(),
        takeoff_and_kill(takeoff_altitude, arm_time, takeoff_time),
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
print("set arm_time in float")
arm_time = float(input())
print("set takeoff_time in float")
takeoff_time = float(input())
print("set goto time in float")
goto_time = float(input())
pixhawk = Pixhawk()

aiorun.run(main(takeoff_altitude, arm_time, takeoff_time))
