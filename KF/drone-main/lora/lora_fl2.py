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

    await asyncio.sleep(300)



async def print_flight_mode(drone):
    """ Prints the flight mode when it changes """

    async for flight_mode in drone.telemetry.flight_mode():
        
        print(f"Flight mode: {flight_mode}")
        ser.write((str(flight_mode) + "\r\n").encode())
        await asyncio.sleep(10)



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
