# Version3: separate phase between recoviering and goto
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

async def freefall_land_v3(location_dict: dict, conf: OmegaConf) -> None:
    deploy_time = time.time()
    light.is_armopen = True
    await pixhawk.task_hold_wait()
    await pixhawk.wait_arm_open(light)
    print("arming in " + str(conf.deploy_arm_s) + " seconds")
    await asyncio.sleep(conf.deploy_arm_s)
    await pixhawk.set_maximum_speed(conf.max_cruise_speed_m_s)
    await pixhawk.arm()
    print("starting goto in " + str(conf.arm_goto_s) + " seconds")
    await pixhawk.task_transition_from_arm_to_goto(deploy_time, conf)
    await pixhawk.task_goto_location_without_set_target(conf.time_limit_goto_s)
    if not pixhawk.abort_goto_land:
        await pixhawk.task_goto_land(conf.land_time_limit_s)
    await pixhawk.task_land()

async def main(location_dict: dict, conf: OmegaConf) -> None:
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
        pixhawk.cycle_record_log(),
        record.cycle_record(pixhawk),
        detection.cycle_detect(pixhawk, record),
        freefall_land_v3(location_dict, conf),
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
    with open("config/freefall_goto_v3_example.yaml", mode="r") as f:
        conf = OmegaConf.load(f)
    pixhawk = Pixhawk()
    light = LightSensor()
    detection = LibcsDetection()
    record = LibcsRecord(LOG_VIDEO_PATH)
    detection.model_ver = conf.model_ver
    pixhawk.set_target_from_dict(location_dict, conf.target_name)
    print("initialized!")
    aiorun.run(main(location_dict, conf))
