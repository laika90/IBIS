import spidev               
import time                         
import sys    
import RPi.GPIO as GPIO
import asyncio
import picamera
from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)
from logger_performace import logger_info
import serial
import cv2
import numpy as np
import datetime
from mavsdk.offboard import (OffboardError, PositionNedYaw)


#　GPI0 PIN settings--------------------------
fuse_Pin = 3
lora_power_pin = 4
# ----------------------------------------

#　Time settings--------------------------
wait_time = 60
lora_sleep_time = 3
fuse_time = 7.0
stored_timelimit = 60
stored_judge_time = 15
released_timelimit = 3 * 60
released_judge_time = 5
land_timelimit = 20
# ----------------------------------------

#　flags--------------------------
is_landed = False 
is_lora_power_on = False
# ----------------------------------------

# parameters--------------------------------
light_threshold = 400
goal = [40.1425536, 139.9872313]
height = 7 # goalの高度
fling_speed = 5
#-----------------------------------------

#　picamera settings--------------------------
pixel_number_x = 3296 #[mm]
pixel_number_y = 2521
pixel_size = 1.12 #[um]
f = 3.04 #[mm]
# ----------------------------------------

#　deamon file--------------------------
deamon_file = open("/home/pi/ARLISS_IBIS/IB/log/Performance_log.txt")
deamon_log = deamon_file.read()
# ----------------------------------------
        
        
# def set_gpio():
    
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setwarnings(False)
    # GPIO.setup(fuse_Pin, GPIO.OUT)
    # GPIO.setup(lora_power_pin, GPIO.OUT)
    # GPIO.output(lora_power_pin, 1)
    
    
async def serial_connect():
    
    connect_counter = 0
    while True:
        try:
            lora = serial.Serial('/dev/ttyS0', 115200, timeout=1)
        except:
            logger_info.info ("Serial port error. Waiting.")
            connect_counter += 1
            if connect_counter >= 100:
                break
            await asyncio.sleep(3)
        else:
            break
    logger_info.info("Serial port OK.")
    operation_write(lora)
    await write(lora, ("Lora start").encode())
    logger_info.info("Lora READY")
    return lora


async def write(lora, message: str):
    
    msg_send = str(message) + "\r\n"
    lora.write(msg_send.encode("ascii"))
    time.sleep(lora_sleep_time)
    
    
def operation_write(lora):
    
    lora.write(b'2\r\n')
    time.sleep(1)
    lora.write(b'z\r\n')
    time.sleep(1)
    
    
async def send_gps(lora, drone):
    
    lat_deg, lng_deg, alt_deg = await get_gps(drone)
    if is_lora_power_on:
        lat = "lat:" + str(lat_deg)
        lng = "lng:" + str(lng_deg)
        alt = "alt:" + str(alt_deg)
        await write(lora, lat.encode())
        logger_info.info(lat)
        await write(lora, lng.encode())
        logger_info.info(lng)
        await write(lora, alt.encode())
        logger_info.info(alt)
    
    
async def get_gps(drone):
    
    lat, lng, alt = "0", "0", "0"
    while True:
        try:
            await asyncio.wait_for(gps(drone), timeout=0.8)
        except asyncio.TimeoutError:
            logger_info.info("Can't catch GPS")
            lat = "error"
            lng = "error"
            alt = "error"
        return lat, lng, alt
        
        
async def gps(drone):
    
    global lat, lng, alt
    async for position in drone.telemetry.position():
            logger_info.info(position)
            lat = str(position.latitude)
            lng = str(position.longitude)
            alt = str(position.absolute_altitude_m)
            break


async def wait_store(lora):
    
    if "Three minutes passed" in deamon_log:
        await write(lora, "skipped store wait")
        logger_info.info("skipped store wait")
        return
    
    else:
        logger_info.info("Waiting for store")
        time.sleep(wait_time)
        logger_info.info("Three minutes passed")
    

def get_light_val():
    
    resp = spi.xfer2([0x68, 0x00])                 
    value = ((resp[0] << 8) + resp[1]) & 0x3FF    
    return value


async def stored_judge(lora):
    
    if "stored judge finish" in deamon_log:
        await write(lora, "skipped stored judge")
        logger_info.info("skipped stored judge")
        return
    
    else:
        await write(lora, "stored judge start")
        logger_info.info("######################\n# stored judge start #\n######################")

        # 関数の開始時間
        start_time = time.perf_counter()
        # 光の継続時間
        duration_start_time = time.perf_counter()
        is_continue = False

        while True:


            light_val = get_light_val()
            time_stamp = time.perf_counter() - duration_start_time
            logger_info.info("{:5.1f}| 光センサ:{:>3d}, 継続:{}".format(time_stamp, light_val, is_continue))

            if is_continue:
                # 光が途切れていた場合、やり直し
                if light_val >= light_threshold:
                    is_continue = False
                    continue

                # 光の継続時間
                duration_time = time.perf_counter() - duration_start_time

                if duration_time > stored_judge_time:
                    logger_info.info("-- Light Judge")
                    break
            
            elif light_val < light_threshold:
                is_continue = True
                duration_start_time = time.perf_counter()
            
            elapsed_time = time.perf_counter() - start_time

            if elapsed_time > stored_timelimit:
                logger_info.info("-- Timer Judge")
                break

        await write(lora, "stored judge finish")
        logger_info.info("#######################\n# stored judge finish #\n#######################")


async def released_judge(lora):
    
    if "released judge finish" in deamon_log:
        await write(lora, "skipped released judge")
        logger_info.info("skipped released judge")
        return
    
    else:
        await write(lora, "released judge start")
        logger_info.info("########################\n# released judge start #\n########################")

        # 関数の開始時間
        start_time = time.perf_counter()
        # 光の継続時間
        duration_start_time = time.perf_counter()
        is_continue = False


        while True:

            light_val = get_light_val()
            time_stamp = time.perf_counter() - duration_start_time
            logger_info.info("{:5.1f}| 光センサ:{:>3d}, 継続:{}".format(time_stamp, light_val, is_continue))

            if is_continue:
                # 光が途切れていた場合、やり直し
                if light_val <= light_threshold:
                    is_continue = False
                    continue

                # 光の継続時間
                duration_time = time.perf_counter() - duration_start_time

                if duration_time > released_judge_time:
                    logger_info.info("-- Light Judge")
                    break
            
            elif light_val > light_threshold:
                is_continue = True
                duration_start_time = time.perf_counter()
            
            elapsed_time = time.perf_counter() - start_time

            if elapsed_time > released_timelimit:
                logger_info.info("-- Timer Judge")
                break

        await write(lora, "released judge finish")
        logger_info.info("#########################\n# released judge finish #\n#########################")


async def land_judge(lora, drone):
    
    if "land judge finish" in deamon_log:
        await write(lora, "skipped land judge")
        logger_info.info("skipped land judge")
        return
    
    else:
        write(lora, "land judge start")
        global is_landed
        logger_info.info("#########################\n# land judge start #\n#########################")
        start_time = time.time()
        while True:
            time_now = time.time()
            if time_now-start_time < land_timelimit:
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
        
        await write(lora, "land judge finish")
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


async def fusing():
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(fuse_Pin, GPIO.OUT, initial=GPIO.HIGH)
        logger_info.info("-- Fuse start")

        GPIO.output(fuse_Pin, 0)
        logger_info.info("-- Fusing")

        await asyncio.sleep(fuse_time)
        logger_info.info("-- Fused! Please Fly")

        GPIO.output(fuse_Pin, 1)
    
    except:
        GPIO.output(fuse_Pin, 1)


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
        await asyncio.sleep(0)


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

    file_path = '/home/pi/ARLISS_IBIS/Images/NSE_{}.jpg'.format(datetime.datetime.now())

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
    await asyncio.sleep(10)
    logger_info.info("-- Landed")


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


async def run():

    drone = System()
    logger_info.info("-- Waiting for drone to be connected...")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    
    async for state in drone.core.connection_state():
        if state.is_connected:
            logger_info.info("-- Connected to drone!")
            break
    
    # set_gpio()
    
    lora = await serial_connect()
    
    await wait_store(lora)
    await stored_judge(lora)
    await released_judge(lora)
    await land_judge(lora, drone)
    
    fuse_task = asyncio.ensure_future(fusing())
    # lora_task = asyncio.ensure_future(send_gps(lora, drone))
    await fuse_task
    # await lora_task

    logger_info.info("Checking drone to be connected...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            break
        
    get_log_task = asyncio.ensure_future(get_log(drone))
    img_navigation_task = asyncio.ensure_future(img_navigation(drone))

    mission_items = []
    mission_items.append(MissionItem(goal[0],
                                     goal[1],
                                     height, # rel_alt
                                     fling_speed, # speed
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

    logger_info.info("waiting for pixhawk to hold")
    # flag = False #MAVSDKではTrueって出るけどFalseが出ない場合もあるから最初からFalseにしてる
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            logger_info.info("-- Global position estimate OK")
            # logger_info.info("-- Global position estimate OK")
            break
        
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            logger_info.info("-- Global position estimate OK")
            # logger_info.info("-- Global position estimate OK")
            break
        
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            logger_info.info("-- Global position estimate OK")
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

    logger_info.info("-- Starting mission")
    await drone.mission.start_mission()

    await get_log_task
    await img_navigation_task
    # while True:
    #     await asyncio.sleep(1)
    #     mission_finished = await drone.mission.is_mission_finished()
    #     if mission_finished:
    #         logger_info.info("Mission complete!")
    #         break
    
    # logger_info.info("-- Landing")
    # await drone.action.land()
    # await asyncio.sleep(10)
    # logger_info.info("-- Landed")
  
    
    
if __name__ == "__main__":
    
    spi = spidev.SpiDev()     
    spi.open(0, 0)                    
    spi.max_speed_hz = 1000000 
    
    asyncio.run(run())
    
    spi.close()
    sys.exit()