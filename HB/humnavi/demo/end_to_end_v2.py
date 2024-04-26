import asyncio
import json
import os
import sys
import time

import aiorun
from omegaconf import OmegaConf

sys.path.append(os.getcwd())

from humnavi.light import LightSensor
from humnavi.pixhawk import Pixhawk



async def end_to_end(location_dict: dict, conf: OmegaConf) -> None:
    await pixhawk.task_hold_wait()
    await pixhawk.wait_arm_open(light)
    print("arms opened!")
    deploy_time = time.time()
    await asyncio.sleep(conf.deploy_arm_s)
    await pixhawk.set_maximum_speed(conf.max_cruise_speed)
    await pixhawk.arm()
    arm_time = time.time()
    print("armed after deploy ", arm_time - deploy_time, " sec.")
    while True:
        print("freefall start at height:", pixhawk.relative_altitude_m, "m")
        if (
            pixhawk.down_m_s > conf.limit_down_m_s
            or pixhawk.lidar < conf.limit_lidar
            or (time.time() - arm_time) > conf.arm_goto_s
        ):
            break
        else:
            await asyncio.sleep(0.01)
    print("freefall end at height", pixhawk.relative_altitude_m, "m")
    target_name = conf.mission_name + "_target"
    await pixhawk.task_goto_location(
        location_dict, target_name, conf.time_limit_goto
    )
    await pixhawk.task_goto_land(conf.land_time_limit)
    await pixhawk.land()

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
        pixhawk.cycle_show(),
        pixhawk.cycle_arliss_log(),
        light.cycle_light_naive_carefully(conf.cds_threshold),
        end_to_end(location_dict, conf),
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
    with open("config/end_to_end_v2_example.yaml", mode="r") as f:
        conf = OmegaConf.load(f)
    pixhawk = Pixhawk()
    light = LightSensor()
    print("initialized!")
    aiorun.run(main(location_dict, conf))
