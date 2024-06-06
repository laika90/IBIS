import asyncio
import mavsdk
import json
import numpy as np
from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)
from mavsdk.offboard import (OffboardError, PositionNedYaw)
from logger_lib import logger_info
from camera import Camera
import time
import RPi.GPIO as GPIO


class Pixhawk:
    
    def __init__(self,
                 fuse_pin,
                 wait_time,
                 fuse_time,
                 land_timelimit,
                 land_judge_len,
                 health_continuous_count,
                 waypoint_lat,
                 waypoint_lng,
                 waypoint_alt,
                 mission_speed,
                 image_navigation_timeout,
                 lora,
                 light,
                 deamon_pass = "/home/pi/ARLISS_IBIS/IB/log/Performance_log.txt",
                 use_camera = False,
                 use_gps_config = False,
                 use_other_param_config = False):
        
        self.pix = System()
        self.available_camera = True
        #カメラを使おうとする、できなかったらログにエラー内容を出力
        if use_camera:
            try:
                self.camera = Camera()
            except Exception as e:
                logger_info.info(e) #レベルINFOでエラー内容をログに出力
                self.available_camera = False
            
        self.lora = lora
        self.light = light
        
        #use_gps_configがTrueになっているならconfig内のjsonファイルからデータを取得。それ以外の場合はある値に設定。
        if use_gps_config:
            json_pass_gps = "/home/pi/ARLISS_IBIS/IB/config/matsudo_config/GPS_matsudo_config.json"
            f = open(json_pass_gps , "r")
            waypoint = json.load(f)
            self.waypoint_lat = float(waypoint["waypoint_lat"])
            self.waypoint_lng = float(waypoint["waypoint_lng"])
            f.close()
        else:
            self.waypoint_lat = waypoint_lat
            self.waypoint_lng = waypoint_lng
            
    #上と同じ。jsonファイルだけ違う
        if use_other_param_config:
            json_pass_other_param = "/home/pi/ARLISS_IBIS/IB/config/matsudo_config/other_param_matsudo_config.json"
            f = open(json_pass_other_param , "r")
            other_param = json.load(f)
            self.fuse_pin = float(other_param["fuse_pin"])
            self.wait_time = float(other_param["wait_time"])
            self.fuse_time = float(other_param["fuse_time"])
            self.land_timelimit = float(other_param["land_timelimit"])
            self.land_judge_len = float(other_param["land_judge_len"])
            self.health_continuous_count = float(other_param["health_continuous_count"])
            self.mission_speed = float(other_param["mission_speed"])
            self.waypoint_alt = float(other_param["waypoint_alt"])
            f.close()
        else:
            self.fuse_pin = fuse_pin
            self.wait_time = wait_time
            self.fuse_time = fuse_time
            self.land_timelimit = land_timelimit
            self.land_judge_len = land_judge_len
            self.health_continuous_count = health_continuous_count
            self.mission_speed = mission_speed
            self.waypoint_alt = waypoint_alt
            self.image_navigation_timeout = image_navigation_timeout
        

#各値の初期設定
        self.flight_mode = None
        self.mp_current = None #現在実行中のミッションアイテムのインデックス
        self.mp_total = None #ミッションアイテムの総数
        self.max_speed = None 
        self.latitude_deg = None
        self.longitude_deg = None
        self.voltage_v = None
        self.remaining_percent = None
        self.lidar = None
        self.image_res = None
        self.east_m = None
        self.north_m = None
        self.is_in_air =  None
        self.pitch_deg = None
        self.roll_deg = None
        
        self.deamon_pass = deamon_pass
        self.deamon_file = open(self.deamon_pass)
        self.deamon_log = self.deamon_file.read()
        
        self.is_waited = False
        self.is_tasks_cancel_ok = False
        self.is_landed = False 
        self.is_judge_alt = False
        
        logger_info.info("Pixhawk initialized") #レベルINFOでログに出力
        

#テレメトリー経由で現在のフライトモードをstringで取得、値に代入
    async def get_flight_mode(self):

        async for flight_mode in self.pix.telemetry.flight_mode():
            self.flight_mode = flight_mode
            

#現在実行中のミッションプロセス、およびその総数を取得、値に代入           
    async def get_mission_progress(self):
        
        async for mission_progress in self.pix.mission.mission_progress():
            self.mp_current = mission_progress.current
            self.mp_total = mission_progress.total
            

#機体をmaximum_speedにする関数の中からmaximum_speedのfloatのみを取得。
#get_maximum_speed_async()ならnon-blockingだから実際にmaximum_speedにするときはこっちの方が良さそう
    async def get_max_speed(self):

        async for speed in self.pix.action.get_maxium_speed():
            self.max_speed = speed
            

#現在の地面との距離の読み取り値を取得、不明な場合はNan.
    async def get_distance_alt(self):

        async for distance in self.pix.telemetry.distance_sensor():
            return distance.current_distance_m
        
    
#現在の地面との距離の読み取り値を取得、不明な場合はNan.lidarの値として代入  
    async def get_lidar(self):
        
        async for distance in self.pix.telemetry.distance_sensor():
            self.lidar = distance.current_distance_m


#ホームポジションとの相対的な高度を得る        
    async def get_position_alt(self):

        async for position in self.pix.telemetry.position():
            return position.absolute_altitude_m
        
        
#緯度経度の取得 
    async def get_position_lat_lng(self):

        async for position in self.pix.telemetry.position():
            self.latitude_deg = position.latitude_deg
            self.longitude_deg = position.longitude_deg


#バッテリーの電圧、推定バッテリー残量を取得
    async def get_battery(self):

        async for battery in self.pix.telemetry.battery():
            self.voltage_v = battery.voltage_v
            self.remaining_percent = battery.remaining_percent


#空中にいるかどうかのboolを取得    
    async def get_in_air(self):

        async for is_in_air in self.pix.telemetry.in_air():
            self.is_in_air = is_in_air


#ピッチ角、ロール角を取得
    async def get_pitch_roll(self):
        
        async for angle in self.drone.telemetry.attitude_euler(): #droneではなくpixでは？-----------------------------
            self.pitch_deg = angle.pitch_deg
            self.roll_deg = angle.roll_deg


#上のget_in_airと同じだが、returnで返してる
    async def return_in_air(self):

        async for is_in_air in self.pix.telemetry.in_air():
            return is_in_air
        

#上のget_pitch_rolと同じだが、returnで返してる
    async def return_pitch_roll(self):
        
        async for angle in self.pix.telemetry.attitude_euler():
            return angle.pitch_deg, angle.roll_deg



#flightmodeを取得し続けるcycle.
    async def cycle_flight_mode(self):

        try:
            while True:
                await self.get_flight_mode()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        

#mission_progressを取得し続けるcycle.    
    async def cycle_mission_progress(self):

        try:
            while True:
                await self.get_mission_progress()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass


#緯度経度を取得し続けるcycle.
    async def cycle_position_lat_lng(self):

        try:
            while True:
                await self.get_position_lat_lng()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        

#loraで緯度経度を送り続けるcycle.    
    async def cycle_lora(self):
        
        try:
            while True:
                await self.lora.write("lat:"+str(self.latitude_deg))
                await asyncio.sleep(1)
                await self.lora.write("lng:"+str(self.longitude_deg))
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
    

#バッテリーのボルト、残量を取得し続けるcycle.
    async def cycle_battery(self):

        try:
            while True:
                await self.get_battery()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass


#lidarの値を取得し続けるcycle.    
    async def cycle_lidar(self):

        try:
            while True:
                await self.get_lidar()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass


#pitch,rollを取得し続けるcycle.
    async def cycle_pitch_roll(self):

        try:
            while True:
                await self.get_pitch_roll()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass


#空中にいるかどうかのboolを取得し続けるcycle.
    async def cycle_is_in_air(self):

        try:
            while True:
                await self.get_in_air()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass


#logに自らの状態を反映するcycle.一秒おき.出力結果はlogを参照
    async def cycle_show(self):

        try:
            while True:
                log_txt = (
                    " mode:"
                    + str(self.flight_mode)
                    + " mission progress:"
                    + str(self.mp_current)
                    + "/"
                    + str(self.mp_total)
                    + " lat:"
                    + str(self.latitude_deg)
                    + " lng:"
                    + str(self.longitude_deg)
                    + " lidar:"
                    + str(self.lidar)
                    + "m"
                )
                logger_info.info(str(log_txt))
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass
            

#コンピューターとドローンを接続、logに出力 
    async def connect(self):

        logger_info.info("Waiting for drone to connect...")
        await self.pix.connect(system_address="serial:///dev/ttyACM0:115200")
        async for state in self.pix.core.connection_state():
            if state.is_connected:
                logger_info.info("Drone connected!")
                break
            

#自律制御前のホバリングモード(hold)に移行.成功・失敗はログに出力.できるまで繰り返す
    async def hold(self):

        logger_info.info("Waiting for drone to hold...")
        while True:
            try:
                await self.pix.action.hold()
            except mavsdk.action.ActionError:
                logger_info.info("Hold denied")
                await asyncio.sleep(0.1)
            else:
                logger_info.info("Hold mode!")
                break 


#自律制御に入る準備段階、armモードに移行.成功・失敗はログに出力.できるまで    
    async def arm(self):
        
        logger_info.info("Arming")
        while True:
            try:
                await self.pix.action.arm()
            except mavsdk.action.ActionError:
                logger_info.info("Arming denied")
                await asyncio.sleep(0.1)
            else:
                logger_info.info("Armed!")
                break    


#takeoffモードに移行.離陸モード  
    async def takeoff(self):
        
        logger_info.info("Taking off")
        await self.pix.set_takeoff_altitude(self.altitude)
        await self.pix.takeoff()
        logger_info.info("Took off!")
        

#landモードに移行.空中にいるかどうかを判定し続け、空中じゃないと判定したら着地        
    async def land(self):
        
        logger_info.info("Landing")
        await self.pix.action.land()
        while True:
            await asyncio.sleep(1)
            is_in_air = await self.return_in_air()
            logger_info.info(f"is_in_air:{is_in_air}")
            if not is_in_air:
                break
        logger_info.info("Landed!")
            

#タイマーをスタートして一定時間が経つとwait_phaseを終了。wait_timeのログ出力が毎回0になってるから上手くいってるか怪しいかも--------------------------------------
#if分の中はlog/Skipp_logを用いて判定をスキップするとき用のもの。
#pre_timeの存在意義がわからない------------------------------------------
    async def wait_store(self):
        
        if "{} seconds passed".format(self.wait_time) in self.deamon_log:
            logger_info.info("skipped store wait")
            await self.lora.write("02")
            return
        
        else:
            pre_time = 0
            start_time = time.time()
            logger_info.info("Waiting for store")
            await self.lora.write("00")
            while True:
                await asyncio.sleep(0.5)
                time_now = time.time()
                time_passed = int((time_now-start_time)//1)
                if time_now > pre_time+1.0:
                    pre_time = time_now
                if time_passed > self.wait_time:
                    self.is_waited = True
                    break
            logger_info.info("{} seconds passed. Wait phase finished".format(self.wait_time))
            await self.lora.write("01")
    

#store_wait中に0.5秒間隔でlight_valをログに残し続ける
#pre_time_stampの存在意義がわからない------------------------------------------
    async def print_light_val(self):

        duration_start_time = time.perf_counter() # CPU実行時間のみを測定する(sleep timeを除く)
        pre_time_stamp = 0
        while True:
            await asyncio.sleep(0.5)
            if self.is_waited:
                break
            light_val = self.light.get_light_val()
            time_stamp = time.perf_counter() - duration_start_time
            if abs(pre_time_stamp - time_stamp) > 0.5:
                pre_time_stamp = time_stamp
                logger_info.info("{:5.1f}| Light Value:{:>3d}".format(time_stamp, light_val))
            
 
#store_wait中に"Lidar:"と出力。（生存確認の意味合いがあるのかな？）
#処理が0.8秒以上かかる場合はエラーメッセージを代わりに出力
# Lidarの値を返すようにもできそう------------------------------------
    
    async def print_lidar(self):
        
        while True:
            await asyncio.sleep(0.5)
            if self.is_waited:
                break
            try :
                distance = await asyncio.wait_for(self.get_distance_alt(), timeout = 0.8)
                logger_info.info("Lidar:".format(distance))
            except asyncio.TimeoutError:
                logger_info.info("Too high or distance sensor might have some error")
            

#上三つの関数をまとめて実行する関数
    async def print_and_wait(self):
        
        wait_coroutines = [
            self.wait_store(),
            self.print_light_val(),
            self.print_lidar()
        ]
        wait_task = asyncio.gather(*wait_coroutines)
        await wait_task
            

#着地判定
#if分の中はlog/Skipp_logを用いて判定をスキップするとき用のもの。        
    async def land_judge(self):
        
        if "Land judge finish" in self.deamon_log:
            logger_info.info("Skipped land judge")
            await self.lora.write("32")
            return
        
        else:
            logger_info.info("-------------------- Land judge start --------------------")
            await self.lora.write("30")
            start_time = time.time()
            while True:
                
                if self.is_landed:
                    break
                
                try :
                    alt_now = await(asyncio.wait_for(self.get_distance_alt(), timeout = 0.8))       #自分の地面からの高度を計測
                    self.change_judge_alt(alt_now)                                                  #自分の高さが判定するに値する高さ、(15m以下であるかを確認)
                except asyncio.TimeoutError:
                    logger_info.info("Too high or distance sensor might have some error")
                await asyncio.sleep(1)
                time_now = time.time()
                time_passed = int((time_now-start_time)//1)
                logger_info.info("Time passed:{}".format(time_passed))       #{}内の数字が1の時しかないから少し上手くいってないor毎回1秒以内に着地してるかも→2桁のfloatとかで出力した方がいい？------------------------------

                if time_passed < self.land_timelimit:           #経過時間がtime_limit以下ならば
                    
                    if self.is_judge_alt:
                        
                        while True:
                            time_now = time.time()
                            time_passed = int((time_now-start_time)//1)
                            logger_info.info("Time passed:{}".format(time_passed))
                            if time_passed < self.land_timelimit:    #ここでもう一回判定しているのはなぜ？------------------------------
                                
                                true_dist = self.IQR_removal(await self.get_alt_list("LIDAR"))  #四分位範囲外のものを排除したリスト
                                if len(true_dist) == 0:
                                    true_posi = self.IQR_removal(await self.get_alt_list("POSITION"))  #LIDARが取れていないならGPSでとってみる
                                    if len(true_posi) == 0:
                                        continue
                                    try:
                                        ave = sum(true_posi)/len(true_posi)  #listの平均値.ave-positionにするべきかも-------------------------------
                                    except ZeroDivisionError as e:
                                        logger_info.info(e)
                                        continue
                                    for position in true_posi:
                                        if abs(ave-position) > 0.03:  #ave-positionは定義されていないため上の変数名を変えるかこっちを変えるべき-------------------------------
                                            logger_info.info("-- Moving")
                                            break
                                    else:                           #elseのインデントずれてない？--------------------------------
                                        self.is_landed = True
                                        
                                    if self.is_landed:
                                        logger_info.info("-- Position Judge")     #どっちの判断で着地したと判定したかを出力
                                        await self.lora.write("311")
                                        break
                                else:
                                    try:
                                        ave = sum(true_dist)/len(true_dist)     #ave-distanceにするべきかも--------------------
                                    except ZeroDivisionError as e:
                                        logger_info.info(e)
                                        continue
                                    if ave < 1:
                                        for distance in true_dist:
                                            if abs(ave-distance) > 0.03:       #上の変数名変えるべき-----------------------------
                                                logger_info.info("-- Moving")
                                                break
                                        else:                    #インデントずれ?----------------------------
                                            self.is_landed = True
                                        
                                    if self.is_landed:
                                        logger_info.info("-- Lidar Judge")       #どっちの判断で着地したと判定したかを出力
                                        await self.lora.write("310")
                                        break
                                    
                            else:
                                self.is_landed = True
                                if self.is_landed:
                                    logger_info.info("-- Timer Judge")       #一定時間経過で着地したとみなす
                                    await self.lora.write("312")
                                    break
                    else:
                        logger_info.info("-- Over 15m")
                else:
                    self.is_landed = True
                    if self.is_landed:
                        logger_info.info("-- Timer Judge")             #一定時間経過で着地したとみなす
                        break
                        
            logger_info.info("-------------------- Land judge finish --------------------")
    

#landjudgeとsendgpsをまとめて実行    
    async def landjudge_and_sendgps(self):
        
        coroutines = [
            self.land_judge(),
            self.send_gps()
        ]
        self.judge_tasks = asyncio.gather(*coroutines)
        await self.judge_tasks
        

#gpsにより緯度経度および高度をログに記録、Loraで送信.もう少しまとめられそう--------------------------------
    async def send_gps(self):
        
        while True:
            
            if self.is_landed:    #着地していたら処理を行わない
                break
            if self.is_judge_alt:    #高度判定中なら処理を行わない
                break
            else:
                lat_deg, lng_deg, alt = await self.get_gps()
                self.lat = "lat:" + str(lat_deg)
                self.lng = "lng:" + str(lng_deg)
                self.alt = "alt:" + str(alt)
                await self.lora.write(self.lat)   #間に1秒開けながらその都度高度判定が始まっていないかを判定しながらlat,lng,altの順で送信
                logger_info.info(self.lat)
                await asyncio.sleep(1)
                if self.is_judge_alt:
                    break
                await self.lora.write(self.lng)
                logger_info.info(self.lng)
                await asyncio.sleep(1)
                if self.is_judge_alt:
                    break
                await self.lora.write(self.alt)
                logger_info.info(self.alt)
                await asyncio.sleep(1)
            
            
#ログ出力のためにGPSの値をstringとして取得する.エラーの場合はログに出力         
    async def get_gps(self):
    
        lat, lng, alt = "0", "0", "0"
        try:
            lat, lng, alt = await asyncio.wait_for(self.update_gps(), timeout=1.0)
        except asyncio.TimeoutError: #
            logger_info.info("Can't catch GPS")
            lat = "error"
            lng = "error"
            alt = "error"
        return lat, lng, alt
            

#GPSの値を更新する関数。型はstring      
    async def update_gps(self):
        
        async for position in self.pix.telemetry.position():
                logger_info.info(position)
                lat = str(position.latitude_deg)
                lng = str(position.longitude_deg)
                alt = str(position.relative_altitude_m)
                return lat, lng, alt


#is_judge_altをaltの値に応じてFalseからTrueに変更.ここでのaltはstringではない
    def change_judge_alt(self, alt):
        
        if ~self.is_judge_alt:  #~で条件を反転させるから、is_judge_alt=Falseの時にboolを変える
            if alt < 15:
                self.is_judge_alt = True
                logger_info.info("-- Under 15m")
            else:
                self.is_judge_alt = False
        else:
            pass
            
 
#altitudeのlistを取得。priorityの入力に応じてGPS,Lidarで高さを取得           
    async def get_alt_list(self, priority):
        
        altitude_list = []
        pre_time = 0
        for _ in range(self.land_judge_len): #エラーでてる---------------------------------------
            if priority == "LIDAR":  #地面からの高さが知りたい場合
                try :
                    distance = await asyncio.wait_for(self.get_distance_alt(), timeout = 0.8)
                except asyncio.TimeoutError:
                    logger_info.info("Too high or distance sensor might have some error")
                    altitude_list =[]
                    return altitude_list
                if distance > 15:
                    logger_info.info("Too high or distance sensor might have some error")
                    altitude_list =[]
                    return altitude_list
                print_time = time.time()
                if print_time > pre_time+0.3:
                    logger_info.info("altitude of LIDAR:{}".format(distance))
                    pre_time = print_time
                altitude_list.append(distance)
                
            elif priority == "POSITION":   #ホームポジションからの高度が知りたい場合
                
                try:
                    position = await asyncio.wait_for(self.get_position_alt(), timeout = 0.8)
                except asyncio.TimeoutError:
                    logger_info.info("GPS can't catch or pixhawk might have some error")
                    altitude_list =[]
                    return altitude_list
                print_time = time.time()
                if print_time > pre_time+0.3:
                    logger_info.info("altitude of POSITION:{}".format(position))
                    pre_time = print_time
                altitude_list.append(position)
            
            else:  #どちらでもないなら空のリスト
                altitude_list =[]
                return altitude_list
                
        return altitude_list
            

#四分位範囲を用いて外れ値を除去する関数(箱ひげ)
    def IQR_removal(self, data):
        data.sort()
        l = len(data)
        value_25 = l//4
        if value_25 == 0:  #データが4つ未満の場合
            return [] #空のリストを出力.なぜ元のリストではないのだろうか？------------------------
        else:
            quartile_25 = data[value_25]
            quartile_75 = data[value_25*3]
        IQR = quartile_75-quartile_25
        true_data = [i for i in data if quartile_25-1.5*IQR <= i <= quartile_75+1.5*IQR]
        return true_data


#高度をログで出力
    async def print_alt(self):
        
        while True:
            try:
                position = await asyncio.wait_for(self.get_position_alt(), timeout = 0.8)
                logger_info.info("altitude:{}".format(position))
                break
            except asyncio.TimeoutError:
                logger_info.info("Pixhawk might have some error")
                pass
            await asyncio.sleep(0)


#GPIOのピンを設定して出力を有効化する
#GPIO:Raspberry Pi上の信号ピンであるGPIOをコントロールするモジュール
    def fuse(self):
        
        try:
            GPIO.setmode(GPIO.BCM)  #GPIOのピン番号をピン番号にて指定することを表明
            GPIO.setwarnings(False)   #the channel is already in useエラーを出さないようにするための設定
            GPIO.setup(self.fuse_pin, GPIO.OUT, initial=GPIO.HIGH)    #ピンの設定.(ピン番号,出力設定,初期値の指定)
            logger_info.info("Fuse start")

            GPIO.output(self.fuse_pin, 0)      #出力を0Vに
            logger_info.info("-- Fusing")

            time.sleep(self.fuse_time)        #事前に設定したfuse_timeまつ
            logger_info.info("Fused")

            GPIO.output(self.fuse_pin, 1)     #出力を有効化(多分3.3V.自信はない)
        
        except:
            GPIO.output(self.fuse_pin, 1)     #うまくいかなかったらGPIOから出力させるようにする
            

#Lチカ.
    def LED(self):
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.fuse_pin, GPIO.OUT, initial=GPIO.LOW)   #初期設定は上と違ってLOW
            logger_info.info("Light start")

            GPIO.output(self.fuse_pin, 1)
            logger_info.info("-- Lighting")

            time.sleep(self.fuse_time)
            logger_info.info("Lighted")

            GPIO.output(self.fuse_pin, 0)
        
        except:
            GPIO.output(self.fuse_pin, 0)
            

#GPSが十分に作動しているかなどの確認.            
    async def health_check(self):
        
        logger_info.info("Waiting for drone to have a global position estimate...")
        
        health_true_count = 0

        async for health in self.pix.telemetry.health():        #ここのself.pix.telemetry.health()の内容がよくわからない。----------------------------------------
            if health.is_global_position_ok and health.is_home_position_ok:        #グローバル位置推定が「位置制御」モードでの飛行に十分 && ホームポジションが適切に初期化されている
                logger_info.info("gps ok")
                health_true_count += 1
            else:
                logger_info.info("gps ng")
                health_true_count = 0

            if health_true_count >= self.health_continuous_count:
                break
        logger_info.info("Global position estimate OK")


#MissionPlanを作成            
    async def upload_mission(self):
        mission_items = []
        mission_items.append(MissionItem(self.waypoint_lat,    #mission itemのリストの内容はリンク集を参照
                                        self.waypoint_lng,
                                        self.waypoint_alt,
                                        self.mission_speed,
                                        False,
                                        float('nan'),
                                        float('nan'),
                                        MissionItem.CameraAction.NONE,
                                        float('nan'),
                                        float('nan'),
                                        float('nan'),
                                        float('nan'),
                                        float('nan')))

        self.mission_plan = MissionPlan(mission_items)
        await self.pix.mission.set_return_to_launch_after_mission(False) #帰ってこないよう設定
        logger_info.info("Uploading mission")
        await self.pix.mission.upload_mission(self.mission_plan)


#アップロードしたmissionをスタートする        
    async def start_mission(self):

        logger_info.info("Starting mission")
        while True:
            try:
                await self.pix.mission.start_mission()
            except Exception as e:
                logger_info.info(e)
                logger_info.info("Failed start mission")
                await asyncio.sleep(0.1)
            else:
                logger_info.info("Started mission!")
                break


#Missio progressをlogに出力
    async def print_mission_progress(self):
        
        async for mission_progress in self.pix.mission.mission_progress():
            logger_info.info(f"Mission progress: "
                f"{mission_progress.current}/"
                f"{mission_progress.total}")
            

#in_air状態からin_airでなくなったら、task,eventloopをcancelする    
    async def observe_is_in_air(self, tasks):
        
        was_in_air = False
        async for is_in_air in self.pix.telemetry.in_air():
            if is_in_air:
                was_in_air = is_in_air

            if was_in_air and not is_in_air:
                for task in tasks:
                    task.cancel()
                    try:                            #taskがcancelされてるかの確認。いらないかも-------------------------------
                        await task
                    except asyncio.CancelledError:
                        pass
                await asyncio.get_event_loop().shutdown_asyncgens()

                return
            

#ミッションが終わっていたら着地処理に入る        
    async def mission_land(self):
        
        while True:
            await asyncio.sleep(1)
            mission_finished = await self.pix.mission.is_mission_finished()
            logger_info.info(mission_finished)
            if mission_finished:
                await self.land()


#mainとなるcycle_corutineをgatherする
    async def gather_main_coroutines(self):

        main_coroutines = [
            self.cycle_flight_mode(),
            self.cycle_mission_progress(),
            self.cycle_position_lat_lng(),
            self.cycle_lidar(),
            self.cycle_lora(),
            self.cycle_show(),
            self.cycle_wait_mission_finished()
        ]
        tasks = asyncio.gather(*main_coroutines)
        cancel_task = asyncio.create_task(self.tasks_cancel(tasks))
        await asyncio.gather(tasks, cancel_task, return_exceptions=True)


#着地関連のcorutineをgather
    async def gather_land_coroutines(self):

        land_coroutines = [
            self.cycle_pitch_roll(),
            self.cycle_is_in_air(),
            self.cycle_land()
        ]
        tasks = asyncio.gather(*land_coroutines)
        cancel_task = asyncio.create_task(self.tasks_cancel(tasks))
        await asyncio.gather(tasks, cancel_task, return_exceptions=True)


#入ってるmissionを消去する
    async def clear_mission(self):

        logger_info.info("Clearing mission...")
        await self.pix.mission.clear_mission()
        logger_info.info("Cleared mission")


#cycleでmissionが終わったかを判定し続ける
    async def cycle_wait_mission_finished(self):

        while True:
            await asyncio.sleep(1)
            mission_finished = await self.pix.mission.is_mission_finished()
            if mission_finished:
                logger_info.info("Mission finished")
                await self.lora.write("99")
                break
        self.is_tasks_cancel_ok = True 


#cycleでの着地判定
    async def cycle_land(self):

        await self.pix.action.land()
        while True:
            if abs(float(self.roll_deg)) > 60 or abs(float(self.pitch_deg)) > 60:   #機体が異常に傾いたら.これ以外にも判定方ありそう--------------------------
                logger_info.info("Hit the target!")
                await self.kill_forever()
            elif self.is_in_air == False:
                logger_info.info("Landed!")
                break
            await asyncio.sleep(0.01)
        self.is_tasks_cancel_ok = True 
        

#着地後にtaskをcancelするメソッド
    async def tasks_cancel(self, tasks):
        
        while True:
            await asyncio.sleep(1)
            if self.is_tasks_cancel_ok:
                break
        tasks.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


#GPSで機体をある位置に動かすメソッド。最悪これさえあれば動かすことはできそう----------------------------
    async def goto_location(self, lat, lng, abs_alt):

        logger_info.info("Setting goto_location...")
        await self.pix.action.goto_location(lat, lng, abs_alt, 0)


#カメラでターゲットの位置を推定
    async def estimate_target_position(self):

        async for d in self.pix.telemetry.distance_sensor(): #lidarの値を取得
            lidar_height = d.current_distance_m
            logger_info.info(f"current height:{lidar_height}m")
            break

        async for heading in self.pix.telemetry.heading():  #ドローンが向いている方向を取得
            heading_deg = heading.heading_deg
            logger_info.info(f"current heading: {heading_deg}") 
            break
        
        self.camera.change_iso(100) #iso感度(レンズから入ってきた光を、カメラ内でどのくらい増幅させるかの指標)を指定
        self.camera.change_shutter_speed(500)
        self.camera.take_pic()
        self.image_res = self.camera.detect_center()
        logger_info.info('percent={}, center={}'.format(self.image_res['percent'], self.image_res['center']))  #percent:画像内で物体が占める面積%,center:中心位置.なぜ背景が選択されないと保証できるかがわからなかった。--------------------------
        if self.image_res['percent'] <= 1e-8:
            logger_info.info(f"Failed image navigation")
            await self.land()
        else:
            logger_info.info(f"Target detected!")
            x_m, y_m = self.camera.get_target_position(lidar_height)  #ターゲットの位置を取得

            self.east_m = -np.cos(heading_deg*np.pi/180)*x_m-np.sin(heading_deg*np.pi/180)*y_m
            self.north_m = -np.sin(heading_deg*np.pi/180)*x_m+np.cos(heading_deg*np.pi/180)*y_m

            logger_info.info(f"go to the red position -- North:{self.north_m}m,East:{self.east_m}")  #機体固定座標における位置を記録(自信ない)--------------------------
        

#NED座標（航空機力学で使ってるz下が正の座標系）で位置を設定
    async def start_offboard_ned(self):

        logger_info.info("-- Setting initial setpoint")
        await self.pix.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0 , 0.0))
        await self.pix.offboard.start()


#カメラによるゴールの推定位置を設定   
    async def image_navigation_offboard_ned(self):

        await self.pix.offboard.set_position_ned(
            PositionNedYaw(self.north_m, self.east_m, 0.0, 0.0))
        

#赤い物体の位置を計算
    async def calc_red_position(self):

        lat_deg_per_m = 1.1883598784654418e-05
        lng_deg_per_m = 0.000008983148616

        await self.estimate_target_position()

        async for position in self.pix.telemetry.position():
            lat_now = position.latitude_deg
            lng_now = position.longitude_deg
            abs_alt = position.absolute_altitude_m
            break
        red_lat = lat_now+self.north_m*lat_deg_per_m
        red_lng = lng_now+self.east_m*lng_deg_per_m
        is_red_right_below = False
        if abs(self.image_res['center'][0])<0.2 and abs(self.image_res['center'][1])<0.2:
            is_red_right_below = True
        return red_lat, red_lng, abs_alt, is_red_right_below
        

#GPS座標を用いて画像航法
    async def image_navigation_goto(self):

        red_lat, red_lng, abs_alt= await self.calc_red_position()
        logger_info.info(f"[go to] red_lat:{red_lat}, red_lng:{red_lng}, abs_alt:{abs_alt}")
        await self.pix.action.goto_location(red_lat, red_lng, abs_alt, 0)
        await asyncio.sleep(10)
        

#offboardコントロールを止める。できなかった場合はそのまま着地に移行
    async def stop_offboard(self):

        logger_info.info("-- Stopping offboard")
        try:
            await self.pix.offboard.stop()
        except OffboardError as error:
            logger_info.info(f"Stopping offboard mode failed \
                    with error code: {error._result.result}")
            await self.land()


#killコマンド
    async def kill(self):

        await self.pix.action.kill()


#killし続けるコマンド
    async def kill_forever(self):

        while True:
            await self.pix.action.kill()
            await asyncio.sleep(0.1)


#lidarの高度を取得. get_lidar(self)との違いはbreakが入ってることだが、なぜ違うのか？------------------------------------
    async def measure_lidar_alt(self):

        async for distance in self.pix.telemetry.distance_sensor():
            self.lidar = distance.current_distance_m
            break


#        
    async def image_navigation_arliss(self):

        if self.available_camera:                                       #カメラが使用可能なら
            logger_info.info("Start image navigation")
            goal_start_abs_alt = await self.get_position_alt()         #初期位置からの相対高度を取得
            try:
                await asyncio.wait_for(self.measure_lidar_alt(), timeout = 1)       #lidarから高さを計測
            except asyncio.TimeoutError:
                logger_info.info("TimeoutError")
                await self.goto_location(self.waypoint_lat, self.waypoint_lng, goal_start_abs_alt - 5)      #相対高度を用いて飛行を試みる。5m高度を下げる
                await asyncio.sleep(5)
                try:
                    await asyncio.wait_for(self.measure_lidar_alt(), timeout = 1)        #もう一回lidarを試してみる
                except asyncio.TimeoutError:                                             #ダメだったらそのまま着陸
                    logger_info.info("TimeoutError")
                    await self.land()
            if self.lidar > 15:
                await self.goto_location(self.waypoint_lat, self.waypoint_lng, goal_start_abs_alt - 5)  #5m下げる
                await asyncio.sleep(5)
                await self.measure_lidar_alt()
                if self.lidar > 15:                                         #それでも15m以上上空ならそのまま着地.なぜこのような処理にしている?------------------------------
                    await self.land()
            goal_lidar_alt = self.lidar
            goal_abs_alt = await self.get_position_alt()
            await self.goto_location(self.waypoint_lat, self.waypoint_lng, goal_abs_alt - goal_lidar_alt + self.waypoint_alt)   #地面からself.waypoint_altの位置まで移動.この処理もなぜ？---------------------------
            await asyncio.sleep(5)

            red_lat, red_lng, abs_alt, is_red_right_below= await self.calc_red_position()
            lidar_alt = await self.get_distance_alt()
            logger_info.info(f"lidar:{lidar_alt}")
            logger_info.info(f"[go to] red_lat:{red_lat}, red_lng:{red_lng}, alt:{goal_abs_alt - goal_lidar_alt + 5}, abs_alt:{abs_alt}")
            await self.goto_location(red_lat, red_lng, goal_abs_alt - goal_lidar_alt + 5)  #地上から5mへ下降
            await asyncio.sleep(5)

            red_lat, red_lng, abs_alt, is_red_right_below= await self.calc_red_position()
            lidar_alt = await self.get_distance_alt()
            logger_info.info(f"lidar:{lidar_alt}")
            if is_red_right_below:   #真下にあるなら
                logger_info.info(f"Image Navigation Success!")
                await self.land()    #そのまま下降
            else :                   #ないなら
                logger_info.info(f"[go to] red_lat:{red_lat}, red_lng:{red_lng}, alt:{goal_abs_alt - goal_lidar_alt + 3}, abs_alt:{abs_alt}")
                await self.goto_location(red_lat, red_lng, goal_abs_alt - goal_lidar_alt + 3)    #地上から3mへ下降
                await asyncio.sleep(5)

            while True:      #真下にくるまで動き続ける
                red_lat, red_lng, abs_alt, is_red_right_below= await self.calc_red_position()
                lidar_alt = await self.get_distance_alt()
                logger_info.info(f"lidar:{lidar_alt}")
                logger_info.info(f"[go to] red_lat:{red_lat}, red_lng:{red_lng}, abs_alt:{abs_alt}")
                await self.goto_location(red_lat, red_lng, abs_alt)
                await asyncio.sleep(5)
                if is_red_right_below:
                    break

            logger_info.info(f"Image Navigation Success!")
            await self.land()
        else:                     #カメラ使用不可能ならそのまま着地
            await self.land()


#画像航法をして、エラー内容を出力
    async def perform_image_navigation_with_timeout(self):
        
        try:
            await asyncio.wait_for(self.image_navigation_arliss(), timeout = self.image_navigation_timeout)
        except asyncio.TimeoutError:
            logger_info.info("TimeoutError")
            await self.land()
        except Exception as e:
            logger_info.info(e)
            logger_info.info("Wild card error")
            await self.land()


#異常な傾きが生じたらkillそうでなければ着陸判定されるっまでlandする
    async def arliss_land(self):


        await self.pix.action.land()
        logger_info.info("Landing...")
        while True:
            await asyncio.sleep(0.01)
            is_in_air = await self.return_in_air()
            pitch, roll = await self.return_pitch_roll()
            logger_info.info(f"is_in_air:{is_in_air}, pitch:{pitch}, roll:{roll}")
            if not is_in_air:
                logger_info.info("Landed!")
                break
            if abs(float(roll)) > 30 or abs(float(pitch)) > 30:
                logger_info.info("Hit the target!")
                await self.kill()
                await asyncio.sleep(5)
                logger_info.info("Killed!")
                break

        