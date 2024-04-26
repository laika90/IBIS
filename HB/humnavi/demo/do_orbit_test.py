import asyncio
import datetime
import json
import os
import sys

import aiorun
from omegaconf import OmegaConf

sys.path.append(os.getcwd())

from humnavi.pixhawk import Pixhawk
from humnavi.camera import LibcsRecord
from humnavi.logger import logger_info

SYSTEM_ADDRESS = "serial:///dev/ttyACM0:115200"
LOG_VIDEO_PATH = os.path.abspath("log") + "/" + str(datetime.date.today())

async def do_orbit_test(conf: OmegaConf) -> None:
    await pixhawk.arm()
    await asyncio.sleep(conf.arm_takeoff_s)
    await pixhawk.takeoff()
    await asyncio.sleep(conf.takeoff_goto_s)
    await pixhawk.task_goto_location_without_set_target(conf.time_limit_goto_s)
    await pixhawk.task_do_orbit(conf)
    await pixhawk.task_land()

async def main(conf: OmegaConf) -> None:
    await pixhawk.connect(SYSTEM_ADDRESS)
    try:
        await pixhawk.set_maximum_speed(conf.max_cruise_speed_m_s)
    except:
        logger_info.info("set maximum speed ActionError")
        await asyncio.sleep(0.01)
    await pixhawk.set_takeoff_altitude(conf.takeoff_altitude_m)
    logger_info.info("drone connected!")
    main_coroutines = [
        pixhawk.cycle_armed(),
        pixhawk.cycle_flight_mode(),
        pixhawk.cycle_odometry(),
        pixhawk.cycle_gps_info(),
        pixhawk.cycle_gps_position(),
        pixhawk.cycle_attitude(),
        pixhawk.cycle_time(),
        pixhawk.cycle_show(),
        pixhawk.cycle_arliss_log(),
        do_orbit_test(conf),
    ]
    if conf.is_land_detect_deg_only:
        main_coroutines.append(pixhawk.cycle_is_landed_deg_only())
    else:
        main_coroutines.append(pixhawk.cycle_is_landed())
    if drone == "gazebo":
        main_coroutines.append(pixhawk.cycle_fake_lidar())
    else:
        main_coroutines.append(pixhawk.cycle_lidar()) 
    await asyncio.gather(*main_coroutines)

if __name__ == "__main__":
    with open("config/waypoints_gps.json", mode="r") as f:
        location_dict = json.load(f)
    with open("config/do_orbit_test.yaml", mode="r") as f:
        conf = OmegaConf.load(f)
    print("pixhawk or gazebo options: usb, pin, gazebo")
    drone = input()
    if drone == "usb":
        SYSTEM_ADDRESS = "serial:///dev/ttyACM0:115200"
    elif drone == "pin":
        SYSTEM_ADDRESS = "serial:///dev/serial0:921600"
    elif drone == "gazebo":
        SYSTEM_ADDRESS = "udp://:14540"
    pixhawk = Pixhawk()
    record = LibcsRecord(LOG_VIDEO_PATH)
    pixhawk.set_target_from_dict(location_dict, conf.target_name)
    logger_info.info("initialized!")
    aiorun.run(main(conf))
