#!/usr/bin/env python3

import asyncio

from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)
import time #時間制御用モジュール
import spidev #SPI通信のモジュール
import serial

 #光センサのしきい値の設定
bright_border=350
bright_border_low=0
bright_border_high=800
    

latitude_start=35.7963106
longitude_start=139.89165
altitude_start=3

waitSecond=12
lightSecond=0.2
hidenoriSecond=120

# flag=False

latitude_end=35.7953796

longitude_end=139.890972
altitude_end_hover=3

async def run():

    
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    # await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    mission_items = []
    mission_items.append(MissionItem(latitude_start,
                                     longitude_start,
                                     altitude_start,
                                     0,
                                     False,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))
    mission_items.append(MissionItem(latitude_end,
                                     longitude_end,
                                     altitude_end_hover,
                                     0,
                                     False,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))

    mission_items.append(MissionItem(latitude_start,
                                     longitude_start,
                                     altitude_start,
                                     0,
                                     False,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))
    

    

    mission_plan = MissionPlan(mission_items)

    await drone.mission.set_return_to_launch_after_mission(False)

    print("-- Uploading mission")
    await drone.mission.upload_mission(mission_plan)

    while True:
       try:
           ser = serial.Serial('/dev/ttyAMA0',19200,timeout=1)
       except:
           print ("Serial port error. Waiting.")
           time.sleep(5)
       else:
           break
    print ("Serial port OK.") 

    ser.write(b'1\r\n')
    time.sleep(10)
    ser.write(b'z\r\n')
    time.sleep(10)

    ser.write(("Let's GO\r\n").encode())

    print("READY")


    print_mission_progress_task = asyncio.ensure_future(print_mission_progress(drone))
    print_flight_mode_task = asyncio.ensure_future(print_position(drone,ser))



    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break


    print("-- Arming")
    await drone.action.arm()

    print("-- Starting mission")
    await drone.mission.start_mission()


    while True:
        await asyncio.sleep(1)
        mission_finished = await drone.mission.is_mission_finished()
        if mission_finished:
            break
        

    await drone.action.land()

    await asyncio.sleep(10)

    # await drone.action.land()

    # await termination_task


async def print_mission_progress(drone):
    async for mission_progress in drone.mission.mission_progress():
        print(f"Mission progress: "
              f"{mission_progress.current}/"
              f"{mission_progress.total}")
              
async def print_position(drone,ser):
    async for position in drone.telemetry.position():
        latitude = position.latitude_deg 
        longitude = position.longitude_deg
        altitude = position.relative_altitude_m
        lat=str(latitude)[0:9]
        lon=str(longitude)[0:9]
        alt=str(altitude)[0:9]
        print(lat+","+lon)
        ser.write((lat+","+lon +","+alt+ "\r\n").encode())
        await asyncio.sleep(10)




# async def observe_is_in_air(drone, running_tasks):
#     """ Monitors whether the drone is flying or not and
#     returns after landing """

#     was_in_air = False

    # async for is_in_air in drone.telemetry.in_air():
    #     if is_in_air:
    #         was_in_air = is_in_air

    #     if was_in_air and not is_in_air:
    #         for task in running_tasks:
    #             task.cancel()
    #             try:
    #                 await task
    #             except asyncio.CancelledError:
    #                 pass
    #         await asyncio.get_event_loop().shutdown_asyncgens()

    #         return


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
