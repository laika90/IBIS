import asyncio
import os
import sys

import aiorun

sys.path.append(os.getcwd())

from humnavi.pixhawk import Pixhawk
from humnavi.lora import Lora

async def check_gps(pixhawk) -> None:
    """check num_satellites and absolute_altitude_m and judge if drone is out of carrier"""
    print(pixhawk.relative_altitude_m)
    if pixhawk.num_satellites > 6:
        if pixhawk.absolute_altitude_m > 1203:
            lora.is_out = True
    await asyncio.sleep(1)

async def switch_lora(pixhawk):
    """turn off lora until drone is out of carrier"""
    while True:
        await check_gps(pixhawk)
        if lora.is_out:
            print("lora start")
            await lora.power_on()
            await lora.write("start lora")
            return
        print("lora waiting")
        await lora.power_off()

async def main() -> None:
    main_coroutines = [
        pixhawk.cycle_armed(),
        pixhawk.cycle_flight_mode(),
        pixhawk.cycle_status_text(),
        pixhawk.cycle_odometry(),
        pixhawk.cycle_gps_info(),
        pixhawk.cycle_gps_position(),
        pixhawk.cycle_attitude(),
        pixhawk.cycle_lidar(),
        pixhawk.cycle_time(),
        pixhawk.cycle_show(),
        pixhawk.cycle_record_log(),
        lora.cycle_receive_lora(pixhawk),
        check_gps(pixhawk),
        switch_lora(pixhawk),
        lora.cycle_send_position(pixhawk),        
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
    pixhawk = Pixhawk()
    lora = Lora()
    aiorun.run(main())
