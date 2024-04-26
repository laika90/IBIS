import asyncio
import datetime
import json
import os
import sys
import mavsdk

import aiorun
from omegaconf import OmegaConf

sys.path.append(os.getcwd())

from humnavi.light import LightSensor
from humnavi.pixhawk import Pixhawk
from humnavi.lora import Lora
from humnavi.logger import logger_info

SYSTEM_ADDRESS = "serial:///dev/ttyACM0:115200"
LOG_VIDEO_PATH = os.path.abspath("log") + "/" + str(datetime.date.today())

async def arliss_hummingbird(conf: OmegaConf) -> None:
    await pixhawk.wait_arm_open(light)
    await pixhawk.task_transition_from_arm_to_goto(conf)
    await pixhawk.task_goto_location_without_set_target(conf)
    await pixhawk.task_goto_land_without_detection(conf)
    await pixhawk.task_land()

async def main(conf: OmegaConf) -> None:
    await pixhawk.connect(SYSTEM_ADDRESS)
    try:
        await pixhawk.set_maximum_speed(conf.max_cruise_speed_m_s)
    except mavsdk.action.ActionError:
        logger_info.info("set maximum speed ActionError")
        await asyncio.sleep(0.01)
    try:
        await pixhawk.set_takeoff_altitude(conf.takeoff_altitude)
    except mavsdk.action.ActionError:
        logger_info.info("set takeoff altitude ActionError")
        await asyncio.sleep(0.01)
    logger_info.info("drone connected!")
    main_coroutines = [
        pixhawk.cycle_hold_wait(light),
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
        pixhawk.cycle_arliss_log(),
        light.cycle_light_naive_carefully(conf.cds_threshold),
        arliss_hummingbird(conf),
    ]
    if conf.lora:
        main_coroutines.append(lora.switch_lora(pixhawk))
        main_coroutines.append(lora.cycle_send_position(pixhawk))
    await asyncio.gather(*main_coroutines)

if __name__ == "__main__":
    with open("config/waypoints_gps.json", mode="r") as f:
        location_dict = json.load(f)
    with open("config/arliss_config.yaml", mode="r") as f:
        conf = OmegaConf.load(f)
    if conf.drone == "usb":
        SYSTEM_ADDRESS = "serial:///dev/ttyACM0:115200"
    elif conf.drone == "pin":
        SYSTEM_ADDRESS = "serial:///dev/serial0:921600"
    elif conf.drone == "gazebo":
        SYSTEM_ADDRESS = "udp://:14540"
    pixhawk = Pixhawk()
    light = LightSensor()
    lora = Lora()
    pixhawk.set_target_from_dict(location_dict, conf.target_name)
    logger_info.info("initialized!")
    aiorun.run(main(conf))
