import sys

ibis_directory = "/home/ibis/PX4-Autopilot/ARLISS_IBIS/IB/Library"
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
waypoint_lat = 47.3972146
waypoint_lng = 8.5455619
waypoint_alt =  3
mission_speed = 5
image_navigation_timeout = 5 * 60
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
#--------------------------------


async def img_navigation(pixhawk):

        logger_info.info("Start image navigation")
        # 高さをwaypoint_altぴったりに合わせる
        # goal_abs_alt = await pixhawk.get_position_alt()
        # goal_lidar_alt = await pixhawk.get_distance_alt()
        # await pixhawk.goto_location(waypoint_lat, waypoint_lng, goal_abs_alt - goal_lidar_alt + waypoint_alt)
        # await asyncio.sleep(5)

        # 10mの高さで画像航法。赤が真下にあっても着陸はしない。
        red_lat, red_lng, abs_alt, is_red_right_below= await pixhawk.calc_red_position()
        lidar_alt = await pixhawk.get_distance_alt()
        logger_info.info(f"lidar:{lidar_alt}")
        logger_info.info(f"[go to] red_lat:{red_lat}, red_lng:{red_lng}, alt:{goal_abs_alt - goal_lidar_alt + 5}, abs_alt:{abs_alt}")
        await pixhawk.goto_location(red_lat, red_lng, goal_abs_alt - goal_lidar_alt + 5)
        await asyncio.sleep(5)

        if waypoint_alt > 5:
            # 5mの高さで画像航法
            red_lat, red_lng, abs_alt, is_red_right_below= await pixhawk.calc_red_position()
            lidar_alt = await pixhawk.get_distance_alt()
            logger_info.info(f"lidar:{lidar_alt}")
            if is_red_right_below:
                logger_info.info(f"Success image navigation!")
                await pixhawk.land()
            else :
                logger_info.info(f"[go to] red_lat:{red_lat}, red_lng:{red_lng}, alt:{goal_abs_alt - goal_lidar_alt + 3}, abs_alt:{abs_alt}")
                await pixhawk.goto_location(red_lat, red_lng, goal_abs_alt - goal_lidar_alt + 3)
                await asyncio.sleep(5)

        # 3mの高さで画像航法
        while True:
            red_lat, red_lng, abs_alt, is_red_right_below= await pixhawk.calc_red_position()
            lidar_alt = await pixhawk.get_distance_alt()
            logger_info.info(f"lidar:{lidar_alt}")
            logger_info.info(f"[go to] red_lat:{red_lat}, red_lng:{red_lng}, abs_alt:{abs_alt}")
            await pixhawk.goto_location(red_lat, red_lng, abs_alt)
            await asyncio.sleep(5)
            if is_red_right_below:
                break
        logger_info.info(f"Success image navigation!")
        await pixhawk.gather_land_coroutines()

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
    
    await pixhawk.connect()
    await pixhawk.upload_mission()
    await pixhawk.health_check()
    await pixhawk.arm()
    await pixhawk.start_mission()
    await pixhawk.gather_main_coroutines()
    # await pixhawk.perform_image_navigation_with_timeout()
    await pixhawk.gather_land_coroutines()
    # try:
    #     await asyncio.wait_for(img_navigation(pixhawk), timeout = 3*60) 
    # except asyncio.TimeoutError:
    #     await pixhawk.land()


if __name__ == "__main__":

    asyncio.run(run())