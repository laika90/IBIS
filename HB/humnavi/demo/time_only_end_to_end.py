import asyncio
import json
import os
import sys
import time

import aiorun

sys.path.append(os.path.abspath("../humnavi"))
sys.path.append(os.path.abspath(".."))

from humnavi.light import LightSensor
from humnavi.pixhawk import Pixhawk


async def end_to_end(
    location_dict: dict,
    mission_name: str,
    deploy_arm_s: float,
    arm_goto_s: float,
    time_limit_goto: float,
) -> None:
    """end to end

    Args:
        location_dict (dict): location dict e.g.)
        mission_name (str): mission name e.g.) noshiro
        deploy_arm_s (float): waiting time between deploy and arming e.g.) 1
        arm_goto_s (float): time limit between arm and goto in seconds e.g.) 2.8
        time_limit_goto (float): time limit of goto
    """
    while True:
        if light.is_armopen == True:
            print("arms opened!")
            await pixhawk.hold()
            deploy_time = time.time()
            await asyncio.sleep(deploy_arm_s)
            await pixhawk.set_maximum_speed(10)
            await pixhawk.arm()
            arm_time = time.time()
            print("armed after deploy ", arm_time - deploy_time, " sec.")
            while True:
                print("freefall start at height:", pixhawk.relative_altitude_m, "m")
                if (time.time() - arm_time) > arm_goto_s:
                    print("freefall end at height", pixhawk.relative_altitude_m, "m")
                    await pixhawk.task_goto_location(
                        location_dict, mission_name, time_limit_goto
                    )
                    await pixhawk.set_maximum_speed(0.5)
                    await pixhawk.land()
                    await asyncio.sleep(10)
                    await pixhawk.disarm()
                else:
                    await asyncio.sleep(0.01)
        else:
            await asyncio.sleep(0.01)


async def main(
    threshold: int,
    location_dict: dict,
    mission_name: str,
    deploy_arm_s: float,
    arm_goto_s: float,
    time_limit_goto: float,
) -> None:
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
        light.cycle_light_naive_carefully(threshold),
        end_to_end(
            location_dict, mission_name, deploy_arm_s, arm_goto_s, time_limit_goto
        ),
    ]
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
    print("threshold for light sensor in int recommended) 100")
    threshold = int(input())
    print("type mission name e.g.) noshiro")
    mission_name = input()
    print("waiting time between deploy and arming e.g.) 30 on the ground 0.5 in case")
    deploy_arm_s = float(input())
    print("time limit between arm and goto in seconds recommended) 2.5")
    arm_goto_s = float(input())
    print("time limit of goto e.g.) 60")
    time_limit_goto = float(input())
    with open("config/waypoints_gps.json", mode="r") as f:
        location_dict = json.load(f)
    pixhawk = Pixhawk()
    light = LightSensor()
    print("initialized!")
    aiorun.run(
        main(
            threshold,
            location_dict,
            mission_name,
            deploy_arm_s,
            arm_goto_s,
            time_limit_goto,
        )
    )
