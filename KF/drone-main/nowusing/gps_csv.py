#これはサンプルコードで、コピペしてよしなに活用することが期待されている

import csv
import asyncio
import pandas as pd
from mavsdk import System

async def run():
    #座標格納用配列
    latitude_list = []
    longitude_list = []

    # Init the drone
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    #await drone.connect(system_address="udp://:14540")
    print("waiting for connect...")
    async for state in drone.core.connection_state():
        if state.is_connected : 
            print("rpi<->pix : connected!")
            break
    
    #現在地を配列に格納(10要素)
    for i in range(10):
        async for position in drone.telemetry.position():
            latitude_list.append(position.latitude_deg)
            longitude_list.append(position.longitude_deg)
            print(longitude_list)
            break #async forのループから抜け出す

    #配列の要素の平均値を計算
    aveLat = sum(latitude_list) / len(latitude_list)
    aveLon = sum(longitude_list) / len(longitude_list)
    print(aveLat)
    print(aveLon)

    #csvに直近10ループのGPSデータの平均値を書き込み
    with open('../flags/gps_data.csv','w') as f:
        writer = csv.writer(f)
        writer.writerow([aveLat,aveLon])
    
    #csvに格納されたGPSデータを読み込んで変数に保存
    #例えば、スタートとゴールの座標をそれぞれcsvファイルから読み込むようにしておけば、書き込みコードを使って簡単に座標の変更が行える
    print("This is the csv data")
    csvdata = pd.read_csv('../flags/gps_data.csv',header=None,dtype=float)
    print("lat is")
    print(csvdata[0][0])
    print("lon is")
    print(csvdata[1][0])

if __name__ == "__main__":
    #run()関数を一度だけ実行する
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    #全て終わったことを一応プリント
    print("now stopped")

