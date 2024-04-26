import serial
import time
from mavsdk import System
import asyncio

system_address = "serial:///dev/ttyACM0:115200"
lat = "start"
lng = "start"
alt = "start"

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

async def Write_GPS(ser):
    while True:
        print("writing")
        latitude = "lat:" + lat + "\r\n"
        longitude = "lng:" + lng + "\r\n"
        altitude = "alt:" + alt + "\r\n"
        ser.write(latitude.encode())
        time.sleep(3)
        ser.write(longitude.encode())
        time.sleep(3)
        ser.write(altitude.encode())
        time.sleep(3)
        await asyncio.sleep(1)
        
async def Get_GPS(drone):
    global lat, lng, alt
    while True:
        try:
            await asyncio.wait_for(GPS(drone), timeout=0.8)
        except asyncio.TimeoutError:
            print("Can't catch GPS")
            lat = "error"
            lng = "error"
            alt = "error"
        await asyncio.sleep(1)
        
async def GPS(drone):
    global lat, lng, alt
    async for position in drone.telemetry.position():
            print(position)
            lat = str(position.latitude_deg)
            lng = str(position.longitude_deg)
            alt = str(position.absolute_altitude_m)
            break
        
async def main():
    drone = System()
    print("Waiting for drone to connect...")
    await drone.connect(system_address)
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("-- Connected to drone!")
            break
    serial = Serial_connect()
    get_GPS_task = asyncio.ensure_future(Get_GPS(drone))
    write_task = asyncio.ensure_future(Write_GPS(serial))
    await get_GPS_task
    await write_task
    
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())