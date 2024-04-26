import sys

ibis_directory = "/home/pi/ARLISS_IBIS/IB/Library"
sys.path.append(ibis_directory)

import asyncio
import numpy as np
from pixhawk import Pixhawk
from logger_lib import logger_info
from lora import Lora
from light import Light

# parameters---------------------
fuse_PIN = 0
wait_time = 0
fuse_time = 0
land_timelimit = 0
land_judge_len = 30
health_continuous_count = 3
waypoint_lat = 35.79696
waypoint_lng = 139.89208
waypoint_alt = 3
mission_speed = 5
light_threshold = 100
stored_timelimit = 100
stored_judge_time = 100
released_timelimit = 100
released_judge_time = 100
lora_power_pin = 4
lora_sleep_time = 0
use_camera = True
hsv_min_1 = np.array([0,85,0])
hsv_max_1 = np.array([5,255,255])
hsv_min_2 = np.array([150,85,0])
hsv_max_2 = np.array([180,255,255])
deamon_pass = "/home/pi/ARLISS_IBIS/IB/log/Performance_log.txt"
#--------------------------------

async def run():
    
    lora = Lora(
        lora_power_pin,
        lora_sleep_time     
        )
    
    light = Light(light_threshold,
                stored_timelimit,
                stored_judge_time,
                released_timelimit,
                released_judge_time,
                lora,
                deamon_pass = "/home/pi/ARLISS_IBIS/IB/log/Performance_log.txt",
                use_other_param_config = False)
    
    pixhawk = Pixhawk(
                 fuse_PIN,
                 wait_time,
                 fuse_time,
                 land_timelimit,
                 land_judge_len,
                 health_continuous_count,
                 waypoint_lat,
                 waypoint_lng,
                 waypoint_alt,
                 mission_speed,
                 lora,
                 light,
                 use_camera = use_camera
                 )
    
    await pixhawk.connect()

    await pixhawk.upload_mission()

    await pixhawk.health_check()

    await pixhawk.arm()

    await pixhawk.start_mission()

    await pixhawk.gather_main_coroutines()

    await pixhawk.image_navigation_goto()

    await pixhawk.land()

    


if __name__ == "__main__":

    asyncio.run(run())