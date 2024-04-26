#include <EEPROM.h>

void setup() {
  Serial.begin(9600);
  unsigned char ar[5];
  EEPROM.put(0x00,"abcd");
  Serial.println(sizeof("abcd"));
  EEPROM.get(0x00,ar);
  Serial.println((char*)ar);
}

void loop() {
}
