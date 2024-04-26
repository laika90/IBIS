import asyncio
import json
import sys

import aiorun
from numpy import average
from omegaconf import OmegaConf

from humnavi.pixhawk import Pixhawk

JSON_PATH = "./config/waypoints_gps.json"


async def task_set_gps(
    location_name: str, num_collection: int, target_altitude: float
) -> None:
    """get gps location of the vehicle

    Args:
        location_name (str): location name
        num_collection (int): the number of samples to collect
        target_altitude (float): target altitude from ground
    """
    num_samples = 0
    latitude_list = []
    longitude_list = []
    abs_altitude_list = []
    rel_altitude_list = []
    target_pos_dict = {}
    while num_samples < num_collection:
        if pixhawk.num_satellites > 0:
            num_samples += 1
            print(f"---sample {num_samples}---")
            print("num satellites:", pixhawk.num_satellites)
            print("latitude:", pixhawk.latitude_deg)
            print("longitude:", pixhawk.longitude_deg)
            print("absolute altitude:", pixhawk.absolute_altitude_m)
            print("relative_altitude:", pixhawk.relative_altitude_m)
            latitude_list.append(pixhawk.latitude_deg)
            longitude_list.append(pixhawk.longitude_deg)
            abs_altitude_list.append(pixhawk.absolute_altitude_m)
            rel_altitude_list.append(pixhawk.relative_altitude_m)
            await asyncio.sleep(2)
        else:
            print("no satellite found...")
            await asyncio.sleep(1)
    print("enough samples collected!")
    ave_latitude = average(latitude_list)
    ave_longitude = average(longitude_list)
    ave_abs_altitude = average(abs_altitude_list)
    ave_rel_altitude = average(rel_altitude_list)
    target_pos = [
        ave_latitude,
        ave_longitude,
        ave_abs_altitude + target_altitude,
        ave_rel_altitude + target_altitude,
        target_altitude,
    ]
    print("new location:", target_pos)

    with open(JSON_PATH, mode="r") as f:
        target_pos_dict = json.load(f)
    target_pos_dict[location_name] = target_pos

    with open(JSON_PATH, mode="w") as f:
        json.dump(target_pos_dict, f)
    sys.exit()


async def main(location_name, num_collection, target_altitude):
    global pixhawk
    pixhawk = Pixhawk()

    main_coroutines = [
        pixhawk.cycle_gps_info(),
        pixhawk.cycle_gps_position(),
        task_set_gps(location_name, num_collection, target_altitude),
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
    print("collection time: the number of samples to calculate mean values:")
    collection_time = int(input())
    print("location name rule: mission_number.zfill(3)  e.g.) noshiro_001")
    print("if it's the target, number = target e.g.) noshiro_target")
    location_name = input()
    print("type target altitude (relative)")
    target_altitude = float(input())
    aiorun.run(main(location_name, collection_time, target_altitude))
