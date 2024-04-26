import asyncio
import json
import os
import sys
import time

import aiorun

sys.path.append(os.getcwd())

from humnavi.light import LightSensor
from humnavi.pixhawk import Pixhawk
from humnavi.logger import logger_info, logger_debug

async def end_to_end(
    location_dict: dict,
    mission_name: str,
    deploy_arm_s: float,
    arm_takeoff_s: float,
    takeoff_goto_s: float,
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
    await pixhawk.task_hold_wait()
    while True:
        if light.is_armopen == True:
                logger_info.info("arms opened!")
                deploy_time = time.time()
                await asyncio.sleep(deploy_arm_s)
                await pixhawk.set_maximum_speed(10)
                await pixhawk.arm()
                arm_time = time.time()
                logger_info.info("armed after deploy " + str(arm_time - deploy_time) + " sec.")
                await asyncio.sleep(arm_takeoff_s)
                await pixhawk.takeoff()
                await asyncio.sleep(takeoff_goto_s)
                logger_info.info("freefall end at height" + str(pixhawk.relative_altitude_m) + "m")
                target_name = mission_name + "_target"
                await pixhawk.task_goto_location(
            location_dict, target_name, time_limit_goto
            )
                await pixhawk.set_maximum_speed(0.5)
                await pixhawk.task_land()
        else:
            await asyncio.sleep(0.01)


async def main(
    threshold: int,
    location_dict: dict,
    mission_name: str,
    deploy_arm_s: float,
    arm_takeoff_s: float,
    takeoff_goto_s: float,
    time_limit_goto: float,
) -> None:
    await pixhawk.connect(SYSTEM_ADDRESS)
    logger_info.info("drone connected!")
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
            location_dict, mission_name, deploy_arm_s, arm_takeoff_s, takeoff_goto_s, time_limit_goto
        ),
    ]
    await asyncio.gather(*main_coroutines)


if __name__ == "__main__":
    logger_info.info("pixhawk or gazebo options: usb, pin, gazebo")
    drone = input()
    if drone == "usb":
        SYSTEM_ADDRESS = "serial:///dev/ttyACM0:115200"
    elif drone == "pin":
        SYSTEM_ADDRESS = "serial:///dev/serial0:921600"
    elif drone == "gazebo":
        SYSTEM_ADDRESS = "udp://:14540"
    logger_info.info("threshold for light sensor in int recommended) 50")
    threshold = int(input())
    logger_info.info("type mission name e.g.) matsudo")
    mission_name = input()
    logger_info.info("waiting time between deploy and arming e.g.) 2.9")
    deploy_arm_s = float(input())
    logger_info.info("time limit between arm and takeoff in seconds recommended) 0.1")
    arm_takeoff_s = float(input())
    logger_info.info("time limit between takeoff and goto in seconds recommended) 0.1")
    takeoff_goto_s = float(input())
    logger_info.info("time limit of goto e.g.) 60")
    time_limit_goto = float(input())
    with open("config/waypoints_gps.json", mode="r") as f:
        location_dict = json.load(f)
    pixhawk = Pixhawk()
    light = LightSensor()
    logger_info.info("initialized!")
    aiorun.run(
        main(
            threshold,
            location_dict,
            mission_name,
            deploy_arm_s,
            arm_takeoff_s,
            takeoff_goto_s,
            time_limit_goto,
        )
    )
