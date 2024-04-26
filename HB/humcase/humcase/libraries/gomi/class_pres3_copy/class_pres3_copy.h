#ifndef _CLASS_PRES_H
#define _CLASS_PRES_H
#include <arduino.h>
#include <Wire.h>

#define BME280_ADDR 0x76
#define CONFIG 0xF5
#define CTRL_MEAS 0xF4
#define CTRL_HUM 0xF2

class pres
/*
set関数は気圧せんさの値をとって値を保存
get関数はクラスの中の値をそのまま返す
judge関数は内部にset関数を持っている
*/
{
  //以下自分で設定する余裕
  //落下するまではset_pre_alt -> judge_alt
  const float minnimam_height = 17; //m
  const float marge1 = 0.5; //m、上昇判定の余裕
  const float marge2 = 0.5; //m、落下判定のための余裕
  const float marge = 0.6; //m、地面基準高度判定のための余裕
  const int check_times = 1; //追加でチェックする回数
  const float eeprom_height = 19;
  //以上自分で設定する定数

  //以下補正用変数
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
  //以上補正よう変数

  //以下実際の値
  float temp;
  //℃
  float pressure;
  //hPa
  float alt;
  //m
  //以上実際の値

  //以下地上での値

  static float ground_pres;
  static float ground_alt;
  static float ground_T;
  //以上地上での値

  //以下上昇判定に利用
  static bool judge_updown; //上昇中に使用、最終的に最高点を保存する
  float pre_alt;
  //以上上昇判定に利用

  //以下定数
  const float R = 287.04; //大気の気体定数J/(kg K)
  const float g = 9.80665;
  //以上定数

  //LPF用変数
  const float filter = 0.3;
  float last_alt = 0;

  bool is_eeprom_height = false;

  public:
    pres();
    ~pres();
    void print_alt();

    //以下セット関数
    void set_value1();  //一回の値
    void set_value();  //五回平均
    static void dummy_set_ground_value(float p, float T, float h);
    void set_ground_value();
    static void set_judge_updown();
    static void set_judge_updown2();
    void set_pre_alt();


    //以下補正よう関数
    uint32_t BME280_compensate_P_int32(int32_t adc_P); //圧力補正
    int32_t BME280_compensate_T_int32(int32_t adc_T); //温度補正
    
    //以下ゲット関数
    static float get_ground_value();
    float get_pres(); //現在の圧力を獲得、単位はhPa
    float get_alt(); //現在の圧力、高度を獲得、単位はm

    //以下ジャッジ関数、内部でset関数実装
    bool judge_alt_up();
    bool judge_alt_down();
    bool judge_alt_to_ground();
    bool judge_start_eeprom();
};


#endif