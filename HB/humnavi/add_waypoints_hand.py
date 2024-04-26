import json

JSON_PATH = "./config/waypoints_gps.json"


def run():
    """
    add waypoints manually
    """
    print("location name rule: mission_number.zfill(3)  e.g.) noshiro_001")
    print("if it's the target, number = target e.g.) noshiro_target")
    location_name = input()
    print("latitude:")
    latitude = float(input())
    print("longitude:")
    longitude = float(input())
    print("abs_altitude:")
    abs_altitude = float(input())
    print("rel_altitude:")
    rel_altitude = float(input())
    print("lidar_altitude")
    target_alt = float(input())
    target_pos = [latitude, longitude, abs_altitude, rel_altitude, target_alt]
    with open(JSON_PATH, mode="r") as f:
        target_pos_dict = json.load(f)
    target_pos_dict[location_name] = target_pos
    with open(JSON_PATH, mode="w") as f:
        json.dump(target_pos_dict, f)


if __name__ == "__main__":
    run()
