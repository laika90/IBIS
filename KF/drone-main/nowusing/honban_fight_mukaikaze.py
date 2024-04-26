#元々KFの人たちが書いたコメントと俺らが推測で追加したコメントとが混ざらないように(KF)と書いておきました
#見た感じ、多い風と向かい風のコード一緒

#!/usr/bin/env python3(KF)

import asyncio #非同期I/O:平行処理を行う(int main 二つを動かす)
               #sleepの値によって同期のタイミングを測っている(await)
               #main関数にあたる処理をasync付きで記述する
               #for文にもついてるから、同期したい(タイミングを合わせたいものの前につけるのかも)
               #https://docs.python.org/ja/3/library/asyncio.html 

from mavsdk import System #ドローンからテレメトリーを取得する?
                          #ドローンの通信に使うライブラリ
                          #https://tomofiles.hatenablog.com/entry/2019/10/14/113348 
                          #http://mavsdk-python-docs.s3-website.eu-central-1.amazonaws.com/system.html#mavsdk.system.System.connect
from mavsdk.mission import (MissionItem, MissionPlan) #ドローンの状態を理解するclass
                                                      #MisssionItem
                                                      #  specify a position, altitude, fly-through behaviour, camera action, gimbal position, and the speed などを配列の要素として指定
                                                      #  class mavsdk.mission.MissionItem(latitude_deg, longitude_deg, relative_altitude_m, speed_m_s, is_fly_through, gimbal_pitch_deg, gimbal_yaw_deg, camera_action, loiter_time_s, camera_photo_interval_s, acceptance_radius_m, yaw_deg, camera_photo_distance_m)
                                                      #MissionPlan
                                                      #  class mavsdk.mission.MissionPlan(mission_items)
                                                      #http://mavsdk-python-docs.s3-website.eu-central-1.amazonaws.com/plugins/mission.html

#mavsdkのサイト
#http://mavsdk-python-docs.s3-website.eu-central-1.amazonaws.com/index.html

import time #時間制御用モジュール(KF)
import spidev #SPI通信のモジュール(KF) #raspi内でしかインストールできなそう
import serial  #シリアル通信モジュール

 #光センサのしきい値の設定(KF)　いらない
bright_border=350
bright_border_low=0
bright_border_high=800
    

waitSecond=25
lightSecond=0.2
hidenoriSecond=10 #ケースに入れたりする作業時間

# flag=False(KF)
# ゴール地点の緯度、経度
latitude_end=40.9004985

longitude_end=-119.0791373
altitude_end_hover=5
altitude_end_first=2000

async def run(): #asyncをつけることで平行処理
    #ここから、通信、高度、座標のsetup
    #LoRa 設定モード、実際に書き込むモード
    while True:  #シリアルデータ受信。通信が来るまで受信を続けるためのwhile True
                 #https://engineer-lifestyle-blog.com/code/python/pyserial-communication-usage/
       try:
           ser = serial.Serial('/dev/ttyAMA0',19200,timeout=1) #(シリアルポート, ボーレート, タイムアウト設定(読み取り操作が完了していないときにタイムアウトになるまで時間)) 
       except:
           print ("Serial port error. Waiting.")
           time.sleep(5) #timeモジュールのsleep関数。処理を一時停止できる(5秒) 
       else:
           break              #通信がとれたら抜ける
    print ("Serial port OK.") #通信がとれたことを出力

    #通信完了

# 初期化されている場合に備えて（1とzを押さなきゃいけない）
    ser.write(b'1\r\n') #writeメソッドでシリアルデータを送信(bで文字列をバイト型に) 
    time.sleep(10)
    ser.write(b'z\r\n')
    time.sleep(10)

    ser.write(("Let's GO\r\n").encode()) #encodeも文字列をバイト型にしてるらしい
                                         #https://ameblo.jp/hitochan007/entry-12103254519.html 
    print("READY") #通信がつながってここからスタート？

    spi=spidev.SpiDev() #インスタンス生成(KF) #spi通信に使うインスタンス https://pypi.org/project/spidev/ 
    spi.open(0,0) #CE0（24番ピン）に接続したデバイスと通信を開始(KF)
    spi.max_speed_hz=1000000 #転送速度を指定(KF)

    hikariSumHigh=0 
    for i in range(100): #100回光センサで読み込み、平均を出す
        resp=spi.xfer2([0x68,0x00]) #SPI通信で値を読み込む(KF)
        hikariSumHigh += ((resp[0]<<8)+resp[1])&0x3FF 
    
    bright_border_high = hikariSumHigh/100

    print("high読み取り完了") #光センサの最大値を読んでる
    print(bright_border_high)

    await asyncio.sleep(hidenoriSecond)

    print("lowデータ読み始めるだよ") #光センサの最低値を読んでる
 
    hikariSumLow=0
    for i in range(100):
        resp=spi.xfer2([0x68,0x00]) #SPI通信で値を読み込む(KF)
        hikariSumLow += ((resp[0]<<8)+resp[1])&0x3FF #値を10ビット数値に変換(KF)

    bright_border_low=hikariSumLow/100

    print("low読み取り完了")
    print(bright_border_low)

    bright_border=(bright_border_low + bright_border_high)/2 #平均をとって採用
    print(bright_border)
    #Pixhawkと通信開始
    drone = System() #mavsdkに用意されたSystem classの初期化メソッド
    await drone.connect(system_address="serial:///dev/ttyACM0:115200") #System classのメンバ関数だと思うけど見つからない 
                                                                       #ドローンとの接続をシリアル通信で行う関数?
    # await drone.connect(system_address="udp://:14540")udp...でガゼボに繋がる

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state(): #connection_state:接続の状態を書き込む
                                                      #http://mavsdk-python-docs.s3-website.eu-central-1.amazonaws.com/plugins/core.html
        if state.is_connected: #is_connected:bool値を与える。connected or disconnected
            print(f"-- Connected to drone!")
            break

# way pointをappend
    mission_items = []
    mission_items.append(MissionItem(latitude_end,
                                     longitude_end, 
                                     altitude_end_first, 
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

    #位置情報完了

    await drone.mission.set_return_to_launch_after_mission(False) #RTL(return-to-launch)状態に移行する(True時) RTLでもどって来ないようにfalse

    print("-- Uploading mission")
    await drone.mission.upload_mission(mission_plan)

   
    #光センサー
    #ドローン軌道の条件を待っている
    #ループの中で値を読み込んで判定(KF)
    cds_time=time.process_time() #現在の時刻を取得(KF)
    while True:
        resp=spi.xfer2([0x68,0x00]) #SPI通信で値を読み込む(KF)
        volume=((resp[0]<<8)+resp[1])&0x3FF #値を10ビット数値に変換(KF)
        # print(volume) #変換した値をPRINT(KF)
        if volume < bright_border: #しきい値よりセンサの値が低かったら時間リセット(KF)
            cds_time=time.process_time()
        if time.process_time() > (cds_time + lightSecond):#lightsecond=0.2秒間しきい値を超えたらループ脱出(KF)
            spi.close()
            break

    #光センサ完了
    
    #タイマースタート
    start=time.time()


    #hold mode(じゃないとtake offとかできない)に入る (高度と座標を維持する定常飛行)　外れちゃうかもだからもう一回やる
    print("waiting for pixhawk to hold")
    flag = False #MAVSDKではTrueって出るけどFalseが出ない場合もあるから最初からFalseにしてる
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
                   await drone.action.hold() #holdじゃない状態からholdしようてしても無理だからもう一回exceptで繋ぎなおす
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
                                     altitude_end_first,
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
                   #await asyncio.sleep(0.5)(KF)
                   break 




    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health(): #どうせ落ちるだけだからあんま意味ない
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break
    
    print_flight_mode_task = asyncio.ensure_future(print_position(drone,ser)) #print_positionが繰り返されてたからちゃんとタスク化されてたらしい
 

    while True:
        time.sleep(0.01)
        if time.time()-start > waitSecond-10: #10秒待つだけだと他の処理が入った時に時間がずれるから、0.01秒待つっていうのを700回繰り返してる
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
            
    #アイドリング
    print("-- Arming")
    await drone.action.arm() #１０秒後に勝手にdisarm

    #指示されたmissionを開始
    print("-- Starting mission")
    await drone.mission.start_mission()


    while True:
        await asyncio.sleep(1)
        mission_finished = await drone.mission.is_mission_finished() #finishedになったら（falseを入れてくれない）並行処理だとすぐlandしちゃう
        if mission_finished:
            break
        

    await drone.action.land()

    await asyncio.sleep(10) #なくてもいい

    # await drone.action.land()(KF)

    # await termination_task(KF)


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


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
