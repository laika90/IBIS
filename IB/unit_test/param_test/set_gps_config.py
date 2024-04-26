#使い方: 変更したいconfigのパスをfile_pathに代入してコード実行．waypoint_lat, waypoint_lngが自動的に置き換わる．
import asyncio
from mavsdk import System
import datetime
import json

async def run():

    # Init the drone
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    print("waiting for connect...")
    async for state in drone.core.connection_state():
        if state.is_connected : 
            print("rpi<->pix : connected!")
            break
    
    # Get GPS
    async for position in drone.telemetry.position():
        waypoint_lat = position.latitude_deg
        waypoint_lng = position.longitude_deg
        break #async forのループから抜け出す
    
    file_path = "/home/pi/ARLISS_IBIS/IB/config/matsudo_config/GPS_matsudo_condig.json"
    try:
        with open(file_path, mode="r") as f:
            waypoint = json.load(f)
        
        # set latitude and longitude
        waypoint["waypoint_lat"] = waypoint_lat
        waypoint["waypoint_lng"] = waypoint_lng
        
        # set time
        dt_now = datetime.datetime.now().isoformat()
        waypoint["set time"] = dt_now
        
        with open(file_path, mode="w") as f:
            json.dump(waypoint, f, indent=4)
            print("waypoint has been updated"+"\n"+json.dumps(waypoint, indent=2)) 
            
    except FileNotFoundError:
        print("file not found")
    except json.JSONDecodeError:
        print("file is not in correct JSON format")
    except Exception as e:
        print("error has occured:", e)
    

if __name__ == "__main__":
    #run()関数を一度だけ実行する
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())