//書き込みはRX,TXピンを外して行う！
#include <TinyGPS++.h>
#include <SoftwareSerial.h>
#include <TinyGPSPlus.h>
 
TinyGPSPlus gps;
SoftwareSerial mySerial(10, 11); // gpsのRX, TX
//LoraはTX,RXピンに接続
//TinyGPSCustom magneticVariation(gps, "GPRMC", 10);
 
void setup() {
 // set the data rate for the SoftwareSerial port
 
 pinMode(12,OUTPUT);  
 digitalWrite(12,LOW);  //Loraを再起動
 
 mySerial.begin(9600); //gpsは多分9600以下
 mySerial.println("Hello, world?");  //絶対いらない

 Serial.begin(19200);
 
 /*
 //Serial.print("1\r\n");
 Serial.println("1");
 delay(30000);
 //Serial.print("z\r\n");
 Serial.println("z");
 delay(30000);
 */
}
 
void loop() { //先輩のコピペ。ライブラリ使うだけ。
  String strlat;
  String strlon;
  String stralt;
  if(mySerial.available() > 0){
    gps.encode(mySerial.read());
    if (gps.location.isUpdated()){
      strlat = gps.location.lat();
      strlon = gps.location.lng();
      stralt = gps.altitude.meters();
      Serial.println(strlat + "/"  + strlon + "/" + stralt);
      delay(30000);
    }
    /*
    else{
      Serial.println("gps not updated...");
      delay(30000);
    }
    */
    
    /*
    else{
      Serial.println("gps.location.isUpdated() == false !");
      delay(100);
    }
    */
  }
}
