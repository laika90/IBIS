#!/usr/bin/env python3

import asyncio

from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)
import time #時間制御用モジュール
import spidev #SPI通信のモジュール

 #光センサのしきい値の設定
bright_border=250

bright_border_low=0
bright_border_high=800
    

latitude_end=35.715496
longitude_end=139.76137079999998
altitude_start=3

latitude_start=35.715496
longitude_start=139.76137079999998
altitude_end_hover=3

waitSecond=11.935
lightSecond=0.2
hidenoriSecond=120


async def run():
    spi=spidev.SpiDev() #インスタンス生成
    spi.open(0,0) #CE0（24番ピン）に接続したデバイスと通信を開始
    spi.max_speed_hz=1000000 #転送速度を指定

    hikariSumHigh=0
    for i in range(100):
        resp=spi.xfer2([0x68,0x00]) #SPI通信で値を読み込む
        hikariSumHigh += ((resp[0]<<8)+resp[1])&0x3FF 
    
    bright_border_high = hikariSumHigh/100

    print("high読み取り完了")
    print(bright_border_high)

    await asyncio.sleep(hidenoriSecond)

    print("lowデータ読み始めるだよ")

    hikariSumLow=0
    for i in range(100):
        resp=spi.xfer2([0x68,0x00]) #SPI通信で値を読み込む
        hikariSumLow=((resp[0]<<8)+resp[1])&0x3FF #値を10ビット数値に変換

    bright_border_low=hikariSumLow/100

    print("low読み取り完了")
    print(bright_border_low)

    bright_border=(bright_border_low + bright_border_high)/2
    print(bright_border)
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    # await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

   

    # running_tasks = [print_mission_progress_task]
    # termination_task = asyncio.ensure_future(
    #     observe_is_in_air(drone, running_tasks))

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



    #SPI通信のための準備
    # spi=spidev.SpiDev() #インスタンス生成
    # spi.open(0,0) #CE0（24番ピン）に接続したデバイスと通信を開始
    # spi.max_speed_hz=1000000 #転送速度を指定

    #bright_border=(hikari_high + hikari_low)/2
    #ループの中で値を読み込んで判定
    cds_time=time.process_time() #現在の時刻を取得
    while True:
        resp=spi.xfer2([0x68,0x00]) #SPI通信で値を読み込む
        volume=((resp[0]<<8)+resp[1])&0x3FF #値を10ビット数値に変換
        print(volume) #変換した値をPRINT

        # async for flight_mode in drone.telemetry.flight_mode():
        # if str(flight_mode) != "HOLD":
        #     try:
        #          drone.action.hold()
        #     except:
        #         pass
        
        if volume < bright_border: #しきい値よりセンサの値が低かったら時間リセット
            cds_time=time.process_time()
        if time.process_time() > (cds_time + hikariSecond):#5秒間しきい値を超えたらループ脱出
            spi.close()
            break
    
    start=time.time()

    print_mission_progress_task = asyncio.ensure_future(print_mission_progress(drone))

    # print("waiting for pixhawk to hold")
    # flag = False
    # while True:
    #     if flag==True:
    #         break
    #     async for flight_mode in drone.telemetry.flight_mode():
    #         if str(flight_mode) == "HOLD":
    #             print("hold確認")
    #             flag=True
    #             break
    #         else:
    #             try:
    #                 await drone.action.hold()
    #             except Exception as e:
    #                 print(e)
    #     await asyncio.sleep(0.5)
   

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    # await asyncio.sleep(waitSecond)
    # while True:
    #     asyncio.sleep(0.01)
    #     if time.time()-start > waitSecond:
    #         break
            
        

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
