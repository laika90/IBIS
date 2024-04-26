import asyncio
import os
import sys
import time

import aiorun

sys.path.append(os.getcwd())

from humnavi.light import LightSensor
from humnavi.pixhawk import Pixhawk


async def task_light_arm(deploy_arm_s: float, arm_goto_s: float):
    while True:
        if light.is_armopen == True:
            start_time = time.time()
            await asyncio.sleep(deploy_arm_s)
            await pixhawk.arm()
            arm_time = time.time()
            print("deploy to arm ", arm_time - start_time, " sec.")
            await asyncio.sleep(1)
            await pixhawk.kill()
            await asyncio.sleep(arm_goto_s - 1)
            print("arm to goto: ", time.time() - arm_time, " sec.")
            break
        else:
            await asyncio.sleep(0.01)


async def main(threshold: int, deploy_arm_s: float, arm_goto_s: float):
    main_coroutines = [
        light.cycle_light_naive(threshold),
        task_light_arm(deploy_arm_s, arm_goto_s),
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
    light = LightSensor()
    pixhawk = Pixhawk()
    "initialized!"
    print("type threshold for oepn_arm")
    threshold = int(input())
    print("waiting time between deploy and arming e.g.) 30 on the ground 1 in case")
    deploy_arm_s = float(input())
    print("time limit between arm and goto in seconds recommended) 2.5")
    arm_goto_s = float(input())

    aiorun.run(main(threshold, deploy_arm_s, arm_goto_s))
