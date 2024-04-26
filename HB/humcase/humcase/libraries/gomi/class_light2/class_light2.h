#ifndef _CLASS_LIGHT2_H_
#define _CLASS_LIGHT2_H_
#include <arduino.h>
#define cds A0

class light
{
static int sample_number;
  static int average_bright;
  static int average_dim;
  const int threshold = 300;
  
  public:
  light();
  ~light();
  //平均計算
  static void update_average_dim(int light_value);
  //平均取得
  static int get_average_dim();
  //初期値保存、最初だけ使用
  static void init_average_dim();
  //平均変えないジャッジ関数（待機中に利用）
  bool judge_stay();
  //展開判断(早い）
  bool judge_light1();
  //展開判断（遅い）
  bool judge_light2();
};
#endif
