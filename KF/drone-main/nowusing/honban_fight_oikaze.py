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
    

waitSecond=277
lightSecond=0.2
hidenoriSecond=240

# flag=False

latitude_end=40.9004985

longitude_end=-119.0791373
altitude_end_hover=5

async def run():
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
        hikariSumLow += ((resp[0]<<8)+resp[1])&0x3FF #値を10ビット数値に変換

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

    mission_items = []
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

   
    #ループの中で値を読み込んで判定
    cds_time=time.process_time() #現在の時刻を取得
    while True:
        resp=spi.xfer2([0x68,0x00]) #SPI通信で値を読み込む
        volume=((resp[0]<<8)+resp[1])&0x3FF #値を10ビット数値に変換
        # print(volume) #変換した値をPRINT
        if volume < bright_border: #しきい値よりセンサの値が低かったら時間リセット
            cds_time=time.process_time()
        if time.process_time() > (cds_time + lightSecond):#5秒間しきい値を超えたらループ脱出
            spi.close()
            break
    
    start=time.time()



    print("waiting for pixhawk to hold")
    flag = False
    while True:
       if flag==True:
           break
       async for flight_mode in drone.telemetry.flight_mode():
           if str(flight_mode) == "HOLD":
               print("hold確認")
               flag=True
               break
           else:
               try:
                   await drone.action.hold()
               except Exception as e:
                   print(e)
                   drone = System()
                   await drone.connect(system_address="serial:///dev/ttyACM0:115200")
                   print("Waiting for drone to connect...")
                   async for state in drone.core.connection_state():

                        if state.is_connected:
                            
                            print(f"-- Connected to drone!")
                            break
                   mission_items = []
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
                   
                   break
                   




    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print_flight_mode_task = asyncio.ensure_future(print_position(drone,ser))
 

    while True:
        time.sleep(0.01)
        if time.time()-start > waitSecond-10:
            print("10秒前やで")
            break

    while True:
        time.sleep(0.01)
        if time.time()-start > waitSecond-3:
            print("3秒前やで")
            break

    while True:
        time.sleep(0.01)
        if time.time()-start > waitSecond-2:
            print("2秒前やで")
            break

    while True:
        time.sleep(0.01)
        if time.time()-start > waitSecond-1:
            print("1秒前やで")
            break

    while True:
        await asyncio.sleep(0.01)
        if time.time()-start > waitSecond:
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
        await asyncio.sleep(13)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
