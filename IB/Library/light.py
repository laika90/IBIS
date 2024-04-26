from typing import Any
import spidev
from logger_lib import logger_info
import time
import json
import asyncio


class Light:
    
    def __init__(self,     
                 light_threshold,
                 stored_timelimit,
                 stored_judge_time,
                 released_timelimit,
                 released_judge_time,
                 lora,
                 deamon_pass = "/home/pi/ARLISS_IBIS/IB/log/Performance_log.txt",
                 use_other_param_config = False):
        
        self.lora = lora
        
        if use_other_param_config:
            json_pass_other_param = "/home/pi/ARLISS_IBIS/IB/config/matsudo_config/other_param_matsudo_config.json"
            f = open(json_pass_other_param , "r")
            other_param = json.load(f)
            self.light_threshold = float(other_param["light_threshold"])
            self.stored_timelimit = float(other_param["stored_timelimit"])
            self.stored_judge_time = float(other_param["stored_judge_time"])
            self.released_timelimit = float(other_param["released_timelimit"])
            self.released_judge_time = float(other_param["released_judge_time"])
            f.close()
        else:
            self.light_threshold = light_threshold
            self.stored_timelimit = stored_timelimit
            self.stored_judge_time = stored_judge_time
            self.released_timelimit = released_timelimit
            self.released_judge_time = released_judge_time
    
        self.deamon_pass = deamon_pass
        self.deamon_file = open(self.deamon_pass)
        self.deamon_log = self.deamon_file.read()
        self.spi_open()
        
        logger_info.info("Light initialized")
        
    
    def spi_open(self):
    
        self.spi = spidev.SpiDev()     
        self.spi.open(0, 0)                    
        self.spi.max_speed_hz = 1000000 
        
    
    def spi_close(self):
        
        self.spi.close()
        
        
    def get_light_val(self):
    
        resp = self.spi.xfer2([0x68, 0x00])                 
        value = ((resp[0] << 8) + resp[1]) & 0x3FF  
        # if value == 0:
        #     value = float("nan")
        return value         
    
    
    async def stored_judge(self):
    
        if "Stored judge finish" in self.deamon_log:
            logger_info.info("Skipped stored judge")
            await self.lora.write("12")
            return
        
        else:
            logger_info.info("-------------------- Stored judge start --------------------")
            await self.lora.write("10")

            start_time = time.perf_counter()
            duration_start_time = time.perf_counter()
            is_continue = False
            pre_time_stamp = 0

            while True:


                light_val = self.get_light_val()
                time_stamp = time.perf_counter() - duration_start_time
                if abs(pre_time_stamp - time_stamp) > 0.4:
                    pre_time_stamp = time_stamp
                    logger_info.info("{:5.1f}| Light Value:{:>3d}, Continuation:{}".format(time_stamp, light_val, is_continue))
                    
                
                if light_val < self.light_threshold:
                    pass
                
                else:
                    is_continue = False
                    continue

                if is_continue:

                    duration_time = time.perf_counter() - duration_start_time

                    if duration_time > self.stored_judge_time:
                        logger_info.info("-- Light Judge")
                        await self.lora.write("110")
                        break
                
                elif light_val < self.light_threshold:
                    is_continue = True
                    duration_start_time = time.perf_counter()
                
                elapsed_time = time.perf_counter() - start_time

                if elapsed_time > self.stored_timelimit:
                    logger_info.info("-- Timer Judge")
                    await self.lora.write("112")
                    break

            logger_info.info("-------------------- Stored judge finish --------------------")


    async def released_judge(self):
        
        if "Released judge finish" in self.deamon_log:
            logger_info.info("Skipped released judge")
            await self.lora.write("22")
            return
        
        else:
            logger_info.info("-------------------- Released judge start --------------------")
            await self.lora.write("20")

            start_time = time.perf_counter()
            duration_start_time = time.perf_counter()
            is_continue = False
            pre_time_stamp = 0


            while True:

                light_val = self.get_light_val()
                time_stamp = time.perf_counter() - duration_start_time
                if abs(pre_time_stamp - time_stamp) > 0.4:
                    pre_time_stamp = time_stamp
                    logger_info.info("{:5.1f}| Light Value:{:>3d}, Continuation:{}".format(time_stamp, light_val, is_continue))
                    
                if is_continue:
                    
                    if light_val > self.light_threshold:
                        pass
                    
                    else:
                        is_continue = False
                        continue

                    duration_time = time.perf_counter() - duration_start_time

                    if duration_time > self.released_judge_time:
                        logger_info.info("-- Light Judge")
                        await self.lora.write("210")
                        break
                
                elif light_val > self.light_threshold:
                    is_continue = True
                    duration_start_time = time.perf_counter()
                
                elapsed_time = time.perf_counter() - start_time

                if elapsed_time > self.released_timelimit:
                    logger_info.info("-- Timer Judge")
                    await self.lora.write("212")
                    break

            logger_info.info("-------------------- Released judge finish --------------------")


    def __del__(self):
        
        self.spi_close()
