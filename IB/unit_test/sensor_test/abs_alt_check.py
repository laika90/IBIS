#!/usr/bin/env python3
import asyncio
from mavsdk import System
import time
import datetime
import csv

async def run():
    start = time.time()
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break
    # center_lat_deg_list = []
    # center_lng_deg_list = []
    # async for _ in range(10):
    #     async for position in drone.telemetry.position():
    #         lat_deg = position.latitude_deg
    #         lng_deg = position.longitude_deg
    #         center_lat_deg_list.append(lat_deg)
    #         center_lng_deg_list.append(lng_deg)
    #         break
    # print("got gps")

    # center_lat_deg_ave = sum(center_lat_deg_list)/10
    # center_lng_deg_ave = sum(center_lng_deg_list)/10
    
    # center = [center_lat_deg_ave, center_lng_deg_ave]
    # print(f"中心の緯度={center[0]}")
    # print(f"中心の経度={center[1]}")
    
    init_abs_alt=0
    async for position in drone.telemetry.position():
        init_abs_alt=position.absolute_altitude_m
        print(init_abs_alt)
        break

    rel_alt_lst=[]
    lidar_lst=[]
    while True:
        async for distance in drone.telemetry.distance_sensor():
            lidar_lst.append(distance.current_distance_m)
            break
        async for position in drone.telemetry.position():
            abs_alt = position.absolute_altitude_m
            rel_alt = abs_alt - init_abs_alt
            rel_alt_lst.append(rel_alt)
            break
        now = time.time()
        if now-start>90:
            break
    dt_now = datetime.datetime.now()
    with open(f"/home/pi/ARLISS_IBIS/log/log_csv/gps_test {dt_now}.csv","w") as file:
        writer = csv.writer(file)
        writer.writerow(rel_alt_lst)
        writer.writerow(lidar_lst)

if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())
