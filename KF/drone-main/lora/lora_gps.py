import asyncio

import re
import serial
import time
from mavsdk import System




async def run():
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    # await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

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
    time.sleep(10)
    ser.write(b'z\r\n')
    time.sleep(10)

    ser.write(("Let's GO\r\n").encode())

    print("READY")

    print_flight_mode_task = asyncio.ensure_future(print_position(drone,ser))

    await asyncio.sleep(300)

async def print_position(drone,ser):
    async for position in drone.telemetry.position():
        latitude = position.latitude_deg 
        longitude = position.longitude_deg
        print(str(latitude)+str(longitude))
        ser.write((str(latitude)+","+str(longitude) + "\r\n").encode())
        await asyncio.sleep(10)




if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
