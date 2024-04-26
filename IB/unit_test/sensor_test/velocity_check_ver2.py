#!/usr/bin/env python3

import asyncio
from mavsdk import System
import time
import datetime
import csv

v_list=[]
pb_list = []
async def run():
    start = time.time()
    # Init the drone
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")

    while True:
        async for v in drone.telemetry.velocity_ned():
            v_list.append(v)
            print(f"velocity:{v}")
            break
        async for o in drone.telemetry.odometry():
            pb = o.position_body
            pb_list.append(pb)
            print(f"position_body:{pb}")
            break


        now = time.time()
        if now-start>30:
            break



    dt_now = datetime.datetime.now()
    with open(f"/home/pi/ARLISS_IBIS/log/log_csv/velocity_check_ver2 {dt_now}.csv","w") as file:
        writer = csv.writer(file)
        writer.writerow(v_list)



    


if __name__ == "__main__":
    # Start the main function
    asyncio.run(run())