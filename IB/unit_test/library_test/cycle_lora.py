import sys
import asyncio

ibis_directory = "/home/pi/ARLISS_IBIS/IB/Library"
sys.path.append(ibis_directory)

from lora import Lora


lora_power_pin = 4
lora_sleep_time = 3


async def cycle_lora(lora):
    
    while True:
        lora.write("lat:error")
        await asyncio.sleep(3)
        lora.write("lng:error")
        await asyncio.sleep(3)
        lora.write("alt:error")
        await asyncio.sleep(3)
        

async def print_num():
    
    while True: