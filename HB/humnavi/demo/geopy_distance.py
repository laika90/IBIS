import sys
import os
import json

sys.path.append(os.getcwd())

from humnavi.pixhawk import Pixhawk

if __name__ == "__main__":
    pixhawk = Pixhawk()
    with open("config/waypoints_gps.json", mode="r") as f:
        location_dict = json.load(f)
    print("target name e.g.) arliss_target")
    target_name = input()
    pixhawk.set_target_from_dict(location_dict, target_name)
    print("latitude")
    pixhawk.latitude_deg = float(input())
    print("longitude")
    pixhawk.longitude_deg = float(input())
    print(pixhawk.geopy_distance())
