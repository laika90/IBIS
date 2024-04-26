#!/usr/bin/env python3(KF)

import asyncio

from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)

#高度、緯度、経度の初期値
altitude_start=3

latitude_start=35.7963106
longitude_start=139.89165

async def run():
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    # await drone.connect(system_address="udp://:14540")(KF)

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break #接続完了

    mission_items = []
    mission_items.append(MissionItem(latitude_start, #latitude_deg
                                     longitude_start, #longitude_deg
                                     altitude_start, #relative_altitude_m
                                     0, #speed_m_s
                                     False, #is_fly_through
                                     float('nan'), #gimbal_pitch_deg
                                     float('nan'), #gimbal_yaw_deg
                                     MissionItem.CameraAction.NONE, #camera_action
                                     float('nan'), #loiter_time_s
                                     float('nan'), #camera_photo_interval_s
                                     float('nan'), #acceptance_radius_m
                                     float('nan'), #yaw_deg
                                     float('nan'))) #camera_photo_distance_m
    

    mission_plan = MissionPlan(mission_items)

    await drone.mission.set_return_to_launch_after_mission(False) #ミッション完了後にRTL（Return-to-Launch）に移行するかどうかを設定

    print("-- Uploading mission")
    await drone.mission.upload_mission(mission_plan) #mission itemをドローンにアップロード

    print_mission_progress_task = asyncio.ensure_future(print_mission_progress(drone))
   

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok: #2つの位置推定が”position control”モードで飛行するのに十分なら
            print("-- Global position estimate OK")
            break
        

    print("-- Arming")
    await drone.action.arm()

    print("-- Starting mission")
    await drone.mission.start_mission()

    await asyncio.sleep(10)

    # await drone.action.land()(KF)

    # await termination_task(KF)


async def print_mission_progress(drone):
    async for mission_progress in drone.mission.mission_progress(): 
#mission_progressのParameters:
#current (int32_t) – Current mission item index (0-based), if equal to total, the mission is finished
#total (int32_t) – Total number of mission items
        
        print(f"Mission progress: "
              f"{mission_progress.current}/"
              f"{mission_progress.total}")

#実行
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
