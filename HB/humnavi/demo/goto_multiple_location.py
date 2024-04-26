import asyncio
import json
import os
import sys

import aiorun
from omegaconf import OmegaConf

sys.path.append(os.getcwd())

from humnavi.pixhawk import Pixhawk

SYSTEM_ADDRESS = "serial:///dev/serial0:921600"


async def takeoff_goto_multiple_location(location_dict: dict, conf: OmegaConf) -> None:
    """goto multiple location

    Args:
        location_dict (dict): location dict
        conf (Omegaconf): config omegaconf
    """
    await pixhawk.set_takeoff_altitude(conf.takeoff_altitude_m)
    await pixhawk.set_maximum_speed(conf.maximum_speed_ms)
    await pixhawk.hold()
    await asyncio.sleep(1)
    await pixhawk.arm()
    await asyncio.sleep(1)
    await pixhawk.takeoff()
    await asyncio.sleep(10)
    print("starting goto...")
    target_list = conf.target_list
    for target_name in target_list:
        await pixhawk.task_goto_location(location_dict, target_name, conf.time_limit)
    await pixhawk.land()


async def main(location_dict: dict, conf: OmegaConf) -> None:
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
        pixhawk.cycle_show(),
        pixhawk.cycle_time(),
        pixhawk.cycle_arliss_log(),
        takeoff_goto_multiple_location(location_dict, conf),
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
    with open("config/waypoints_gps.json", mode="r") as f:
        location_dict = json.load(f)
    with open("config/goto_multiple_location_example.yaml", mode="r") as f:
        conf = OmegaConf.load(f)
    pixhawk = Pixhawk()
    aiorun.run(main(location_dict, conf))
