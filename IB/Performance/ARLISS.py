import sys
import asyncio

ibis_directory = "/home/pi/ARLISS_IBIS/IB/Library"
sys.path.append(ibis_directory)

from ibis import Ibis


fuse_pin = 3
wait_time = 0
lora_sleep_time = 3 
fuse_time = 5
land_timelimit = 30
land_judge_len = 20
health_continuous_count = 1
waypoint_lat = 40.85543333
waypoint_lng = -119.11018888
waypoint_alt = 10
mission_speed = 12
image_navigation_timeout = 5 * 60
light_threshold = 700
stored_timelimit = 0
stored_judge_time = 1
released_timelimit = 0
released_judge_time = 1
lora_power_pin = 4
deamon_pass = "/home/pi/ARLISS_IBIS/IB/log/Performance_log.txt"
is_destruct_deamon = False
use_camera = True
use_gps_config = False
use_other_param_config = False


async def run():
    
    ibis = Ibis(# pixhawk
                 fuse_pin,
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
               # light
                 light_threshold,
                 stored_timelimit,
                 stored_judge_time,
                 released_timelimit,
                 released_judge_time,
               # lora
                 lora_power_pin,
                 lora_sleep_time, 
               # deamon
                 deamon_pass,
                 is_destruct_deamon,
               # other defaults
                 use_camera,
                 use_gps_config,
                 use_other_param_config)
    
    await ibis.IBIS_MISSION()
    
    
if __name__ == "__main__":
  
  asyncio.run(run())