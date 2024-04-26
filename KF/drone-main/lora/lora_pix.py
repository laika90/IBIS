#!/usr/bin/env python3

import asyncio
import re
from threading import Timer
import serial
import time

from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)

latitude_end=35.7958674
longitude_end=139.891334
altitude_start=3

latitude_start=35.7963106
longitude_start=139.89165
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
                               
    
    mission_items.append(MissionItem(latitude_end,
                                     longitude_end,
                                     0.5,
                                     0,
                                     True,
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
    print_altitude_task = asyncio.ensure_future(print_altitude(drone))
    print_mission_progress_task = asyncio.ensure_future(print_mission_progress(drone))
   

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

async def print_altitude(drone):
    """ Prints the altitude when it changes """

    while True:
        try:
            ser = serial.Serial('/dev/ttyAMA0',19200,timeout=1)
        except:
            print ("Serial port error. Waiting.")
            time.sleep(5)
        else:
            break
    print ("Serial port OK. Waiting for reset.")

    ser.write(b'1\r\n')
    Timer.sleep(3)
    ser.write(b'z\r\n')
    Timer.sleep(7)

    ser.write(("Let's GO\r\n").encode())

    print("READY")

    await asyncio.sleep(0.1)

    while True:
        previous_altitude = 0.0

        async for position in drone.telemetry.position():
            altitude = position.relative_altitude_m
            if abs(previous_altitude - altitude) >= 0.1:
                previous_altitude = altitude
                print(f"Altitude: {altitude}")
                ser.write((altitude + "\r\n").encode())


    
            

async def print_mission_progress(drone):
    async for mission_progress in drone.mission.mission_progress():
        print(f"Mission progress: "
              f"{mission_progress.current}/"
              f"{mission_progress.total}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
