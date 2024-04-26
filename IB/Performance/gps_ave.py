import asyncio
import numpy as np
from mavsdk import System


async def run():
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")

    lat_lst = []
    lng_lst = []
    for _ in range(10):
        lat, lng = await get_gps(drone)
        print(f"lat:{lat},lng:{lng}")
        lat_lst.append(lat)
        lng_lst.append(lng)
    lat_l = np.array(lat_lst)
    lng_l = np.array(lng_lst)

    print(f"lat_ave:{np.average(lat_l)},lng_ave:{np.average(lng_l)}")
    


async def get_gps(drone):
    async for position in drone.telemetry.position():
        lat = position.latitude_deg
        lng = position.longitude_deg
        break
    return lat, lng


if __name__ == "__main__":
    asyncio.run(run())