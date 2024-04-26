#include <TinyGPS++.h>
#include <TinyGPSPlus.h>
#include "SPI.h"
#include <Adafruit_DPS310.h>
#include <SoftwareSerial.h>
#include "eeprom_utility.h"
#include <string.h>

/*****************************
 *ARLISS2022 KINGFISHER*
 *ケース展開*
 *****************************/

int eeprom_cursor = 200;
int count2 = 0;
void nichidai_fall_speed_holder();

//オプション///////////////////////////////////////// ← ここの値を変えてモード等変更
#define h_default 0           // 基準高度　基準高度からの相対高度を出すのに使う
unsigned long wait_min = 2;              // 明るいところでの明るさをとった後に、暗いところでスタンバイするまでの待機時間(分)
#define MotorTimer 3000        // モーターが回転する時間(ms) 
#define cds_keep_time 200      // 光センサの継続受付時間(!!ms!!)
#define TimeJG_time_sec 15      // 時間判定の時間(s)、ケース放出されて光センサ反応してからの時間
#define cds_border_ratio 0.5   // 
//#define release_height -3200    // 分離を行う最大高度(m)　これを下回ったら分離する

#define bright_border_read false

#define fall_speed_read false

#define switch_num 0          //　デバック緩和用switch番号
                              //0:本番 1:EEPROM_utility 2:cds_test 3:motor_test 4:airP_test 5:カルマンフィルタ適用高度吐き
                              //6:gps_transmission_test
//ピン指定等//////////////////////////////////////////////////

//Adafruit_DPS310 dps;
TinyGPSPlus gps;

#define gps_RX 10
#define gps_TX 11
SoftwareSerial gpsSerial(gps_RX,gps_TX);

#define Lora_sleep 12
#define CDS_PIN 2              // 光センサのアナログピン番号
#define MOTOR_PIN 14           // ギヤードモーターのデジタルピン
#define DPS310_CS 10           // SPI通信の番号（？）
#define p_0 1013.25            // 海面気圧　ここを基準に高度を計算する

int counter = 0;               // 汎用カウンタ
bool frag = true;             // 汎用フラグ
unsigned long timer = 0;       // 汎用タイマ
unsigned long timer_ = 0;
sensors_event_t temp_event, pressure_event; 

//各種判定///////////////////////////////////////////////
unsigned long start_time;      // 放出時の時間
bool Released = false;         // 放出判定
bool Height_frag = false;           // 高度判定
bool Time_frag = false;             // 時間判定
unsigned long TimeJG_time = TimeJG_time_sec * 1000; // 時間判定の時間(ms)、ケース放出されて光センサ反応してからの時間
void Final_Judge();            // MotorGoをtrueにする最終判断

//EEPROM////////////////////////////////////////////
#define test_sequence_end 50              // テストシーケンス終了時に1
#define test_sequence_end_2 51 
#define motor_test_done 52 
#define cds_test_done 53 
#define airP_test_done 54 

#define dps310_connect_done 0 
#define cds_set_done 1 
#define release_done 2 
#define height_judge_done 3
#define time_judge_done 4
#define final_judge_done 5
#define motoron_done 6
#define motoroff_done 7
#define wait_till_dark 8

#define bright_border_val 100

//ギヤードモータ//////////////////////////////////////
// モーターを回す時にtrueにする
bool MotorGo = false;          
// 分離終了時にギヤードモータを停止させる
bool GoodByeSequence = false;  

//光センサ（CDS）/////////////////////////////////////
// 明るい時、ピンへの入力値がこれよりも大きくなる
float bright_border;         
// 閾値bright_borderの設定    
void CDS_set();               
 // 放出判定でReleaseをtrueに 
void CDS_Judge();       
//　CDSのテスト用      
void lightSensor_test();
bool cds_test_frag = false;

//気圧センサ//////////////////////////////////////////
float p=1013,T=26,h=0,h_=0; 
//p　センサから得た気圧
//T　センサから得た温度
//h　p,Tから計算した高度
// 高度を計算して，hに格納
void Cal_and_Set_height();  
//カルマンフィルタの初期値を上空で取得するためにicをtrueに           
void Set_top();       
// 高度判定でHeightをtrueに         
void Height_Judge();           

//カルマンフィルタ////////////////////////////////////

//x 観測値
//xPre　前の値
//xForecast　予測された観測値
//sigmaForecast　状態の予測誤差の分散
//sigmaState 状態方程式のノイズの分散
//sigmaSee 観測方程式のノイズの分散
float x,xPre_T,xPre_p,xForecast,kGain,sigmaForecast,sigmaState,sigmaSee;
//ic カルマンフィルタの初期値を一番最初だけセンサから取得する際のフラグ　上空でtrueにする
bool ic = true;
// カルマンフィルタ
void Kalman_Filter(float sigmaState,float sigmaSee,float xPre); 
// 気温にカルマンフィルタを2回適用
void Kalman_T();         
// 気圧にカルマンフィルタを2回適用      
void Kalman_p();       
// カルマンフィルタに突っ込むデータと，出てきたデータ        
float val_raw,val_filter;   
//　カルマンフィルタの初期値を格納　上空で実行する   
void Kalman_ic();
//　Tとpに対してカルマンフィルタをcount回だけ実行
void Kalman_for_T_and_p(int count);

//EEPROM_utility/////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//以上，設定///////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////

void setup() {
    Serial.begin(19200);         // Loraのbps値に注意
    
    gpsSerial.begin(9600); //gpsとの通信
    
    //EEPROM.update(dps310_connect_done,1);
    
    pinMode(MOTOR_PIN,OUTPUT);     // ギヤードモータのピンを設定
    
    if(bright_border_read){
        float x;
        EEPROM.get(bright_border_val,x);
        Serial.print(x);
        while(1);
    }
    
    switch (switch_num)
    {
    case 0:
         /*
        if ((! dps.begin_SPI(DPS310_CS) )) { //SPI通信ができていなかったら無限ループ．ｵﾜﾘ
            Serial.println("Failed to find DPS");
            EEPROM.update(dps310_connect_done,2);
            while(1);
        }

        dps.configurePressure(DPS310_64HZ, DPS310_64SAMPLES); // 気圧センサの周波数
        dps.configureTemperature(DPS310_64HZ, DPS310_64SAMPLES); 

        */

        /*
        Serial.println("bright_gain,dark_gain,bright_border");
        float aa = 0;
        for(int i = 800;i < 812;i+=4){
            EEPROM.get(i,aa);
            Serial.println(aa);
        }
        */

        pinMode(Lora_sleep,OUTPUT);  
        digitalWrite(Lora_sleep,HIGH);//Loraスリープモード突入
        
        CDS_set();
        break;
    case 1:
        eeprom_utility_setup();
        break;
    case 5:
        float x;
        Serial.println("previous h below");
        for(int i = eeprom_cursor;i <= 1020;i+=4){
            EEPROM.get(i,x);
            Serial.println(x);
            delay(1);
        }
        Serial.println("previous h above");
        delay(10);

        if (! dps.begin_SPI(DPS310_CS)) { //SPI通信ができていなかったら永遠にループ
          Serial.println("Failed to find DPS");
          while (1) yield();
        }
        dps.configurePressure(DPS310_32HZ, DPS310_32SAMPLES); // 気圧センサの周波数
        dps.configureTemperature(DPS310_32HZ, DPS310_32SAMPLES);
        break;
    case 6:
        pinMode(Lora_sleep,OUTPUT); 
        digitalWrite(Lora_sleep,HIGH);//Loraスリープモード突入
        delay(2000);
        break;
    default:
        break;
    }

}

/////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////

void loop() {
    switch (switch_num)
    {
    case 0:
        if(!Released){
            CDS_Judge();
                if(Released){
                start_time = millis();
                //Set_top(); // icをtrueへ変える
            }
        }
        else{
            /*
            while (!dps.temperatureAvailable() || !dps.pressureAvailable()) {
                return; // センサからの出力が正しく受け取れるまで空回り
            }
        
            dps.getEvents(&temp_event, &pressure_event);
            Set_temperature(temp_event.temperature);
            Set_pressure(pressure_event.pressure);
            
            // カルマンフィルタ使用時の初期条件をセンサ値から取得 最初だけ
            Kalman_ic();
            
            //Height_Judge();
            */
            
            Time_Judge();
            
            Final_Judge();
            
            if(MotorGo){
                motorON();
                EEPROM.update(motoron_done,1);
                for(int k = 0;k <= MotorTimer;k++){
                    delay(1);
                    if(k == MotorTimer){
                    GoodByeSequence = true;
                    MotorGo = false;
                    }
                }
            }
            
            if(GoodByeSequence){
                motorOFF();
                EEPROM.update(motoroff_done,1);
                //Serial.println("This is the end of my role !");
                //Serial.println("Have a good flight, bro...");

                digitalWrite(Lora_sleep,LOW);//スリープモード解除　安心のため5秒待機
                delay(5000);

                Serial.println("1");
                delay(6000);
                Serial.println("z");
                delay(6000);
                Serial.println("now in operaiton !");
                delay(6000);
                
                gps_transmission(); // ケースアルゴリズムの終点
            }
        }
        break;
    case 1://EEPROM_utility
        eeprom_utility_main();
        break;
    case 2://cds_test
        lightSensor_test();
        break;
    case 3://motor_test
        digitalWrite(MOTOR_PIN,HIGH);
        delay(100);
        digitalWrite(MOTOR_PIN,LOW);

        Serial.println("End of motor_test");
        EEPROM.update(motor_test_done,1);
        
        break;
    case 4://airP_test
        dps.getEvents(&temp_event, &pressure_event);
        Set_temperature(temp_event.temperature);
        Set_pressure(pressure_event.pressure);

        Cal_and_Set_height();

        Serial.print(Get_height() - h_default);
        Serial.println(" m");
        Serial.println("End of airP_test");
        EEPROM.update(airP_test_done,1);
        break;
    case 5://カルマンフィルタ適用高度吐き
        dps.getEvents(&temp_event, &pressure_event);
        Set_temperature(temp_event.temperature);
        Set_pressure(pressure_event.pressure);
               
        Kalman_ic();
      
        Kalman_for_T_and_p(1000);

        timer = millis();
        
        Serial.print("h = ");
        Serial.print(Get_height()-h_);
        Serial.print("  :  ");
        Serial.println(timer - timer_);
        if(eeprom_cursor<=1020){
          EEPROM.put(eeprom_cursor,Get_height()-h_);
          //　時間間隔はほぼ670
          eeprom_cursor += 4; 
        }
        h_ = Get_height();
        timer_ = timer;
        
        break;
    case 6:
        digitalWrite(Lora_sleep,LOW);//スリープモード解除　安心のため5秒待機
        delay(5000);
        
        Serial.println("1");
        delay(6000);
        Serial.println("z");
        delay(6000);
        Serial.println("now in operaiton !");
        delay(6000);
        
        gps_transmission(); // GPS無限送信を行うので break; に意味はない
        break;
    default:
        Serial.print("switch_num undefined");
        while(1);
    }
}

//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//以下，関数///////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////

void lightSensor_test(){
  int light_analog_data;
  float voltage;

  light_analog_data = analogRead(CDS_PIN);//アナログ0番ピンの入力状態をanalog_dataに代入
  
  Serial.println(light_analog_data);//「voltage」を送信
  
  /*
  if(light_analog_data>600){
    cds_test_frag = true;
  }
  */
}

void motorON(){ // モータをONにする
  digitalWrite(MOTOR_PIN,HIGH);
}

void motorOFF(){ // モータをOFFにする
  digitalWrite(MOTOR_PIN,LOW);
}

void Cal_and_Set_height(){                                                   
  float x;
  x = (pow(p_0/Get_pressure(),0.1902)-1)*(Get_temperature()+273.15)*153.846;
  Set_height(x);
}

void Kalman_Filter(float sigmaState,float sigmaSee,float xPre){
    //状態方程式に基づいた、状態の予測  
    xForecast = xPre;
    //予測誤差の分散は、状態方程式の分散との足し合わせ
    sigmaForecast = sigmaForecast + sigmaState; 
    //カルマンゲイン、状態の予測誤差の分散が大きければ、あまり補正されない。観測方程式のノイズの分散が小さければ、大きく補正される。
    kGain = sigmaForecast/(sigmaForecast + sigmaSee); 
    //カルマンゲインを使って補正
    val_filter = xForecast + kGain * (x - xForecast);
    //本物の観測値を元に、予測誤差の分散を補正
    sigmaForecast = (1 - kGain) * sigmaForecast;
}

// 気温にカルマンフィルタを2回適用
void Kalman_T(){                                  
  val_raw = Get_temperature();
  x = val_raw;
  Kalman_Filter(500,200,xPre_T);
  x = val_filter;
  Kalman_Filter(500,200,xPre_T);
  xPre_T = val_filter;
  Set_temperature(val_filter);    
}

// 気圧にカルマンフィルタを2回適用
void Kalman_p(){                                  
  val_raw = Get_pressure();
  x = val_raw;
  Kalman_Filter(500,200,xPre_p);
  x = val_filter;
  Kalman_Filter(500,200,xPre_p);
  xPre_p = val_filter;
  Set_pressure(val_filter);  
}

//閾値bright_borderの設定
void CDS_set(){
  //Serial.println("bright_gain set start!");
  float bright_gain;
  for(int i = 0;i < 100;i++){
    bright_gain += analogRead(CDS_PIN);
    //Serial.println(bright_gain);
  }
  bright_gain /= 100;
  //Serial.print("bright_gain : ");
  //Serial.println(bright_gain);
  //EEPROM.put(800,bright_gain);

  unsigned long wait_mili = wait_min*60*1000;
  unsigned long wait_start_time = millis();
  while(1){
    /*
    Serial.print(millis());
    Serial.print(" : ");
    Serial.print(wait_start_time);
    Serial.print(" + ");
    Serial.print(wait_mili);
    Serial.print(" = ");
    Serial.println(wait_start_time + wait_mili);
    */
      if(millis() > wait_start_time + wait_mili){   // 暗闇で十分待機したら半無限ループから抜ける
        EEPROM.update(wait_till_dark,1);
        //Serial.println("end dark_loop");
        break;
      }
  }
  //Serial.println("dark_gain set start!");
  float dark_gain;
  for(int i = 0;i < 100;i++){
    dark_gain += analogRead(CDS_PIN);
  }
  
  dark_gain /= 100;
  //EEPROM.put(804,dark_gain);
  /*
  if(dark_gain > 600){
    dark_gain = 600;
  }
  */
  
  //Serial.print("dark_gain : ");
  //Serial.println(dark_gain);
  
  bright_border = (bright_gain + dark_gain)*cds_border_ratio;
  //EEPROM.put(808,bright_border);
  //Serial.print(",bright_border : ");
  //Serial.println(bright_border);
  
  EEPROM.update(cds_set_done,1);
}

// 放出判定でReleasedをtrueに CDSセルは光が当たると抵抗値が小さくなりピンの入力値が大きくなる
void CDS_Judge(){ 
  float cds_gain; 
  unsigned long cds_time = millis();
  while(1){
    cds_gain = analogRead(CDS_PIN);
    /*
    Serial.print("CDS :");
    Serial.println(cds_gain);
    Serial.print("cds_gain : ");
    Serial.print(cds_gain);
    Serial.print(", bright_border :");
    Serial.println(bright_border);
    */
    if(cds_gain < bright_border){                 // 暗かったら時間リセット
      cds_time = millis();
    }
    if(millis() > cds_time + cds_keep_time){
      break;
    }
  }
  Released = true;                                // 5秒ずっと明るい判定だったら、OK
  EEPROM.update(release_done,1);
  //Serial.println("Released = true!");
  //EEPROM.put(bright_border_val,bright_border);
  /*
  unsigned long t__;
  t__ = millis();
  EEPROM.put(900,t__);
  */
}

void Set_top(){
  ic = true;                                      // 機体放出につき気圧・温度の初期条件フラグON
}

void Height_Judge(){
    Kalman_for_T_and_p(1000);
    if(Get_height() < release_height){
        Height_frag = true;
        EEPROM.update(height_judge_done,1);
    }
}

void Time_Judge(){
  /*
  Serial.print("millis() - start_time : ");
  Serial.print(millis() - start_time);
  Serial.print(", TimeJG_time : ");
  Serial.println(TimeJG_time);
  */
  if(millis() - start_time > TimeJG_time){ 
    Time_frag = true;
    EEPROM.update(time_judge_done,1);
    //Serial.println("Time_judge OK");
  }
}

void Final_Judge(){
  /*
  if(Released){
    Serial.println("Released = true");
  }
  if(Time_frag){
    Serial.print("Time_frag = true");
  }
  */
  
  //if((Released && Height_frag) || (Released && Time_frag)){
  
  if(Time_frag){
    MotorGo = true;
    EEPROM.update(final_judge_done,1);
  } 
  
}

void Set_height(float h_){
    h = h_;
}

float Get_height(){
    return h;
}

void Set_pressure(float p_){
  p = p_;
}

float Get_pressure(){
  return p;
}

void Set_temperature(float T_){
  T = T_;
}

float Get_temperature(){
  return T;
}

void nichidai_fall_speed_holder(){
    int k = 0;
    unsigned long tt;
    unsigned long tt_;
    double velocity_now = 0;
    float height_now = 0;
    float height_prev = 0;
    while(1){
        if(k > 50){
            while(1);
        }
        else{ 
            dps.getEvents(&temp_event, &pressure_event);
            T = temp_event.temperature;
            p = pressure_event.pressure;
            Cal_and_Set_height();
            height_prev = Get_height();
            
            delay(500);
            
            dps.getEvents(&temp_event, &pressure_event);
            T = temp_event.temperature;
            p = pressure_event.pressure;
            Cal_and_Set_height();
            height_now = Get_height();
            velocity_now = abs(height_prev - height_now)*1000 / 500;
            
            EEPROM.put(eeprom_cursor,velocity_now);
            Serial.print(" height_prev - height_now : ");
            Serial.print(height_prev);
            Serial.print(" - ");
            Serial.print(height_now);
            Serial.print(" , ");
            Serial.print(500);
            Serial.print(",tt_-tt : ");
            Serial.print(tt_-tt);
            Serial.print(" ,velocity_now : ");
            Serial.println(velocity_now);
            
            eeprom_cursor += 4;
            k++;
        }
    }
}

void Kalman_ic(){
    if(ic){ // カルマンフィルタ使用時の初期条件をセンサ値から取得
      xPre_T = Get_temperature();
      xPre_p = Get_pressure();
      ic = false;
    }
}

void Kalman_for_T_and_p(int count){
    for(int k = 0;k < count;k++){
    Kalman_T();
    Kalman_p();
    }
    Cal_and_Set_height(); // カルマンフィルタのかかった高度をhに格納  
}

void gps_transmission(){
    while(1){
        /*
        String strlat;
        String strlon;
        String stralt;
        */
        while (gpsSerial.available() > 0){
            gps.encode(gpsSerial.read());
            if(gps.location.isUpdated()){
                /*
                strlat = gps.location.lat();
                strlon = gps.location.lng();
                stralt = gps.altitude.meters();
                Serial.println(strlat + "/"  + strlon + "/" + stralt);
                */
                Serial.print(gps.location.lat(),6);
                Serial.print("/");
                Serial.println(gps.location.lng(),6);

                delay(20000);
                /*
                for(int i = 28;i < 40;++i){
                    EEPROM.write(i,0);
                }
                EEPROM.put(28,lat);
                EEPROM.put(32,lon);
                EEPROM.put(36,alt);
                */
            }
        }
    }
}

void Test_func(){
  Serial.println("Now testing...");
}
