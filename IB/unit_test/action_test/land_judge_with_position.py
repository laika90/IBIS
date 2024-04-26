import time
from mavsdk import System
import asyncio

is_landed = False

async def land_judge(drone):
    
    global is_landed
    start_time = time.time()
    
    while True:
        
        time_now = time.time()
        await asyncio.sleep(0)
        
        if time_now-start_time < 30:
            try :
                alt_now = await(asyncio.wait_for(get_distance_alt(drone), timeout = 0.8))
            except asyncio.TimeoutError:
                print("Too high or distance sensor might have some error")
                true_posi = IQR_removal(await get_alt_list(drone, "POSITION"))
                if len(true_posi) == 0:
                    continue
                try:
                    ave = sum(true_posi)/len(true_posi)
                except ZeroDivisionError as e:
                    print("GPS can't catch or pixhawk might have some error")
                    continue
                for position in true_posi:
                    if abs(ave-position) > 0.1:
                        print("-- Moving")
                        continue
                else:
                    is_landed = True
                
            if is_judge_alt(alt_now):
                true_dist = IQR_removal(await get_alt_list(drone, "LIDAR"))
                if len(true_dist) == 0:
                    continue
                try:
                    ave = sum(true_dist)/len(true_dist)
                except ZeroDivisionError as e:
                    print(e)
                    continue
                
                if is_low_alt(ave):
                    for distance in true_dist:
                        if abs(ave-distance) > 0.01:
                            print("-- Moving")
                            break
                    if is_landed:
                        print("-- Lidar Judge")
                        break
                else:
                    print("-- Over 1m")
        else:
            is_landed = True
            if is_landed:
                print("-- Timer Judge")
                break
                
    
    print("####### Land judge finish #######")
    
    
def is_low_alt(alt):
    
    if alt < 1:
        return True
    else:
        return False


def is_judge_alt(alt):
    
    if alt < 15:
        print("####### Land judge start #######")
        return True
    else:
        return False
        
        
async def get_alt_list(drone, priority):
    
    altitude_list = []
    iter = 0
    while True:
        if priority == "LIDAR":
            try :
                distance = await asyncio.wait_for(get_distance_alt(drone), timeout = 0.8)
            except asyncio.TimeoutError:
                print("Too high or distance sensor might have some error")
                altitude_list =[]
                return altitude_list
            altitude_list.append(distance)
            
        elif priority == "POSITION":
            try:
                position = await asyncio.wait_for(get_position_alt(drone), timeout = 0.8)
            except asyncio.TimeoutError:
                print("GPS can't catch or pixhawk might have some error")
                altitude_list =[]
                return altitude_list
            altitude_list.append(position)
            
        iter += 1
        if iter >= 30:
            break
    return altitude_list
        

def IQR_removal(data):
    
    try:
        data.sort()
        quartile_25 = (data[7]+data[8])/2
        quartile_75 = (data[22]+data[23])/2
        IQR = quartile_75-quartile_25
        true_data = [i for i in data if quartile_25-1.5*IQR <= i <= quartile_75+1.5*IQR]
    except IndexError as e:
        print(e)
        true_data = []
    return true_data


async def print_alt(drone):
    
    while True:
        try:
            position = await asyncio.wait_for(get_position_alt(drone), timeout = 0.8)
            print("altitude:{}".format(position))
        except asyncio.TimeoutError:
            print("Pixhawk might have some error")
        if is_landed:
            return
        await asyncio.sleep(0)
        

async def get_distance_alt(drone):
    
    async for distance in drone.telemetry.distance_sensor():
        return distance.current_distance_m
    

async def get_position_alt(drone):
    
    async for position in drone.telemetry.position():
        return position.abs_altitude_m
    
    
async def run():
    
    drone = System()
    land_judge(drone)