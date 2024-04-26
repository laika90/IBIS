#include <SoftwareSerial.h>

#define LoRa_switch 12
SoftwareSerial mySerial(8, 9); // RX, TX
 
void setup() {
 // Open serial communications and wait for port to open:
 pinMode(LoRa_switch,OUTPUT);
 digitalWrite(LoRa_switch,LOW);
 Serial.begin(19200);
 mySerial.begin(19200);
 
 
 
 // set the data rate for the SoftwareSerial port
 mySerial.begin(19200);
 mySerial.println("Hello, world?");
}
 
void loop() { // run over and over
 if (mySerial.available()) {
 Serial.write(mySerial.read());
 }
 if (Serial.available()) {
 mySerial.write(Serial.read());
 }
}
