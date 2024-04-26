from pixhawk import Pixhawk
from lora import Lora
from light import Light
from logger_lib import logger_info
import time


class Ibis:
    
    def __init__(self,
               # pixhawk
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
                 is_destruct_deamon = True,
               # other defaults
                 use_camera = False,
                 use_gps_config = False,
                 use_other_param_config = False):
      
        logger_info.info("#################### Initializing Ibis ####################")
          
        self.lora = Lora(lora_power_pin,
                          lora_sleep_time)
        
        self.light = Light(light_threshold,
                            stored_timelimit,
                            stored_judge_time,
                            released_timelimit,
                            released_judge_time,
                            self.lora,
                            deamon_pass)
        
        self.pixhawk = Pixhawk(fuse_pin,
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
                                self.lora,
                                self.light,
                                deamon_pass,
                                use_camera,
                                use_gps_config,
                                use_other_param_config)
        
        self.deamon_pass = deamon_pass
        self.deamon_file = open(self.deamon_pass)
        self.deamon_log = self.deamon_file.read()
        self.is_destruct_deamon = is_destruct_deamon
        
        logger_info.info("#################### Ibis initialized ####################")
          
          
    async def wait_storing_phase(self):
        
        logger_info.info("#################### Wait store phase start ####################")
        await self.lora.power_on()
        await self.pixhawk.connect()
        await self.pixhawk.print_and_wait()
        logger_info.info("#################### Wait store phase finished ####################")
        
        
    async def judge_phase(self):
        
        logger_info.info("#################### Judge phase start ####################")
        await self.pixhawk.upload_mission()
        await self.light.stored_judge()
        await self.light.released_judge()
        await self.lora.write("Ibis released")
        await self.pixhawk.landjudge_and_sendgps()
        logger_info.info("#################### Judge phase finished ####################")
    
    async def fuse_phase(self):
      
        logger_info.info("#################### Fuse phase start ####################")
        self.pixhawk.fuse()
        time.sleep(2)
        self.pixhawk.fuse()
        logger_info.info("#################### Fuse phase finished ####################")
        
        
    async def flying_phase(self):
        
        logger_info.info("#################### Flying phase start ####################")
        await self.pixhawk.hold()
        await self.pixhawk.health_check()
        await self.pixhawk.arm()
        await self.pixhawk.start_mission()
        await self.pixhawk.gather_main_coroutines()
        await self.pixhawk.perform_image_navigation_with_timeout()
        logger_info.info("#################### Flying phase finished ####################")
    
    
    async def destruct_deamon(self):
        
        if self.is_destruct_deamon:
            logger_info.info("Destructing deamon log")
            with open(self.deamon_pass, "w") as deamon:
                deamon.write("")
            
    
    async def IBIS_MISSION(self):
        
        logger_info.info("#################### IBIS MISSION START ####################")
        
        await self.wait_storing_phase()
        
        await self.judge_phase()
        
        await self.fuse_phase()
        
        await self.flying_phase()
        
        logger_info.info("#################### IBIS MISSION COMPLETE ####################")
        
        await self.lora.write("IBIS MISSION COMPLETE")
        
        await self.destruct_deamon()