# Teremetry
## mavsdk.teremetry.Teremetry
機体のテレメトリーと状態情報（バッテリー、GPS、RC接続、フライトモードなど）を取得し、テレメトリーの更新レートを設定できるようにするクラス。全て非同期asyncで定義されている。
### actuator_control_target()
"actuator control target"の最新情報を出力する。  
actuator control targetはモーターの制御対象となるグループと、そのコントロールに関する情報。
- groupe
  - 制御対象を定める(先輩は使ってなくて、よくわからん)。
- controls
  - actuatorの制御を指示。
### armed()
"armed"の最新情報を出力する。  
armedはarm状態かどうかのbool値情報。
- is_armed
  - arm状態ならTrue
### attitude_angular_verocity_body()
"attitude" の最新情報を出力(angular verocity)。  
angular velocityは機体の角速度。
- roll_rad_s
  - roll角速度
- pitch_rad_s
  - pitch角速度
- yaw_rad_s
  - yaw角速度
### attitude_euler()
"attitude"の最新情報を出力(Euler)。  
eulerは機体の姿勢情報を表すオイラー角。
- roll_deg
  - roll
- pitch_deg
  - pitch
- yaw_deg
  - Yaw
### battery()
"battery"の最新情報を出力。
batteryはバッテリーの情報
- voltage_v
  - 電圧(V)
- remaining_percent
  - 推測されるバッテリー残量(%)
### distance_sensor()
"Distance Sendor"の最新情報を出力。
Distance Sensorはセンサが読み取った距離情報(なんの距離かまだわかってないです、、実験したい)。
- minimum_distance_m
  - 最小距離
- maximum_distance_m
  - 最大距離
- current_distance_m
  - 現在の距離
### flight_mode()
"flight mode"の最新情報を出力する。 
flight modeは機体の動きをどのように管理するかを定義するものである。
- 手動モード
  - 今回は使わないが、flight modeは手動モードと自立モードに分かれる。
- 自立モード(Autonomous)
  - Multicopterの場合次の7状態が提供されている。
    - Hold Mode
      - 現在の座標と高度を維持するため、停止し、ホバリングを行うモード。風邪等の影響も考慮して維持を行う。
    - Return Mode
      - 機体が安全な場所へ開けた経路を辿って飛行する。細かい設定もできるが、デフォルトでは安全な高さまで上昇しホームポジションまで飛行した後、着陸する。
    - Mission Mode
      - flight controllerにアップロードされた事前定義されたミッションを機体が実行する。
    - Takeoff Mode
      - 離陸高度まで素直に上昇し、その場でホバリングをする。
    - Land Mode
      - Land Modeに移行した座標のまま機体が着陸を行う。
    - Follow Me Mode
      - 自立的にユーザーを追尾する。多分使わない。
    - Offboard Mode
      - MAVLinkで指定された位置、速度、姿勢野設定値に機体を従わせる。
### gps_info()
"GPS info"の最新情報を出力。  
GPS infoはGPSの情報。
- num_satellites
  - GPSに用いることのできる衛星の数
- fix_type
  - 0:no GPS (衛星なし？)  
  1:no fix (測位不能)  
  2:2D fix (平面情報取得)
  3:3D fix (高度も取得)
  4:DGPS fix (より高精度)
  5:RTK float (精度上昇)
  6:RTK fixed (数センチ誤差)
### health()
"health"の最新情報を出力する。  
healthはドローンが正常な状態か否かを判断するbool値。
- is_gyrometer_calibration_ok
  - ジャイロセンサがキャリブレーションされていたらTrue
- is_accelerometer_calibration_ok
  - 加速度センサがキャリブレーションされていたらTrue
- is_magnetometer_calibrration_ok
  - 地磁気がキャリブレーションされていたらTrue
- is_local_position_ok
  - local positionの推定値が飛行するのに十分な値であればTrue
- is_grobal_position_ok
  - grobal positionの推定値が飛行するのに十分な値ならTrue
- is_home_position_ok
  - home positionが正しく初期化されていればTrue
- is_armable
  - arm可能であればTrue
### health_all_ok()
"HealthAllOk"の最新情報を出力。  
HealthAllOkは上記のhealthが全てOKかどうかのbool値？
- is_health_all_ok
  - healthが全てOKならTrue？
### home()
"home position"の最新情報を出力。  
home positionは帰還するべき場所。
- latitude_deg
  - 緯度
- longitude_deg
  - 経度
- absolute_altitude_m
  - 平均海面高からの絶対高度
- relative_altitude_m
  - takeoff高度からの相対高度
### in_air()
"in air"の最新情報を出力。  
わかんないけど何かのbool値。
- is_in_air
### odometry()
"odometry"の最新情報を出力する。  
odometryとは車輪型移動ロボットにおける車輪やステアリングの回転角度の計算から、それぞれの移動量を求め、その累積計算からロボットの位置を推定する手法。
- position_body
  - x_m
    - x座標
  - y_m
    - y座標
  - z_m
    - z座標
- verocity_body
  - x_m_s
    - x方向速度
  - y_m_s
    - y方向速度
  - z_m_s
    - z方向速度
- angular_verocity_body
  - roll_rad_s
    - roll角速度
  - pitch_rad_s
    - pitch角速度
  - yaw_rad_s
    - yaw角速度
### position()
"position"の最新情報を出力する。  
positionはドローンの三次元座標を表す数値情報。
homeと同じメンバ変数を持つ。
### rc_status()
"RC status"の最新情報を出力する。  
RC statusはremot controlの状態。
- is_available
  - rcがavailableならTrue
- signal_strength_percent
  - 信号の強さ(%)
### status_text()
"status text"の最新情報を出力。  
status textはメッセージ型の情報。おそらくpixhawkからなんかの情報が送られてくる？
- INFO 
  - 情報
- WARNING
  - 警告
- CRITICSL
  - 重要
### unix_epoch_time()
"unix epoch time"の最新情報を出力する。  
unix epoch timeは時刻情報。
- time_us
  - 時刻を表示
### verocity_ned()
"ground speed"の最新情報を出力。  
ground speedはローカル座標系における速度。NEDフレーム(North East Down)で表現される。
- north_m_s
  - 北方向の速度
- east_m_s
  - 東方向の速度
- down_m_s
  - 鉛直下向き速度