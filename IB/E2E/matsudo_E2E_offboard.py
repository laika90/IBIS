import spidev               
import time                         
import sys    
import RPi.GPIO as GPIO
import asyncio
import picamera
import cv2
import numpy as np
import datetime
from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)
from mavsdk.offboard import (OffboardError, PositionNedYaw)
from logger_E2E import logger_info
 
 
light_threshold = 500
is_landed = False
fuse_Pin = 3
fuse_time = 5.0
stored_timelimit = 100
stored_judge_time = 15
released_timelimit = 100
released_judge_time = 10
land_timelimit = 100

# パラメータ--------------------------------
goal = [35.7961963, 139.8918611]
height = 6 # goalの高度
#-----------------------------------------

#　picameraの仕様--------------------------
pixel_number_x = 3296 #[mm]
pixel_number_y = 2521
pixel_size = 1.12 #[um]
f = 3.04 #[mm]
# ----------------------------------------


def get_light_val():
    resp = spi.xfer2([0x68, 0x00])                 
    value = ((resp[0] << 8) + resp[1]) & 0x3FF    
    return value


def stored_judge():
    logger_info.info("######################\n# stored judge start #\n######################")

    # 関数の開始時間
    start_time = time.perf_counter()
    # 光の継続時間
    duration_start_time = time.perf_counter()
    is_continue = False

    while True:


        light_val = get_light_val()
        time_stamp = time.perf_counter() - duration_start_time
        print("{:5.1f}| 光センサ:{:>3d}, 継続:{}".format(time_stamp, light_val, is_continue))

        if is_continue:
            # 光が途切れていた場合、やり直し
            if light_val >= light_threshold:
                is_continue = False
                continue

            # 光の継続時間
            duration_time = time.perf_counter() - duration_start_time

            if duration_time > stored_judge_time:
                logger_info.info("stored judge case 1")
                break
        
        elif light_val < light_threshold:
            is_continue = True
            duration_start_time = time.perf_counter()
        
        elapsed_time = time.perf_counter() - start_time

        if elapsed_time > stored_timelimit:
            logger_info.info("stored judge case 2")
            break

    logger_info.info("#######################\n# stored judge finish #\n#######################")


def released_judge():
    logger_info.info("########################\n# released judge start #\n########################")

    # 関数の開始時間
    start_time = time.perf_counter()
    # 光の継続時間
    duration_start_time = time.perf_counter()
    is_continue = False


    while True:

        light_val = get_light_val()
        time_stamp = time.perf_counter() - duration_start_time
        print("{:5.1f}| 光センサ:{:>3d}, 継続:{}".format(time_stamp, light_val, is_continue))

        if is_continue:
            # 光が途切れていた場合、やり直し
            if light_val <= light_threshold:
                is_continue = False
                continue

            # 光の継続時間
            duration_time = time.perf_counter() - duration_start_time

            if duration_time > released_judge_time:
                logger_info.info("released judge case 1")
                break
        
        elif light_val > light_threshold:
            is_continue = True
            duration_start_time = time.perf_counter()
        
        elapsed_time = time.perf_counter() - start_time

        if elapsed_time > released_timelimit:
            logger_info.info("released judge case 2")
            break

    logger_info.info("#########################\n# released judge finish #\n#########################")


# async def connect_pixhawk():
#     drone = System()
#     logger_info.info("-- Waiting for drone to be connected...")
#     await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    
#     async for state in drone.core.connection_state():
#         if state.is_connected:
#             logger_info.info("-- Connected to drone!")
#             break
    
#     logger_info.info("-- Throw the viecle")
#     time.sleep(5)
    
#     return drone


async def land_judge(drone):
    global is_landed
    logger_info.info("#########################\n# land judge start #\n#########################")
    start_time = time.time()
    while True:
        time_now = time.time()
        if time_now-start_time < 30:
            true_dist = IQR_removal(await alt_list(drone))
            try:
                ave = sum(true_dist)/len(true_dist)
            except ZeroDivisionError as e:
                logger_info.info(e)
                continue
            
            if await is_low_alt(ave):
                for distance in true_dist:
                    if abs(ave-distance) > 0.01:
                        logger_info.info("-- Moving")
                        break
                else:
                    is_landed = True
                    logger_info.info("-- Lidar Judge")
            else:
                logger_info.info("-- Over 1m")
                
        else:
            is_landed = True
            logger_info.info("-- Timer Judge")
            
        if is_landed:
            logger_info.info("-- Landed")
            break
    
    logger_info.info("#########################\n# land judge finish #\n#########################")
        
        
async def is_low_alt(alt):
    return alt < 1
        
        
async def alt_list(drone):
    distance_list = []
    iter = 0
    while True:
        try:
            distance = await asyncio.wait_for(get_distance_alt(drone), timeout = 0.8)
        except asyncio.TimeoutError:
            logger_info.info("Too high or lidar error")
            distance_list = []
            return distance_list
        iter += 1
        logger_info.info("altitude:{}".format(distance))
        distance_list.append(distance)
        await asyncio.sleep(0)
        if iter >= 30:
            break
    return distance_list


def IQR_removal(data):
    try:
        data.sort()
        quartile_25 = data[7]
        quartile_75 = data[23]
        IQR = quartile_75-quartile_25
        true_data = [i for i in data if quartile_25-1.5*IQR <= i <= quartile_75+1.5*IQR]
    except IndexError as e:
        logger_info.info(e)
        true_data= []
    return true_data


async def get_distance_alt(drone):
    async for distance in drone.telemetry.distance_sensor():
        return distance.current_distance_m


def fusing():
    try:
        logger_info.info("-- Fuse start")
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(fuse_Pin, GPIO.OUT)

        GPIO.output(fuse_Pin, 0)
        logger_info.info("-- Fusing")

        time.sleep(fuse_time)
        logger_info.info("-- Fused! Please Fly")

        GPIO.output(fuse_Pin, 1)
    
    except:
        GPIO.output(fuse_Pin, 1)


async def run():

    drone = System()
    logger_info.info("-- Waiting for drone to be connected...")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    
    async for state in drone.core.connection_state():
        if state.is_connected:
            logger_info.info("-- Connected to drone!")
            break
    
    logger_info.info("-- Throw the viecle")
    time.sleep(5)
    stored_judge()
    released_judge()
    await land_judge(drone)
    fusing()


    await asyncio.sleep(1)
    logger_info.info("waiting 1s")

    # drone = System()
    # await drone.connect(system_address="serial:///dev/ttyACM0:115200")

    logger_info.info("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            break
        
    get_log_task = asyncio.ensure_future(get_log(drone))
    # img_navigation_task = asyncio.ensure_future(img_navigation(drone))

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

    # logger_info.info("waiting for pixhawk to hold")
    # flag = False #MAVSDKではTrueって出るけどFalseが出ない場合もあるから最初からFalseにしてる
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            # logger_info.info("-- Global position estimate OK")
            break
    # while True:
    #    if flag==True:
    #        break
    #    async for flight_mode in drone.telemetry.flight_mode():
    #        if str(flight_mode) == "HOLD":
    #            logger_info.info("hold確認")
    #            flag=True
    #            break
    #        else:
    #            try:
    #                await drone.action.hold() #holdじゃない状態からholdしようてしても無理だからもう一回exceptで繋ぎなおす
    #            except Exception as e:
    #                logger_info.info(e)
    #                drone = System()
    #                await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    #                logger_info.info("Waiting for drone to connect...")
    #                async for state in drone.core.connection_state():

    #                     if state.is_connected:
                            
    #                         logger_info.info(f"-- Connected to drone!")
    #                         break
    #                mission_items = []
    #                mission_items.append(MissionItem(goal[0],
    #                                  goal[1],
    #                                  height, # rel_alt
    #                                  5, # speed
    #                                  True, #止まらない
    #                                  float('nan'),
    #                                  float('nan'), #gimbal_yaw_deg
    #                                  MissionItem.CameraAction.NONE,
    #                                  float('nan'),
    #                                  float('nan'),
    #                                  float('nan'),
    #                                  float('nan'),
    #                                  float('nan')))

    #                mission_plan = MissionPlan(mission_items)

    #                await drone.mission.set_return_to_launch_after_mission(False)

    #                logger_info.info("-- Uploading mission")
    #                await drone.mission.upload_mission(mission_plan)
    #                #await asyncio.sleep(0.5)(KF)
    #                break 

    logger_info.info("-- Arming")
    await drone.action.arm()

    await asyncio.sleep(100)

    logger_info.info("-- Starting mission")
    await drone.mission.start_mission()

    await get_log_task
    # await img_navigation_task
    while True:
        await asyncio.sleep(1)
        mission_finished = await drone.mission.is_mission_finished()
        if mission_finished:
            break
        
    await drone.action.land()
  
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
        log_txt = (" mode:",mode," Mission progress:",mp_current,"/",mp_total," lidar: ",lidar,"m"," abs_alt:",abs_alt,"m"," rel_alt:",rel_alt,"m")
        logger_info.info(str(log_txt))
        await asyncio.sleep(0.5)

# async def img_navigation(drone):
#     while True:
#         await asyncio.sleep(1)
#         mission_finished = await drone.mission.is_mission_finished()
#         if mission_finished:
#             logger_info.info("mission finished")
#             break

#     await asyncio.sleep(10)


#     camera = picamera.PiCamera()
#     logger_info.info('キャメラ初期化完了')

#     async for d in drone.telemetry.distance_sensor(): #? 測れなかったらどうしよう
#         lidar_height = d.current_distance_m
#         logger_info.info(f"current height:{lidar_height}m")
#         break
#     async for heading in drone.telemetry.heading():
#         heading_deg = heading.heading_deg
#         logger_info.info(f"current heading: {heading_deg}") 
#         break


#     file_path = '/home/pi/ARLISS_IBIS/Images/image_navigation_test_ver2_{}.jpg'.format(datetime.datetime.now())

#     logger_info.info("taking pic...: {}".format(file_path))
#     take_pic(camera,file_path) # 写真を撮る
#     res = detect_center(file_path) # 赤の最大領域の占有率と重心を求める

#     logger_info.info('percent={}, center={}'.format(res['percent'], res['center']))

#     await asyncio.sleep(1)

#     distance = lidar_height
#     a = pixel_number_x*pixel_size/1000 # 画像(ピクセル単位)の横の長さ[mm]
#     b = pixel_number_y*pixel_size/1000 # 画像(ピクセル単位)の縦の長さ[mm]
#     image_x = distance*a/f # 画像の横の距離[m]
#     image_y = distance*b/f # 画像の縦の距離[m]
#     x_m = res['center'][0]*image_x/2
#     y_m = res['center'][1]*image_y/2

#     east_m = 1/np.sqrt(2)*(y_m-x_m)*np.cos(heading*np.pi/180)-1/np.sqrt(2)*(y_m+x_m)*np.sin(heading*np.pi/180)
#     north_m = 1/np.sqrt(2)*(y_m-x_m)*np.sin(heading*np.pi/180)+1/np.sqrt(2)*(y_m+x_m)*np.cos(heading*np.pi/180)

#     logger_info.info(f"go to the red position:北に{north_m}m,東に{east_m}")

#     logger_info.info("-- Setting initial setpoint")
#     await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0 , 0.0))
#     await drone.offboard.start()

#     await drone.offboard.set_position_ned(
#             PositionNedYaw(north_m, east_m, 0.0, 0.0)) #? 方位が違うかも
#     await asyncio.sleep(10)

#     logger_info.info("-- Stopping offboard")
#     try:
#         await drone.offboard.stop()
#     except OffboardError as error:
#         logger_info.info(f"Stopping offboard mode failed \
#                 with error code: {error._result.result}")
#     logger_info.info("画像認識成功、着陸します") 
#     await drone.action.land()

# def take_pic(camera,file_path):
#     camera.capture(file_path)

# def save_detected_img(file_path, img, center_px):
#     cv2.circle(img, (int(center_px[0]), int(center_px[1])), 30, (0, 200, 0),
#             thickness=3, lineType=cv2.LINE_AA)
#     cv2.imwrite(file_path, img)

# def detect_center(file_path):
#     img = cv2.imread(file_path) # 画像を読み込む
    
#     height, width = img.shape[:2] # 画像のサイズを取得する

#     hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) # 色基準で2値化する

#     # 色の範囲を指定する
#     hsv_min = np.array([0,145,0])
#     hsv_max = np.array([5,255,255])
#     mask1 = cv2.inRange(hsv, hsv_min, hsv_max)

#     # 赤色のHSVの値域2
#     hsv_min = np.array([0,110,0]) #カメラ故障のため，0→150へ変更
#     hsv_max = np.array([179,255,255])
#     mask2 = cv2.inRange(hsv, hsv_min, hsv_max)

#     mask = mask1 + mask2

#     # 非ゼロのピクセルが連続してできた領域を検出する
#     nlabels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)

#     #　画像の背景の番号は 0 とラベリングされているので、実際のオブジェクトの数は nlabels - 1 となる
#     nlabels = nlabels - 1
#     labels = np.delete(labels, obj=0, axis=0)
#     stats = np.delete(stats, obj=0, axis=0)
#     centroids = np.delete(centroids, obj=0, axis=0)
#     centroids[:,0] = (width/2 - centroids[:,0]) / width*2
#     centroids[:,1] = (height/2 - centroids[:,1]) / height*2
#     percent = stats[:,4] / (height*width)
    
#     res = {}

#     if nlabels == 0:
#         res['height'] = None
#         res['width'] = None
#         res['percent'] = 0
#         res['center'] = None
#     else:
#         max_index = np.argmax(percent)
#         res['height'] = height
#         res['width'] = width
#         res['percent'] = percent[max_index]
#         res['center'] = centroids[max_index]
#         save_detected_img(file_path, img, ((1-res['center'][0])*width/2, (1-res['center'][1])*height/2))
    
#     return res
    
    
if __name__ == "__main__":
    # SPI
    spi = spidev.SpiDev()     
    spi.open(0, 0)                    
    spi.max_speed_hz = 1000000 
    
    asyncio.run(run())
    
    spi.close()
    sys.exit()