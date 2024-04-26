import json
import os
import datetime
import matplotlib.pyplot as plt
from geopy import distance

LOG_PATH = os.path.abspath("log")
if __name__ == "__main__":
    print("Input the date for the log. e.g.) 2022-07-15")
    date = input()
    print("Input the number for the log e.g.) 1")
    log_idx = input()
    file_name = LOG_PATH + "/" + date + "/" + log_idx.zfill(3) + ".json"
    with open(file_name, mode="r") as f:
        log_dict = json.load(f)
    odometry_x_m_list = []
    odometry_y_m_list = []
    for i in range(len(log_dict["lng_deg"])):
        if log_dict["lng_deg"][i] == 0.0 or log_dict["target point"][i][0] == None:
            continue
        odometry_x_m = distance.distance(
            (log_dict["target point"][i][0], log_dict["target point"][i][1]),
            (log_dict["lat_deg"][i], log_dict["target point"][i][1]),
        ).meters
        odometry_y_m = distance.distance(
            (log_dict["target point"][i][0], log_dict["target point"][i][1]),
            (log_dict["target point"][i][0], log_dict["lng_deg"][i]),
        ).meters
        odometry_x_m_list.append(odometry_x_m)
        odometry_y_m_list.append(odometry_y_m)
    plt.scatter(odometry_x_m_list, odometry_y_m_list, label="route", c="y")
    plt.scatter(
        odometry_x_m_list[0], odometry_y_m_list[0], label="start point", c="red"
    )
    plt.scatter(
        odometry_x_m_list[-1], odometry_y_m_list[-1], label="finish point", c="blue"
    )
    plt.scatter(0, 0, label="target", c="green")
    plt.xlabel("x_m")
    plt.ylabel("y_m")
    plt.xlim(min(0, min(odometry_x_m_list)) - 1, max(0, max(odometry_x_m_list)) + 1)
    plt.ylim(min(0, min(odometry_y_m_list)) - 1, max(0, max(odometry_y_m_list)) + 1)
    tz_pdt = datetime.timezone(datetime.timedelta(hours=-7))
    for i in range(len(log_dict["unix time"])):
        if log_dict["unix time"][i] == 0.0:
            continue
        start_dt_pdt = datetime.datetime.fromtimestamp(log_dict["unix time"][i]/1e6, tz_pdt)
        break
    print("control start time:", start_dt_pdt)
    print(
        "control start point:",
        odometry_x_m_list[0],
        odometry_y_m_list[0],
        log_dict["rel_alt_m"][0],
    )
    finish_dt_pdt = datetime.datetime.fromtimestamp(log_dict["unix time"][-1]/1e6, tz_pdt)
    print("control finish time:", finish_dt_pdt)
    print(
        "control finish point:",
        odometry_x_m_list[-1],
        odometry_y_m_list[-1],
        log_dict["lidar"][-1],
    )
    print(
        "target point: ",
        log_dict["target point"][-1][0],
        log_dict["target point"][-1][1],
        0.0,
    )
    plt.legend()
    plt.show()
