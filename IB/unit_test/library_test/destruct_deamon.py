import sys
import asyncio

ibis_directory = "/home/pi/ARLISS_IBIS/IB/Library"
sys.path.append(ibis_directory)

from ibis import Ibis


fuse_pin = 3
wait_time = 60
lora_sleep_time = 3 
fuse_time = 3
land_timelimit = 8
land_judge_len = 30
health_continuous_count = 0
waypoint_lat = 0
waypoint_lng = 0
waypoint_alt = 0
mission_speed = 0
image_navigation_timeout = 5 * 60
light_threshold = 400
stored_timelimit = 60
stored_judge_time = 10
released_timelimit = 8
released_judge_time = 5
lora_power_pin = 4
deamon_pass = "/home/pi/ARLISS_IBIS/IB/log/Performance_log.txt"
is_destruct_deamon = True


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
              deamon_pass = "/home/pi/ARLISS_IBIS/IB/log/Performance_log.txt",
              is_destruct_deamon = True)
    
  await ibis.destruct_deamon()


if __name__ == "__main__":
    
    asyncio.run(run())