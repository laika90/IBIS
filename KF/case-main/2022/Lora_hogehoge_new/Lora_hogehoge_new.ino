//書き込みはRX,TXを抜いて行う！
#include <SoftwareSerial.h>


#define LoRa_switch 12
SoftwareSerial LoRa(8,9); //SoftwareSerialを使う場合必要

void setup()
{
  
   
   pinMode(LoRa_switch,OUTPUT);
   digitalWrite(LoRa_switch,LOW);
   //LoRa.begin(19200);  //SoftwareSerialを使う場合こっち
   Serial.begin(19200); //Serialを使う場合こっち
   delay(2000); //LoRa起動待ち
}

void loop() 
{
  int i;
  for(i = 0;i < 10;i++){
    
//    if(i%2 == 1){
//      digitalWrite(LoRa_switch,HIGH);
//    }
//    else{
//      digitalWrite(LoRa_switch,LOW);
//    }
//    delay(6000);
    
    //LoRa.print("hogehoge"); //SoftwareSerialを使う場合こっち
    //LoRa.println(i);
    Serial.print("hogehoge"); //Serialを使う場合こっち
    Serial.println(i);
    delay(15000);
  }
}
