#!/usr/bin/env python3
# 北に20m→南に40m
import asyncio
import picamera
import cv2
import numpy as np
import datetime
from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)
from mavsdk.offboard import (OffboardError, PositionNedYaw)
from logger import logger_info, logger_debug

# パラメータ--------------------------------
goal = [40.19404418,140.05968388000002]
height = 6 # goalの高度
#-----------------------------------------

#　picameraの仕様--------------------------
pixel_number_x = 3296 #[mm]
pixel_number_y = 2521
pixel_size = 1.12 #[um]
f = 3.04 #[mm]
# ----------------------------------------

async def run():
    
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")

    logger_info.info("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            break
        # else:
        #     await drone.connect(system_address="serial:///dev/ttyACM0:115200")
        #     logger_info.info("Waiting for drone to connect...")
        #     async for state in drone.core.connection_state():
        #         if state.is_connected:
        #             print("2回目connect成功")
        #             break

        
    get_log_task = asyncio.ensure_future(get_log(drone))
    img_navigation_task = asyncio.ensure_future(img_navigation(drone))

    mission_items = []
    mission_items.append(MissionItem(goal[0],
                                     goal[1],
                                     height, # rel_alt
                                     5, # speed
                                     True, #止まらない
                                     float('nan'),
                                     float('nan'), #gimbal_yaw_deg
                                     MissionItem.CameraAction.NONE,
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan'),
                                     float('nan'))) #Absolute_yaw_deg, 45にするのこっちかも

    mission_plan = MissionPlan(mission_items)

    await drone.mission.set_return_to_launch_after_mission(False)

    logger_info.info("-- Uploading mission")

    await drone.mission.upload_mission(mission_plan)

    logger_info.info("Waiting for drone to have a global position estimate...")
    
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            logger_info.info("-- Global position estimate OK")
            break

    logger_info.info("-- Arming")
    await drone.action.arm()

    logger_info.info("-- Starting mission")
    await drone.mission.start_mission()

    await get_log_task
    await img_navigation_task
  
async def get_log(drone):
    while True:
        async for flight_mode in drone.telemetry.flight_mode():
            mode = flight_mode
            break
        async for distance in drone.telemetry.distance_sensor():
            lidar = distance.current_distance_m
            break
        async for position in drone.telemetry.position():
            abs_alt = position.absolute_altitude_m
            rel_alt = position.relative_altitude_m
            break
        async for mission_progress in drone.mission.mission_progress():
            mp_current = mission_progress.current
            mp_total = mission_progress.total
            break
        log_txt = (f"mode:{mode},Mission progress:{mp_current}/{mp_total},mp_total,lidar:{lidar}[m],abs_alt:{abs_alt}[m],rel_alt:{rel_alt}[m]")
        logger_info.info(str(log_txt))
        await asyncio.sleep(0.5)

async def img_navigation(drone):
    while True:
        await asyncio.sleep(1)
        mission_finished = await drone.mission.is_mission_finished()
        if mission_finished:
            logger_info.info("mission finished")
            break

    await asyncio.sleep(10)


    camera = picamera.PiCamera()
    logger_info.info('キャメラ初期化完了')

    async for d in drone.telemetry.distance_sensor(): #? 測れなかったらどうしよう
        lidar_height = d.current_distance_m
        logger_info.info(f"current height:{lidar_height}m")
        break
    async for heading in drone.telemetry.heading():
        heading_deg = heading.heading_deg
        logger_info.info(f"current heading: {heading_deg}") 
        break


    file_path = '/home/pi/ARLISS_IBIS/Images/image_navigation_test_ver2_{}.jpg'.format(datetime.datetime.now())

    logger_info.info("taking pic...: {}".format(file_path))
    take_pic(camera,file_path) # 写真を撮る
    res = detect_center(file_path) # 赤の最大領域の占有率と重心を求める

    logger_info.info('percent={}, center={}'.format(res['percent'], res['center']))

    await asyncio.sleep(1)

    distance = lidar_height
    a = pixel_number_x*pixel_size/1000 # 画像(ピクセル単位)の横の長さ[mm]
    b = pixel_number_y*pixel_size/1000 # 画像(ピクセル単位)の縦の長さ[mm]
    image_x = distance*a/f # 画像の横の距離[m]
    image_y = distance*b/f # 画像の縦の距離[m]
    x_m = res['center'][0]*image_x/2
    y_m = res['center'][1]*image_y/2

    east_m = 1/np.sqrt(2)*(y_m-x_m)*np.cos(heading_deg*np.pi/180)-1/np.sqrt(2)*(y_m+x_m)*np.sin(heading_deg*np.pi/180)
    north_m = 1/np.sqrt(2)*(y_m-x_m)*np.sin(heading_deg*np.pi/180)+1/np.sqrt(2)*(y_m+x_m)*np.cos(heading_deg*np.pi/180)

    logger_info.info(f"go to the red position:北に{north_m}m,東に{east_m}")

    logger_info.info("-- Setting initial setpoint")
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0 , 0.0))
    await drone.offboard.start()
    logger_info.info("offboard start")

    await drone.offboard.set_position_ned(
            PositionNedYaw(north_m, east_m, 0.0, 0.0)) #? 方位が違うかも
    await asyncio.sleep(10)

    logger_info.info("-- Stopping offboard")
    try:
        await drone.offboard.stop()
    except OffboardError as error:
        logger_info.info(f"Stopping offboard mode failed \
                with error code: {error._result.result}")
    logger_info.info("画像認識成功、着陸します") 
    await drone.action.land()

def take_pic(camera,file_path):
    camera.capture(file_path)

def save_detected_img(file_path, img, center_px):
    cv2.circle(img, (int(center_px[0]), int(center_px[1])), 30, (0, 200, 0),
            thickness=3, lineType=cv2.LINE_AA)
    cv2.imwrite(file_path, img)

def detect_center(file_path):
    img = cv2.imread(file_path) # 画像を読み込む
    
    height, width = img.shape[:2] # 画像のサイズを取得する

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) # 色基準で2値化する

    # 色の範囲を指定する
    hsv_min = np.array([0,145,0])
    hsv_max = np.array([5,255,255])
    mask1 = cv2.inRange(hsv, hsv_min, hsv_max)

    # 赤色のHSVの値域2
    hsv_min = np.array([0,110,0]) #カメラ故障のため，0→150へ変更
    hsv_max = np.array([179,255,255])
    mask2 = cv2.inRange(hsv, hsv_min, hsv_max)

    mask = mask1 + mask2

    # 非ゼロのピクセルが連続してできた領域を検出する
    nlabels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)

    #　画像の背景の番号は 0 とラベリングされているので、実際のオブジェクトの数は nlabels - 1 となる
    nlabels = nlabels - 1
    labels = np.delete(labels, obj=0, axis=0)
    stats = np.delete(stats, obj=0, axis=0)
    centroids = np.delete(centroids, obj=0, axis=0)
    centroids[:,0] = (width/2 - centroids[:,0]) / width*2
    centroids[:,1] = (height/2 - centroids[:,1]) / height*2
    percent = stats[:,4] / (height*width)
    
    res = {}

    if nlabels == 0:
        res['height'] = None
        res['width'] = None
        res['percent'] = 0
        res['center'] = None
    else:
        max_index = np.argmax(percent)
        res['height'] = height
        res['width'] = width
        res['percent'] = percent[max_index]
        res['center'] = centroids[max_index]
        save_detected_img(file_path, img, ((1-res['center'][0])*width/2, (1-res['center'][1])*height/2))
    
    return res


if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())