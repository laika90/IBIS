#include <class_light3.h>
#define cds A0
#include <EEPROM.h>
#define syoki 255
#define kaigyou 10

int light::sample_number = 0;
//暗い時の値（高い）
float light::average_dim = 0;
//明るい時の値（低い）、今使ってないけど、今後閾値を自動設定するコード書くのに使いたい
float light::average_bright = 0;
float light::value[40]= 
{0,0,0,0,0,
0,0,0,0,0,
0,0,0,0,0,
0,0,0,0,0,
0,0,0,0,0,
0,0,0,0,0,
0,0,0,0,0,
0,0,0,0,0};
 
light::light()
{
  Serial.println("light start");
  pinMode(cds, INPUT);
}

light::~light()
{
  Serial.println("class_light destoroyed!!");
}

//平均値最初一個からスタートしたら安定しなさそうだから、１０個くらいの平均とっとく
void light::init_average_dim()
{
  average_dim = analogRead(cds);
  sample_number++;
  value[0] = average_dim;

  for (int i = 1; i < 40; i++)
  {
    float light_value = analogRead(cds);
    value[i] = light_value;
    average_dim += (light_value - average_dim) / (float)i;
    sample_number++;
    delay(50);
  }
  Serial.println("first value");
  Serial.println(average_dim);
}

void light::update_average_dim(int light_value)
{
  average_dim = (40.0 * average_dim - value[sample_number % 40] + (float)light_value) / 40.0;
  value[sample_number % 40] = light_value;
  Serial.print("average_dim");
  Serial.println(average_dim);
  sample_number++;
}

//平均を変えないジャッジ関数、間サットを缶に入れる時とか役立つかも
bool light::judge_stay()
{
  int light_value = 0;
  for ( int i = 0; i < 5; i++) {
    light_value += analogRead(cds);
    delay(50);
  }
  
  light_value = light_value / 5;
  Serial.print("new value");
  Serial.println(light_value);
  
  if (average_dim - light_value  > threshold) {
    Serial.println("staying");
    return true;
  }
  else {
    return false;
  }
}
 

bool light::judge_light1() { //判断早く、一個の値で判断
  int light_value = 0;
  light_value = analogRead(cds);
  Serial.print("new value");
  Serial.println(light_value);
  if (average_dim - light_value > threshold) {
    Serial.println("light1 reated");
    return true;
  }
  else {
    update_average_dim(light_value);
    return false;
  }
}

bool light::judge_light2() { //判断遅いが正確、５個の平均とる
  int light_value = 0;
  for ( int i = 0; i < 5; i++) {
    light_value += analogRead(cds);
    delay(50);
  }
  
  light_value = light_value / 5;
  Serial.print("new value");
  Serial.println(light_value);
  
 //光センサ反応したらeeprom保存
  if (average_dim - light_value > threshold) {
    int address = 0;
    char value[4];
    Serial.println("light2 reated");
    EEPROM.put(address, "DetectLight");
    address = address + sizeof("DetectLight") - 1;

    EEPROM.put(address, kaigyou);
    address += 1;

    EEPROM.put(address, "AverageValue");
    address= address + sizeof("AverageValue") - 1;

    EEPROM.put(address, kaigyou);
    address += 1;
  
    // EEPROM.put(address, sprintf(value, average_dim));
    // address = address +sizeof(sprintf(value, average_dim))-1;

    // EEPROM.put(address, kaigyou);
    // address += 1;

    EEPROM.put(address, "DtectedValue");
    address = address + sizeof( "DtectedValue") - 1;

    EEPROM.put(address, kaigyou);
    address += 1;
    
    EEPROM.put(address, "DriveMotor");
    address = address + sizeof("DriveMotor") - 1;
    return true;
  }
 
  else {
    for (int i = 0; i < 5; i++)
    {
    update_average_dim(light_value);
    }
  }
  return false;
}