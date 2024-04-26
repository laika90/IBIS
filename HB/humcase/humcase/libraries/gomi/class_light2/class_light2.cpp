#include <class_light2.h>
#define cds A0
#include <EEPROM.h>
#define syoki 255
#define kaigyou 10

int light::sample_number = 0;
//暗い時の値（高い）
int light::average_dim = 0;
//明るい時の値（低い）、今使ってないけど、今後閾値を自動設定するコード書くのに使いたい
int light::average_bright = 0;

 
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
  sample_number = 1;
  for (int i = 0; i < 10; i++)
  {
    update_average_dim(analogRead(cds));
    delay(50);
  }
  Serial.println("first value");
  Serial.println(average_dim);
}

//平均値を更新
void light::update_average_dim(int light_value){
  average_dim = average_dim + (light_value - average_dim) / sample_number;
  sample_number++;
  Serial.print("average_dim");
  Serial.println(average_dim);
}

//平均を変えないジャッジ関数、間サットを缶に入れる時とか役立つかも
bool light::judge_stay()
{
  int l = 0;
  for ( int i = 0; i < 5; i++) {
    l += analogRead(cds);
    delay(50);
  }
  
  l = l / 5;
  Serial.print("new value");
  Serial.println(l);
  
  if (average_dim - l  > threshold) {
    Serial.println("staying");
    return true;
  }
  else {
    return false;
  }
}
 

bool light::judge_light1() { //判断早く、一個の値で判断
  int l = 0;
  l = analogRead(cds);
  Serial.print("new value");
  Serial.println(l);
  if (average_dim -l  > threshold) {
    Serial.println("light1 reated");
    return true;
  }
  else {
    update_average_dim(l);
    return false;
  }
}

bool light::judge_light2() { //判断遅いが正確、５個の平均とる
  int l = 0;
  for ( int i = 0; i < 5; i++) {
    l += analogRead(cds);
    delay(50);
  }
  
  l = l / 5;
  Serial.print("new value");
  Serial.println(l);
  
 //光センサ反応したらeeprom保存
  if (average_dim -l > threshold) {
    int address = 0;
    char value[4];
    Serial.println("light2 reated");
    EEPROM.put(address, "DetectLight");
    address = address + sizeof("DetectLight") -1;

    EEPROM.put(address, kaigyou);
    address += 1;

    EEPROM.put(address, "AverageValue");
    address= address + sizeof("AverageValue")-1;

    EEPROM.put(address, kaigyou);
    address += 1;
  
    // EEPROM.put(address, sprintf(value, average_dim));
    // address = address +sizeof(sprintf(value, average_dim))-1;

    // EEPROM.put(address, kaigyou);
    // address += 1;

    EEPROM.put(address, "DtectedValue");
    address = address + sizeof( "DtectedValue")-1;

    EEPROM.put(address, kaigyou);
    address += 1;
    
    EEPROM.put(address, "DriveMotor");
    address = address + sizeof("DriveMotor")-1;
    return true;
  }
 
  else {
    for (int i = 0; i< 5; i++)
    {
    update_average_dim(l);
    }
  }
  return false;
}
