# Version2: with optical goal tracking / limited speed recovering
import asyncio
import json
import os
import sys
import time
import datetime

import aiorun
import mavsdk
from omegaconf import OmegaConf

sys.path.append(os.getcwd())

from humnavi.light import LightSensor
from humnavi.detection import LibcsDetection
from humnavi.pixhawk import Pixhawk
from humnavi.camera import LibcsRecord

LOG_VIDEO_PATH = os.path.abspath("log") + "/" + str(datetime.date.today())

async def freefall_land_v2(location_dict: dict, conf: OmegaConf) -> None:
    deploy_time = time.time()
    light.is_armopen = True
    await pixhawk.task_hold_wait()
    await pixhawk.wait_arm_open(light)
    print("arming in 5 seconds")
    await asyncio.sleep(5)
    await pixhawk.set_maximum_speed(3)
    await pixhawk.arm()
    arm_time = time.time()
    print("armed after deploy ", arm_time - deploy_time, " sec.")
    while time.time() - arm_time < conf.arm_goto_s:
        await asyncio.sleep(0.01)
    print("freefall end at", pixhawk.lidar, "m")

    # recovery for 3 seconds
    target_name = conf.mission_name + "_target"
    await pixhawk.task_goto_location(
        location_dict, target_name, 3.0
    )
    
    # goto
    await pixhawk.set_maximum_speed(10)
    await pixhawk.task_goto_location(
        location_dict, target_name, conf.time_limit_goto
    )
    if not pixhawk.abort_goto_land:
        await pixhawk.task_goto_land(conf.time_limit_land)
    await pixhawk.task_land()

async def main(location_dict: dict, conf: OmegaConf) -> None:
    await pixhawk.connect(SYSTEM_ADDRESS)
    print("drone connected!")
    main_coroutines = [
        pixhawk.cycle_show(),
        pixhawk.cycle_armed(),
        pixhawk.cycle_flight_mode(),
        pixhawk.cycle_odometry(),
        pixhawk.cycle_gps_info(),
        pixhawk.cycle_gps_position(),
        pixhawk.cycle_attitude(),
        pixhawk.cycle_lidar(),
        pixhawk.cycle_is_landed(),
        pixhawk.cycle_time(),
        pixhawk.cycle_record_log(),
        record.cycle_record(pixhawk),
        detection.cycle_detect(pixhawk, record),
        freefall_land_v2(location_dict, conf),
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
    with open("config/waypoints_gps.json", mode="r") as f:
        location_dict = json.load(f)
    with open("config/freefall_goto_v2_example.yaml", mode="r") as f:
        conf = OmegaConf.load(f)
    pixhawk = Pixhawk()
    light = LightSensor()
    detection = LibcsDetection()
    record = LibcsRecord(LOG_VIDEO_PATH)
    detection.model_ver = conf.model_ver
    print("initialized!")
    aiorun.run(main(location_dict, conf))
