import asyncio
from mavsdk import System
import time
import csv
import datetime

async def run():
    start = time.time()
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
    while True:
        async for position in drone.telemetry.position():
            latitude_list.append(position.latitude_deg)
            longitude_list.append(position.longitude_deg)
            break #async forのループから抜け出す
        now = time.time()
        if now-start>10:
            break
    dt_now = datetime.datetime.now()
    with open(f"/home/pi/ARLISS_IBIS/log/log_csv/gps_test {dt_now}.csv","w") as file:
        writer = csv.writer(file)
        writer.writerow(latitude_list)
        writer.writerow(longitude_list)
    

if __name__ == "__main__":
    #run()関数を一度だけ実行する
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
