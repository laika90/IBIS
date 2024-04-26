import asyncio
import datetime
import json
import os
import sys

import aiorun

sys.path.append(os.getcwd())

from humnavi.camera import LibcsRecord
from humnavi.detection import LibcsDetection
from humnavi.pixhawk import Pixhawk

LOG_VIDEO_PATH = os.path.abspath("log") + "/" + str(datetime.date.today())

pixhawk = Pixhawk()
record = LibcsRecord(LOG_VIDEO_PATH)
detection = LibcsDetection()


async def detection_land(
    takeoff_altitude_m: float,
    location_dict: dict,
    mission_name: str,
    goto_time_limit: float,
    land_time_limit: float,
) -> None:
    """goto -> landing with detection
    Args:
        takeoff_altitude_m (float): takeoff altitude in m
        location_dict (dict): waypoints dict
        mission_name (str): mission name
        goto_time_limit (float): time limit for goto mode
        land_time_limit (float): time limit for landing sequence
    """
    await pixhawk.set_takeoff_altitude(takeoff_altitude_m)
    await pixhawk.set_maximum_speed(10)
    await pixhawk.hold()
    await asyncio.sleep(1)
    await pixhawk.arm()
    await asyncio.sleep(1)
    await pixhawk.takeoff()
    await asyncio.sleep(10)
    while str(pixhawk.flight_mode) != "HOLD":
        await pixhawk.hold()
        await asyncio.sleep(0.1)
    print("starting goto...")
    target_name = mission_name + "_target"
    await pixhawk.task_goto_location(location_dict, target_name, goto_time_limit)
    await pixhawk.task_goto_land(land_time_limit)
    await pixhawk.land()


async def main(
    takeoff_altitude_m: float,
    location_dict: dict,
    mission_name: str,
    goto_time_limit: float,
    land_time_limit: float,
) -> None:
    """execute detection land
    Args:
        takeoff_altitude (float): takeoff altitude in m
        location_dict (dict): location dict
        mission_name (str): mission name
        goto_time_limit (float): time limit for goto mode
        land_time_limit (float): time limit for landing sequence
    """
    detection.model_ver = 2
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
        record.cycle_record(pixhawk),
        detection.cycle_detect(pixhawk, record),
        detection_land(
            takeoff_altitude_m,
            location_dict,
            mission_name,
            goto_time_limit,
            land_time_limit,
        ),
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
    print("type mission name e.g.) noshiro")
    mission_name = input()
    with open("config/waypoints_gps.json", mode="r") as f:
        location_dict = json.load(f)
    print("set takeoff altitude (relative) in float")
    takeoff_altitude = float(input())
    print("time limit for go to mode e.g.) 30")
    goto_time_limit = float(input())
    print("time limit for landing sequence e.g.) 30")
    land_time_limit = float(input())
    aiorun.run(
        main(
            takeoff_altitude,
            location_dict,
            mission_name,
            goto_time_limit,
            land_time_limit,
        )
    )
