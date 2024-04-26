#ifndef _CLASS_PRES_H
#define _CLASS_PRES_H
#include <arduino.h>
#include <Wire.h>

#define BME280_ADDR 0x76
#define CONFIG 0xF5
#define CTRL_MEAS 0xF4
#define CTRL_HUM 0xF2

class pres
{
  //落下するまではset_pre_altitude_ -> judge_altitude_
  int minnimam_height = 3.5;
  int marge1 = 1.5; //m、上昇判定の余裕
  int marge2 = 1.5; //m、落下判定のための余裕
  int marge3 = 1.5; //m、地面基準上昇判定のための余裕
  int marge4 = 1.5; //m、地面基準落下判定のための余裕
  uint16_t dig_T1;
  int16_t  dig_T2;
  int16_t  dig_T3;
  uint16_t dig_P1;
  int16_t  dig_P2;
  int16_t  dig_P3;
  int16_t  dig_P4;
  int16_t  dig_P5;
  int16_t  dig_P6;
  int16_t  dig_P7;
  int16_t  dig_P8;
  int16_t  dig_P9;
  unsigned char dac[26];
  unsigned int i;

  int32_t t_fine;
  int32_t adc_P, adc_T, adc_H;

  int32_t  temp_cal;
  uint32_t pres_cal;
  float temp;
  //℃
  float pressure;
  //hPa
  float altitude_;
  //m
  static float ground_pres;
  static float ground_altitude_;
  static float ground_T;
  static bool judge_updown;

  float R = 287.04; //大気の気体定数J/(kg K)
  float g = 9.80665;

  //上昇中に使用、最終的に最高点を保存する
  float pre_altitude_;

  public:
    pres();
    ~pres();
    static void dummy_set_ground_value(float p, float T, float h);
    static float get_ground_value();
    void set_ground_value();
    void set_pres();
    //現在の圧力保存、メインでは使わない
    uint32_t BME280_compensate_P_int32(int32_t adc_P);
    //圧力補正、メインでは使わない
    int32_t BME280_compensate_T_int32(int32_t adc_T);
    //温度補正、メインでは使わない
    void set_altitude_();
    //現在の圧力保存、高度を保存、メインでは使わない
    static void set_judge_updown();
    //judge_alt_to_ground内部で利用
    static bool get_judge_updown();
    //judge_alt_to_ground内部で利用

    
    float get_pres(); 
    //現在の圧力を保存、獲得、単位はhPa
    float get_altitude_(); 
    //現在の圧力、高度を保存、獲得単位はm


    //以下メインで利用judge_altitude_()内部でpreの値をいじっていないことを確認
    void set_pre_altitude_();
    //上昇中に使用、現在の圧力、高度を保存、現在の高度を5回平均
    bool judge_altitude_up();
    //現在の圧力保存、高度を保存、preと比較
    bool judge_altitude_down();
    
    bool judge_alt_to_ground();
    //下降中に利用
};


#endif
