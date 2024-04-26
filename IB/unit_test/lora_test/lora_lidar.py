import serial
import time
from mavsdk import System
import asyncio

system_address = "serial:///dev/ttyACM0:115200"
dist = "start"

def Serial_connect():
    while True:
        try:
            ser = serial.Serial('/dev/ttyS0', 115200, timeout=1)
        except:
            print ("Serial port error. Waiting.")
            time.sleep(5)
        else:
            break
    print ("Serial port OK.")
    ser.write(b'2\r\n')
    time.sleep(1)
    ser.write(b'z\r\n')
    time.sleep(1)
    ser.write(("Let's GO\r\n").encode())
    time.sleep(1)
    print("READY")
    return ser

async def Write_distance(ser):
    global dist
    while True:
        print("sending : {}".format(dist))
        bufw = dist
        ser.write((bufw+"\r\n").encode())
        time.sleep(3)
        await asyncio.sleep(0.5)
        
async def Get_distance(drone):
    global dist
    while True:
        async for distance in drone.telemetry.distance_sensor():
            dist = str(distance.current_distance_m)
            await asyncio.sleep(0)
            break
        
async def main():
    drone = System()
    print("Waiting for drone to connect...")
    await drone.connect(system_address)
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break
    serial = Serial_connect()
    get_dist_task = asyncio.ensure_future(Get_distance(drone))
    write_task = asyncio.ensure_future(Write_distance(serial))
    await get_dist_task
    await write_task
    
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())