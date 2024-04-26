import asyncio
import json
import os
import sys

import aiorun

sys.path.append(os.getcwd())

from humnavi.pixhawk import Pixhawk

SYSTEM_ADDRESS = "serial:///dev/serial0:921600"


async def goto_from_air(location_dict: dict, mission_name: str) -> None:
    """goto from air

    Args:
        location_dict (dict): waypoints dict
        mission_name (str): mission name
    """
    await pixhawk.hold()
    await asyncio.sleep(1)
    await pixhawk.arm()
    await asyncio.sleep(1)
    try:
        _ = location_dict[mission_name + "_target"]
    except KeyError:
        print("set mission target")

    for i in range(len(location_dict)):
        try:
            print("heading for waypoints ", str(i + 1))
            lat, lng, abs_alt, _ = location_dict[mission_name + "_" + str(i + 1)]
            await pixhawk.goto_location(lat, lng, abs_alt, 0)
        except KeyError:
            print("heading for target ")
            lat, lng, abs_alt, _ = location_dict[mission_name + "_target"]
            await pixhawk.goto_location(lat, lng, abs_alt, 0)
    await pixhawk.land()


async def main(location_dict: dict, mission_name: str) -> None:
    """execute goto from air

    Args:
        location_dict (dict): location dict
        mission_name (str): mission name
    """
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
        goto_from_air(location_dict, mission_name),
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
    pixhawk = Pixhawk()
    print("initialized!")
    aiorun.run(main(location_dict, mission_name))
