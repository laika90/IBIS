#include <SoftwareSerial.h>
#include <stdlib.h>

#define RECV_SIZE 30
#define ES920LR_RST_PIN 13
#define LORA_RX 2
#define LORA_TX 3

String dstId = "00010001";  /*送信相手の番号*/
const int maxSendTimes = 10; /*最大送信回数*/
const int setCmdDelay = 100; /*待機時間*/

SoftwareSerial LoRa_Serial(LORA_RX, LORA_TX);

void setup() {
  pinMode(ES920LR_RST_PIN, OUTPUT);
  // LoRaを再起動させる
  digitalWrite(ES920LR_RST_PIN, LOW);
  delay(100);
  digitalWrite(ES920LR_RST_PIN, HIGH); 
  delay(1500);

  Serial.begin(9600);
  LoRa_Serial.begin(9600);
  delay(3500);
  loraInit();
  Serial.println("Start Recv");
}


void loop() {
  char RecvData[RECV_SIZE] = "";
  unsigned char n = 0;

  while (LoRa_Serial.available() > 0) {
    // バッファから一文字取り出す
    RecvData[n] = LoRa_Serial.read();

    // 改行文字が来たらNULL文字にする
    if (RecvData[n] == '\r' || RecvData[n] == '\n') {
      RecvData[n] = '\0';
      clearBuffer();
      Serial.println(RecvData);
      break;
    }
    
    if (n < RECV_SIZE) {
      n++;
    } else {
      n = 0;
    }
  }
  delay(300);
}


void loraInit() {
  Serial.print("Start...");
  // コマンドモード開始
  LoRa_Serial.println("2"); clearBuffer();
  // bw（帯域幅の設定）
  LoRa_Serial.println("bw 4"); clearBuffer();
  // sf（拡散率の設定）
  LoRa_Serial.println("sf 12"); clearBuffer();
  LoRa_Serial.println("channel 1"); clearBuffer();
  // 自分が参加するPANネットワークアドレスの設定
  LoRa_Serial.println("panid 0001"); clearBuffer();
  // 自分のノードIDを設定
  LoRa_Serial.println("ownid 0002"); clearBuffer();
  // ack受信の設定
  LoRa_Serial.println("ack 2"); clearBuffer();
  //送信元のID付与設定
  LoRa_Serial.println("o 2"); clearBuffer();
  // RRSIの付与設定
  LoRa_Serial.println("p 2"); clearBuffer();
  // 送信モードを設定
  LoRa_Serial.println("n 2"); clearBuffer();
  // 設定を保存する
  LoRa_Serial.println("w"); clearBuffer();
  // 通信の開始
  LoRa_Serial.println("z"); clearBuffer();
  Serial.println("Set up OK!");
}
void clearBuffer() {
  delay(setCmdDelay);
  while (LoRa_Serial.available() > 0) LoRa_Serial.read();
}
