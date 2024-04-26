import json
import os

import matplotlib.pyplot as plt
import numpy as np

LOG_PATH = os.path.abspath("log")
if __name__ == "__main__":
    print("Input the date for the log. e.g.) 2022-07-15")
    date = input()
    print("Input the number for the log e.g.) 1")
    log_idx = input()
    file_name = LOG_PATH + "/" + date + "/" + log_idx.zfill(3) + ".json"
    with open(file_name, mode="r") as f:
        log_dict = json.load(f)
    print("Input the key for visualizer.")
    print("if you choose x_m_gps or y_m_gps, output is (x, y) instead of (value, time)")
    print("options:" + str(log_dict.keys()))
    key = input()
    if key == "x_m_gps" or key == "y_m_gps":
        plt.scatter(
            log_dict["x_m_gps"][0], log_dict["y_m_gps"][0], label="start", c="b"
        )
        plt.scatter(
            log_dict["x_m_gps"][-1], log_dict["y_m_gps"][-1], label="goal", c="r"
        )
        plt.plot(log_dict["x_m_gps"], log_dict["y_m_gps"], label="route", c="black")
        plt.xlabel("x_m_gps")
        plt.ylabel("y_m_gps")
        plt.legend()
        plt.xlim(min(log_dict["x_m_gps"]) - 1, max(log_dict["x_m_gps"]) + 1)
        plt.ylim(min(log_dict["y_m_gps"]) - 1, max(log_dict["y_m_gps"]) + 1)
    else:
        T = len(log_dict[key]) / 2
        print("duration time: ", T)
        t = np.linspace(0, T, len(log_dict[key]))
        plt.plot(t, log_dict[key])
        plt.xlabel("time [s]")
        plt.xlim(0, T * 1.1)
    plt.show()
