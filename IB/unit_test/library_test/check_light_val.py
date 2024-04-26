import sys
import asyncio

ibis_directory = "/home/pi/ARLISS_IBIS/IB/Library"
sys.path.append(ibis_directory)

from light import Light
from lora import Lora

light_threshold = 100
stored_timelimit = 100
stored_judge_time = 100
released_timelimit = 100
released_judge_time = 100
lora_power_pin = 4
lora_sleep_time = 3

lora = Lora(lora_power_pin,
            lora_sleep_time,
            use_other_param_config = False)

light = Light(light_threshold,
            stored_timelimit,
            stored_judge_time,
            released_timelimit,
            released_judge_time,
            lora,
            deamon_pass = "/home/pi/ARLISS_IBIS/IB/log/Performance_log.txt",
            use_other_param_config = False)

async def run():
    await light.stored_judge()
    
asyncio.run(run())