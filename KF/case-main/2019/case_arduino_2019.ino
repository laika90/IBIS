#include <Ethernet.h>

/*****************************
 *ARLISS2019 EVENT HORIZON*
 *ケース展開*
 *****************************/

#include "Arduino.h"
#include "SPI.h"
#include "AE_MPL115A1.h"
#include <TinyGPS++.h>
#include <SoftwareSerial.h>

/*気圧センサのピン対応（センサ - arduino）
 * 5CS - D10
 * 6DOUT - D12
 * 7DIN - D11
 * 8SCLK - D13
 */
 
#define LoraSW 9 //MOSFETのLoraのスイッチピン
#define CDS_PIN A7 //CDSの入力ピン
#define RX_PIN 2 //GPS用にarduinoのピンを設定
#define TX_PIN 3 //GPS用にarduinoのピンを設定

//Cut_PIN2がケース展開の閂、Cut_PIN4が機体放出の閂
#define Cut_PIN1 5
#define Cut_PIN2 4
#define Cut_PIN3 6
#define Cut_PIN4 7

#define wait_min 15  //スイッチ入れて明るいところでの明るさをとった後に、暗いところでスタンバイするまでの待機時間(分)

int bright_border = 900;  //明るい時、ピンへの入力値がこれよりも大きくなる

void CDS_set();//閾値bright_borderの設定

#define TimeJG_time_sec 10 //時間判定の時間(秒)、ケース放出されて光センサ反応してからの時間
unsigned long TimeJG_time = TimeJG_time_sec*1000;

#define h_difference 0  //地上で測った時の気圧に基づく、地上０ｍの高度
#define h_border -120   //機体放出高度(m)、これより低くなると展開

TinyGPSPlus gps;
SoftwareSerial mySerial(RX_PIN,TX_PIN);

unsigned long start_time; //放出時の時間
bool Release = false; //放出判定
bool Hight = false;   //高度判定
bool Time = false;    //時間判定


//loop/////////////////////////////////////////
void CDS_JG();//放出判定でReleaseをtrueに
void Set_top();//放出時の気圧を測定し、カルマンフィルタの初期値設定
void Hight_JG();//高度判定でHightをtrueに
void Time_JG();//時間判定でTimeをtrueに
void GPS();//GPSの値をLoraから送信
void Cut();//テグス溶断→閂抜き


//カルマンフィルタ/////////////////////////////////////////////
float x,xPre,xForecast,kGain,sigmaForecast,sigmaState,sigmaSee;
//x 観測値
//xPre　前の値
//xForecast　予測された観測値
//sigmaForecast　状態の予測誤差の分散
//sigmaState 状態方程式のノイズの分散
//sigmaSee 観測方程式のノイズの分散
void Kalman_Filter(float sigmaState,float sigmaSee);
float val_raw,val_filter;

//////////////////////////////////////////////////////////


void setup() {
  Serial.begin(19200); //モニターに出力するための設定
  pinMode(LoraSW,OUTPUT);//スイッチ
  digitalWrite(LoraSW,LOW);

  pinMode(Cut_PIN1,OUTPUT);
  pinMode(Cut_PIN2,OUTPUT);
  pinMode(Cut_PIN3,OUTPUT);
  pinMode(Cut_PIN4,OUTPUT);
  digitalWrite(Cut_PIN1,LOW);
  digitalWrite(Cut_PIN2,LOW);
  digitalWrite(Cut_PIN3,LOW);
  digitalWrite(Cut_PIN4,LOW);
  

  // set the data rate for the SoftwareSerial port
  mySerial.begin(9600);
  mySerial.println("Hello, world?");

  //MPL115A1　気圧計の初期化 
  SPI_MPL115A1_Init();
  //MPL115A1　補正データ読出し
  SPI_MPL115A1_ReadCoefficient();
  xPre = 0;//カルマンフィルタの適当な初期化

  //Serial.println("program start");

  CDS_set();//閾値bright_borderの設定
}

void loop() {
  if(Release == false){
    CDS_JG(); //放出判定でReleaseをtrueに
    if(Release == true){ //一度だけ実行、次のループからは前段階でスルー     
      start_time = millis(); //放出時の時間を保存
      //Serial.print("start_time :");
      //Serial.println(start_time);
      //Serial.println();      
      digitalWrite(LoraSW,HIGH); //Loraの通信開始
      Set_top();//放出時の気圧を測定し、カルマンフィルタの初期値設定
    }
  }else{ //ケース放出判定後の動作
    GPS();//GPSの値をLoraから送信(1000回ジャッジして1回GPS)
          //ジャッジしてからGPSの順だと送信してる間に落下しちゃうから、ジャッジの前に配置

    //カルマンフィルタの制御のために、高さ制御のジャッジをたくさんやる
    int k;
    for(k = 0;k < 1000;k++){
      Hight_JG();//高度判定でHightをtrueに
      if(Hight == true)break;
    }
    
    Time_JG();//時間判定でTimeをtrueに これは刻む必要ない
              //時間判定の後に高度判定1000回やるのは無駄なので、後ろに配置
    if(Hight == true || Time == true){
      //Serial.println("Cut start");      
      Cut();//テグス溶断→閂抜き
      //Serial.println("Cut finished");

      unsigned long gps_time = millis();
      while(1){
        String strlat;
        String strlon;
        String stralt;
        if(mySerial.available() > 0){
          gps.encode(mySerial.read());
          if (gps.location.isUpdated()){
            strlat = gps.location.lat();
            strlon = gps.location.lng();
            stralt = gps.altitude.meters();
            if(millis() > gps_time + 7000){
              Serial.println(strlat + "/"  + strlon + "/" + stralt);
              gps_time = millis();
            }
          }
        }
      }
    }
  }
}


void Kalman_Filter(float sigmaState,float sigmaSee){
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


//閾値bright_borderの設定
void CDS_set(){
  unsigned long bright_gain;
  int i;
  for(i = 1;i < 100;i++){
    bright_gain += analogRead(CDS_PIN);
  }
  bright_gain /= 100;

  unsigned long wait_mili = wait_min*60*1000;
  unsigned long wait_start_time = millis();
  while(1){
    if(millis() > wait_start_time + wait_mili){
      break;
    }
  }
  unsigned long dark_gain;
  for(i = 1;i < 100;i++){
    dark_gain += analogRead(CDS_PIN);
  }
  dark_gain /= 100;
  bright_border = (bright_gain + dark_gain)/2;
}


void CDS_JG(){ //放出判定でReleaseをtrueに、CDSセルは光が当たると抵抗値が小さくなりピンの入力値が大きくなる
  int cds_gain;
  unsigned long cds_time = millis();
  while(1){
    cds_gain = analogRead(CDS_PIN);
    //Serial.print("CDS :");
    //Serial.println(cds_gain);
    if(cds_gain < bright_border){  //暗かったら時間リセット
      cds_time = millis();
    }
    if(millis() > cds_time + 5000){
      break;
    }
  }
  Release = true; //5秒ずっと明るい判定だったら、おっけい
}


void Set_top(){//放出時の気圧を測定し、カルマンフィルタの初期値設定
  float baro_top = 0;  
  int i = 0;
  for(i = 0;i < 50;i++){ //50回の平均をとる
    //MPL115A1　気圧のＡＤ値読出し
    SPI_MPL115A1_ReadPressure();
    //MPL115A1　計算後の気圧データ (hPa)
    baro_top += SPI_MPL115A1_Pressure();//10分の1の値
  }
  baro_top /= 5;

  //Serial.print("h_top : ");
  //Serial.println(44330.8*(1.0-pow((baro_top/1013.25), 0.190263)));
  //Serial.println();
  
  xPre = baro_top; //カルマンフィルタで用いる初期値
}

void Hight_JG(){//高度判定でHightをtrueに

  float h_now;
  
  //MPL115A1　気圧のＡＤ値読出し
  SPI_MPL115A1_ReadPressure();
  //MPL115A1　計算後の気圧データ (hPa)
  val_raw = SPI_MPL115A1_Pressure() * 10;

  //カルマンフィルタ（2回かけてる）
  x = val_raw;
  Kalman_Filter(100,1000);
  x = val_filter;
  Kalman_Filter(100,1000);
  xPre = val_filter;

  //val_filterに気圧の値//

  h_now = 44330.8*(1.0-pow((val_filter/1013.25), 0.190263));

  //Serial.print("h_now : ");
  //Serial.println(h_now);

  if(h_now < h_border + h_difference){
    Hight = true;
    //Serial.println(); 
    //Serial.println("Judged by Hight");
    //Serial.println();
  }
}

void Time_JG(){//時間判定でTimeをtrueに
  if(millis() - start_time > TimeJG_time - 5000){ //光センサの判定のところで５秒経っている
    Time = true;
    //Serial.println("Judged by Time");
    //Serial.print("end time :");
    //Serial.println(millis());
    //Serial.println();
  }
}

void GPS(){//GPSの値をLoraから送信
  String strlat;
  String strlon;
  String stralt;
  if(mySerial.available() > 0){
    gps.encode(mySerial.read());
    if (gps.location.isUpdated()){
      strlat = gps.location.lat();
      strlon = gps.location.lng();
      stralt = gps.altitude.meters();
      Serial.println(strlat + "/"  + strlon + "/" + stralt);
    }
  }
}

void Cut(){//テグス溶断→閂抜き
  digitalWrite(Cut_PIN2,HIGH);
  delay(10000); //展開待ち
  digitalWrite(Cut_PIN4,HIGH);
}
