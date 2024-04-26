import asyncio
import datetime
import os
import sys

import aiorun

sys.path.append(os.getcwd())

from humnavi.camera import LibcsRecord
from humnavi.detection import LibcsDetection
from humnavi.pixhawk import Pixhawk

LOG_VIDEO_PATH = os.path.abspath("log") + "/" + str(datetime.date.today())


async def wait_detect():
    await asyncio.sleep(5)
    pixhawk.armed = True


async def main() -> None:
    await pixhawk.connect(SYSTEM_ADDRESS)
    pixhawk.is_detect = True
    main_coroutines = [
        wait_detect(),
        pixhawk.cycle_attitude(),
        pixhawk.cycle_lidar(),
        pixhawk.cycle_gps_position(),
        record.cycle_record(pixhawk),
        detection.cycle_detect(pixhawk, record),
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
    print("model number 1: sheet 2: sheet2 3: cone")
    model_ver = int(input())
    pixhawk = Pixhawk()
    record = LibcsRecord(LOG_VIDEO_PATH)
    detection = LibcsDetection()
    detection.model_ver = model_ver
    aiorun.run(main())
