import asyncio
import os
import sys

import aiorun

sys.path.append(os.getcwd())

from humnavi.pixhawk import Pixhawk

SYSTEM_ADDRESS = "serial:///dev/serial0:921600"


async def main() -> None:
    global pixhawk
    pixhawk = Pixhawk()

    main_coroutines = [
        pixhawk.cycle_armed(),
        pixhawk.cycle_flight_mode(),
        pixhawk.cycle_status_text(),
        pixhawk.cycle_odometry(),
        pixhawk.cycle_gps_info(),
        pixhawk.cycle_position_mean(),
        pixhawk.cycle_attitude(),
        pixhawk.cycle_is_landed(),
        pixhawk.cycle_lidar(),
        pixhawk.cycle_time(),
        pixhawk.cycle_show(),
        pixhawk.cycle_arliss_log(),
    ]
    await pixhawk.connect(SYSTEM_ADDRESS)
    await asyncio.gather(*main_coroutines)


if __name__ == "__main__":
    aiorun.run(main())
