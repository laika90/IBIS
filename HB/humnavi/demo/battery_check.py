import asyncio
import os
import sys

import aiorun

sys.path.append(os.getcwd())

from humnavi.pixhawk import Pixhawk



async def cycle_battery_check():
    while True:
        await pixhawk.get_battery()
        print("voltage:", pixhawk.voltage_v)
        print("remaining percent", pixhawk.remaining_percent)
        await asyncio.sleep(1)

async def main():
    main_coroutines = [cycle_battery_check(), pixhawk.cycle_lidar(), pixhawk.cycle_status_text(), pixhawk.cycle_show()]
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
    pixhawk = Pixhawk()
    print("initialized!")
    aiorun.run(main())
