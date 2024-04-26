#define cds A0
#include <EEPROM.h>
class threshold
/*
 * メンバー変数と引数が名前被りがちなのでメンバー変数使う時はthisをつけた
 */
{
int n_bright = 0; //明るい時のサンプル数
int n_dim = 0; //暗い時のサンプル数
float mu_bright = 0; //明るい時の平均
float sigma_bright = 0; //明るい時の標準偏差
float mu_dim = 0; //暗い時の平均
float sigma_dim = 0; //暗い時の標準偏差
int sleep_time_s = 120; //ケースにしまうまでの時間

public:
void update_bright_val(int x); //明るい時の平均と標準偏差、サンプル数を更新
void update_dim_val(int x); //暗い時の平均と標準偏差、サンプル数を更新
float Gaussian(float x, float mu, float sigma);
float get_1val_top(float mu, float sigma, int n);//下側の片側優位水準1パーセント点を取得
float get_1val_bottom(float mu, float sigma, int n);//上側の片側優位水準1パーセント点を取得
float get_bright_val(float mu_bright, float sigma_bright, int n_bright ); //明るい時の1パーセント点取得
float get_dim_val(float mu_dim, float sigma_dim, int n_dim);//暗い時の1パーセント点取得
float get_threshold1(float mu_bright, float sigma_bright, int n_bright, float mu_dim, float sigma_dim, int n_dim);//それぞれの1パーセント点の平均をとって閾値を得る
float get_threshold2(float mu_bright, float sigma_bright, float mu_dim, float sigma_dim); //二分探索である値が明るい時に出る確率と暗い時に出る確率の大小が入れ替わる点を閾値に
void blink_LED(int time_s);
float determine_threshold(); //光センサの値を読み取って閾値を生成
};

void threshold::update_bright_val(int x)
/*明るい時、光センサの値xから平均と標準偏差、サンプル数を更新
 */
{
  float pre_mu_bright = this->mu_bright;
  this->mu_bright = (this->n_bright * this->mu_bright + (float)x) / (this->n_bright + 1);
  this->sigma_bright = sqrt((this->n_bright * (pow(this->sigma_bright,2) +pow(pre_mu_bright, 2)) + (float)pow(x,2)) / (this->n_bright+1) - pow(this->mu_bright, 2));
  this->n_bright++;
}


void threshold::update_dim_val(int x)
/*暗い時、光センサの値xから平均と標準偏差、サンプル数を更新
 */
{
  float pre_mu_dim = this->mu_dim;
  this->mu_dim = (this->n_dim*this->mu_dim + (float)x) / (this->n_dim+1);
  this->sigma_dim = sqrt((this->n_dim*(pow(this->sigma_dim, 2) + pow(pre_mu_dim, 2)) + (float)pow(x,2)) / (this->n_dim+1) - pow(this->mu_dim, 2) );
  this->n_dim++;
}


float threshold::Gaussian(float x, float mu, float sigma)
/*
 * 正規分布を計算
 */
{
  return exp(-pow((x-mu), 2) / pow(2*mu,2)) / sqrt(2*PI*pow(sigma,2));
}


float threshold::get_1val_top(float mu, float sigma, int n)
/*
 * 上側の片側優位水準1パーセント点を取得
 * 自由度は十分大きと仮定し、正規分布に近似できるとする
 */
{
  return mu + 2.33 * sigma / sqrt(n);
}


float threshold::get_1val_bottom(float mu, float sigma, int n)
/*
 * 下側の片側優位水準1パーセント点を取得
 */
{
  return mu - 2.33 * sigma / sqrt(n); 
}


float threshold::get_bright_val(float mu_bright, float sigma_bright, int n_bright )
/*
 * 明るい時の1パーセント点取得
 * 明るい時は値が小さくなるので上側の0.01パーセント点を用いる
 */
{
  return get_1val_top(mu_bright, sigma_bright, n_bright);
}


float threshold::get_dim_val(float mu_dim, float sigma_dim, int n_dim)
/*
 * 暗い時の0.01パーセント点取得
 * 暗い時は値が大きくなるので下側の0.01パーセント点を用いる
 */
{
  return get_1val_bottom(mu_dim, sigma_dim, n_dim);
}


float threshold::get_threshold1(float mu_bright, float sigma_bright, int n_bright, float mu_dim, float sigma_dim, int n_dim)
/*
 * それぞれの1パーセント点の平均をとって閾値を得る
 */
{
  return 0.6 * get_bright_val(mu_bright, sigma_bright, n_bright) + 0.4 * get_dim_val(mu_dim, sigma_dim, n_dim); //4:6内分点をとって明るい側に閾値を寄せる（変更する可能性あり
}


float threshold::get_threshold2(float mu_bright, float sigma_bright, float mu_dim, float sigma_dim)
/*
 * ある値が明るい時に出る確率と暗い時に出る確率の大小が入れ替わる点を閾値に
 * 2分探索でGaussianが等しくなる点を探す
 */
{
  float threshold; //閾値
  float dif; //判定に利用
  float high = mu_dim; //暗い時の方が値が大きい
  float low = mu_bright; //明るい時の方が値が小さい
  float mid;
  
  while(true)
  /*
   * Gaussianの差が0.0001より小さくなったらbreak
   * mu_dimとmu_brightの間のGaussianの差の関数系は単調増加なので2分探索で問題ない
   */
  {
    mid = high + low; //真ん中の点を取得
    dif = Gaussian(mid, mu_dim, sigma_dim) - Gaussian(mid, mu_bright, sigma_bright); //真ん中の点における暗い時と明るい時のGaussianの差
    if (abs(dif) < 0.0001)
    {
      break;
    }
    else if (dif > 0)
    {
      high = mid;
    }
    else
    {
      low = mid;
    }
  }
  threshold = mid;
  return threshold;
}


void threshold::blink_LED(int time_s)
{
 for (int i=0; i < time_s; i++)
  { 
    digitalWrite(LED_BUILTIN, HIGH);
    delay(500); 
    digitalWrite(LED_BUILTIN, LOW); 
    delay(500); 
    Serial.println("sleeping");
    Serial.print(i);
    Serial.println("秒");
    Serial.println("あと");
    Serial.print(time_s - i);
    Serial.println("秒");
  }
}

float threshold::determine_threshold()
/*
 * 閾値を光センサの値を読み取って決める
 */
{
  Serial.println("明るい状態にしてください");
  delay(10000);
  int x;
  for (int i; i < 1000; i++)
  /*
   * 50秒間そのまま（Lチカするまで）
   */
  {
    x = analogRead(cds); //光センサの値取得
    update_bright_val(x); //平均と分散を逐次計算
    delay(50);
  }
  Serial.print(sleep_time_s);
  Serial.println("2分間のうちにケースにしまってください");
  blink_LED(sleep_time_s);
  for (int i; i < 1000; i++)
  /*
   * 50秒間そのまま
   */
  {
    x = analogRead(cds); //光センサの値取得
    update_dim_val(x); //平均と分散を逐次計算
    delay(50);
  }
  
  float threshold = get_threshold1(mu_bright, sigma_bright, n_bright, mu_dim, sigma_dim, n_dim);
//  float threshold = get_threshold2(mu_bright, sigma_bright, n_bright, mu_dim, sigma_dim, n_dim); //どっちのコードがいいか比較したい
  return threshold;
}


void setup() {
  Serial.begin(9600);
  Serial.print("threshold");
  int a;
  Serial.print(EEPROM.get(0,a));
}

void loop() {
  threshold my_threshold;
  float threshold = my_threshold.determine_threshold();
  EEPROM.put(0,threshold);
  delay(1000000);
}
