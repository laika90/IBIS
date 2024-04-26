import json

JSON_PATH = "./config/waypoints_gps.json"


def run():
    """
    remove waypoints manually
    input waypoints name and remove
    """
    print("location name you want to remove:  e.g.) noshiro_001")
    location_name = input()
    with open(JSON_PATH, mode="r") as f:
        target_pos_dict = json.load(f)
    try:
        target_pos_dict.pop(location_name)
        print(location_name, "removed")
    except:
        print("no location called", location_name)
        print("remove failed")
    with open(JSON_PATH, mode="w") as f:
        json.dump(target_pos_dict, f)


if __name__ == "__main__":
    run()
