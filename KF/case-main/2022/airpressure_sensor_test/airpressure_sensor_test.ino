#include <Adafruit_DPS310.h>
#include <EEPROM.h>

/*****************************
 *ARLISS2022 KINGFISHER*
 *大気圧センサ*
 *****************************/

Adafruit_DPS310 dps; // センサの構造体を生成

#define DPS310_CS 10           // SPI通信の番号（？）
#define p_0 1013.25            // 海面気圧　ここを基準に高度を計算する

unsigned long fall_timer;      // 落下速度タイマー (ms)
unsigned long fall_dt;         // 落下速度計測用時間差分(ms)
float height_now;              // 現在の高度
float height_prev = 0;         // 1ステップ前の高度
double velocity_now;           // 現在の速度
double velocity_max = 0;       // 暫定最大速度

int counter = 0;               // 汎用カウンタ
bool frag = false;             // 汎用フラグ

#define max_adress 0
double zero = 0;

double velocity;
int eeprom_cursor = 4;

//オプション////////////////////////////////////////// ← ここの値を変えてモード変更
#define h_default 0              // 基準高度　基準高度からの相対高度を出すのに使う
#define ifKalman true            // カルマンフィルタのテストを行う場合　true
#define fallSpeed_test false        // パラシュート落下速度実験時　true
#define fallSpeed_test_EEPROM false // 同上試験のEEPROM読み取り

//高度計算////////////////////////////////////////////
float p,T,h; 
//p　センサから得た気圧
//T　センサから得た温度
//h　p,Tから計算した高度
void Cal_height(); 

//カルマンフィルタ/////////////////////////////////////
float x,xPre_T,xPre_p,xForecast,kGain,sigmaForecast,sigmaState,sigmaSee;
bool ic = true;
//x 観測値
//xPre　前の値
//xForecast　予測された観測値
//sigmaForecast　状態の予測誤差の分散
//sigmaState 状態方程式のノイズの分散
//sigmaSee 観測方程式のノイズの分散
//ic カルマンフィルタの初期値を一番最初だけセンサから取得する際のフラグ
void Kalman_Filter(float sigmaState,float sigmaSee); // カルマンフィルタ
void Kalman_T(); // 気温にカルマンフィルタを2回適用
void Kalman_p(); // 気圧にカルマンフィルタを2回適用
float val_raw,val_filter;

/////////////////////////////////////////////////////

void setup() {
  //delay(30000);
  Serial.begin(115200); //モニターに出力するための設定
  while (!Serial) delay(10); //接続まで待つ
  ///*
  if (! dps.begin_SPI(DPS310_CS)) { //SPI通信ができていなかったら永遠にループ
    Serial.println("Failed to find DPS");
    while (1) yield();
  }
  //*/
  
  Serial.println("DPS OK!"); // 気圧センサの接続OK!

  dps.configurePressure(DPS310_32HZ, DPS310_32SAMPLES); // センサ取得頻度を指定
  dps.configureTemperature(DPS310_32HZ, DPS310_32SAMPLES); // センサ取得頻度を指定
  
  if(fallSpeed_test){
    fall_timer = millis(); // 落下試験のときはここでタイマー動かしとく（初動辻褄合わせ用）
  }
}

void loop() {
  if(fallSpeed_test_EEPROM){
    EEPROM.get(max_adress,velocity_max);
    Serial.print("velocity_max == ");
    Serial.println(velocity_max);
    for(int i = 1;4*i < 1024;i++){
        EEPROM.get(4*i,velocity);
        Serial.println(velocity);
      }
    EEPROM.put(max_adress,zero);
    while(1);
  }
  
  sensors_event_t temp_event, pressure_event;
  
  while (!dps.temperatureAvailable() || !dps.pressureAvailable()) {
    return;          // センサからの出力が正しく受け取れるまで空回り
  }
  
  if(fallSpeed_test){
    dps.getEvents(&temp_event, &pressure_event);
    T = temp_event.temperature;
    p = pressure_event.pressure;
    Cal_height();
    
    fall_dt = (millis() - fall_timer); // 単位はms
    //Serial.print("fall_dt == ");
    //Serial.println(fall_dt);
    height_now = h;
    velocity_now = (height_prev - height_now) / fall_dt ; // 単位はm/ms
    velocity_now *= 1000;
    if(velocity_now >= 15){
      return;
    }
    if(eeprom_cursor < 1024 ){
      if(velocity_now > 0){
        EEPROM.put(eeprom_cursor,velocity_now);
        Serial.print("velocity now == ");
        Serial.print(velocity_now);
        Serial.print(" : eeprom ");
        Serial.println(eeprom_cursor/4);
        eeprom_cursor += 4;
      }
    }
    
    if(velocity_now > velocity_max){
      velocity_max = velocity_now;
      EEPROM.put(max_adress,velocity_max); // EEPROMへ暫定最大速度を書き込み
      Serial.print("velocity_max == ");
      Serial.println(velocity_max);
    }
    
    fall_timer = millis();
    height_prev = height_now;
    return;
  }
  
  dps.getEvents(&temp_event, &pressure_event);
  T = temp_event.temperature;
  p = pressure_event.pressure;

  /*
  Serial.print(F("Temperature = "));
  Serial.print(T);
  Serial.println(" *C");

  Serial.print(F("Pressure = "));
  Serial.print(p);
  Serial.println(" hPa"); 
  */
  
  Cal_height();
  Serial.print(F("Altitude = "));
  Serial.print(h - h_default);
  Serial.println(" m");

  if(ic){ // カルマンフィルタ使用時の初期条件をセンサ値から取得
    xPre_T = T;
    xPre_p = p;
    ic = false;
  }

  if(ifKalman){ 
    for(int k = 0;k<1000;k++){
      Kalman_T();
      Kalman_p();
    }
    Cal_height();
    
    Serial.print(F("Kalman Altitude = "));
    Serial.print(h - h_default);
    Serial.println(" m");
  }
}

void Cal_height(){  /*気圧と温度から高度を計算する　w/ global h,p,T : 高度,気圧,温度　
                                                   constant p_0　: 海面気圧      */
  h = (pow(p_0/p,0.1902)-1)*(T+273.15)*153.846;
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

void Kalman_T(){// 気温にカルマンフィルタを2回適用
  val_raw = T;
  x = val_raw;
  Kalman_Filter(500,200,xPre_T);
  x = val_filter;
  Kalman_Filter(500,200,xPre_T);
  xPre_T = val_filter;
  T = val_filter;     
  
}

void Kalman_p(){// 気圧にカルマンフィルタを2回適用
  val_raw = p;
  x = val_raw;
  Kalman_Filter(500,200,xPre_p);
  x = val_filter;
  Kalman_Filter(500,200,xPre_p);
  xPre_p = val_filter;
  p = val_filter;  
}
