#include <class_light.h>
#define cds A0
#include <EEPROM.h>


light::light()
{
  Serial.println("light start");
  pinMode(cds, INPUT);
  EEPROM.put(0,analogRead(cds));
  EEPROM.put(4,analogRead(cds));
}

bool light::judge_light1() { //判断早く
  int l = 0;
  l = analogRead(cds);
  Serial.println(l);
  if (l < threshold) {
    EEPROM.put(8,l);
    return true;
  }
  else {
    return false;
  }
}

bool light::judge_light2() { //判断遅いが正確
  int l = 0;
  for (int i = 0; i < 5; i++) {
    l += analogRead(cds);
    delay(10);
  }
  l = l / 5;
  Serial.println(l);
  if (l < threshold) {
    EEPROM.put(12,l);
    return true;
  }
  else {
    return false;
  }
}
