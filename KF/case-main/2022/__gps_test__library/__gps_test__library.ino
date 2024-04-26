#include <TinyGPS++.h>

#include <SoftwareSerial.h>
 
TinyGPSPlus gps;
SoftwareSerial mySerial(10,11); // SoftwareSerialを使う場合必要
//TinyGPSCustom magneticVariation(gps, "GPRMC", 10);
 
void setup() {
 // Open serial communications and wait for port to open:
 Serial.begin(19200); //いくつでもおけ
 while (!Serial) {
 ; // wait for serial port to connect. Needed for native USB port only
 }
 Serial.println("Goodnight moon!"); //10,11ピン使うとこっちの挨拶


 
 // set the data rate for the SoftwareSerial port
 mySerial.begin(9600); //多分9600以下
 mySerial.println("Hello, world?"); //0,1ピン使うとこっちの挨拶
}
 
void loop() { // 先輩もコピペしてる
 while (mySerial.available() > 0){
 char c = mySerial.read();
 //Serial.print(c);
 gps.encode(c);
 if (gps.location.isUpdated()){
 Serial.print("LAT="); Serial.println(gps.location.lat(), 6);
 Serial.print("LONG="); Serial.println(gps.location.lng(), 6);
 Serial.print("ALT="); Serial.println(gps.altitude.meters());
 }
 }
}
