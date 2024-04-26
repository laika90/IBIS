import sys

ibis_directory = "/home/pi/ARLISS_IBIS/IB/Library"
sys.path.append(ibis_directory)

import asyncio
from pixhawk import Pixhawk
from lora import Lora
from light import Light

# parameters---------------------
fuse_PIN = 0
wait_time = 0
lora_sleep_time = 0
fuse_time = 0
land_timelimit = 0
land_judge_len = 30
health_continuous_count = 1
waypoint_lat = 40.6332542
waypoint_lng = -119.4518258
waypoint_alt = 4
mission_speed = 5
image_navigation_timeout = 0
light_threshold = 100
stored_timelimit = 100
stored_judge_time = 100
released_timelimit = 100
released_judge_time = 100
lora_power_pin = 4
lora_sleep_time = 0
use_camera = False
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
                 image_navigation_timeout,
                 lora,
                 light,
                 use_camera = use_camera,
                 use_gps_config = False
                 )
    
    lora.serial_connect()
    
    await pixhawk.connect()

    await pixhawk.upload_mission()

    await pixhawk.hold()

    await pixhawk.health_check()

    await pixhawk.arm()

    await pixhawk.start_mission()

    # await pixhawk.gather_main_coroutines()
    try:
        await asyncio.wait_for(pixhawk.gather_main_coroutines(), timeout = 10)
    except asyncio.TimeoutError:
        await pixhawk.kill()
        await asyncio.sleep(5)
        print("Killed!")

if __name__ == "__main__":

    asyncio.run(run())