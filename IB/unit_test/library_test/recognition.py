import sys
import numpy as np
import time

ibis_directory = "/home/pi/ARLISS_IBIS/IB/Library"
sys.path.append(ibis_directory)

from camera import Camera

hsv_min_1 = np.array([0, 0, 0])
hsv_max_1 = np.array([5,255,255])
hsv_min_2 = np.array([150,0,0])
hsv_max_2 = np.array([180,255,255])

def run():
    
    camera = Camera(hsv_min_1,
                    hsv_max_1,
                    hsv_min_2,
                    hsv_max_2)
        
    camera.change_iso(100)
    camera.change_shutter_speed(500)
    camera.take_pic()
    res = camera.detect_center()
    print('percent={}, center={}'.format(res['percent'], res['center']))

    # distance = 1
    # x_m, y_m = camera.get_target_position(distance)
    # print(f"x={x_m},y={y_m}")

run()
