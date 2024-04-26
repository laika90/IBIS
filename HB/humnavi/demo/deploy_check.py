import asyncio
import os
import sys

import aiorun

sys.path.append(os.getcwd())

from humnavi.light import LightSensor


async def main(threshold):
    main_coroutines = [light.cycle_light_naive_carefully(threshold)]

    await asyncio.gather(*main_coroutines)


if __name__ == "__main__":
    light = LightSensor()
    "initialized!"
    print("type threshold for oepn_arm")
    threshold = int(input())
    aiorun.run(main(threshold))
