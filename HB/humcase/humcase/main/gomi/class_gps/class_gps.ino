#include <SoftwareSerial.h>

SoftwareSerial mySerial(10, 11); //tx, rxを指定

 
class gps
{
    String latitude;
    String longitude;
    String time_jp; //日本時間

  public:
    gps();
    String NMEA_to_DMS(float val); //座標を度、分、秒に
    String time_to_jp(String time_utc); //utc時間を日本時間に
    String get_val(); //クラス内の値をそのまま返す
    void update_val(); //gpsをとって値を更新
    void print_val();
};

gps::gps()
/*
   セッティングgpsとuart通信を開始
*/
{
  mySerial.begin(9600);
}

String gps::NMEA_to_DMS(float val)
/*
   座標の値がNMEAなので座標を度、分、秒（DMS)に
*/
{
  int d = val / 100; //度を求める、少数は切り捨て
  int m = ((val / 100.0) - d) * 100.0; //分を求める
  float s = ((((val / 100.0) - d) * 100.0) - m) * 60; //秒を求める
  return String(d) + "度" + String(m) + "分" + String(s, 1) + "秒";
}

String gps::time_to_jp(String time_utc)
/*
   utc時間（イギリス）で帰ってくるで日本時間に
*/
{
  int hh = (time_utc.substring(0, 2).toInt()) + 9; //時だけ+9して分秒は変えない
  if (hh > 24) hh = hh - 24;

  return String(hh, DEC) + ":" + time_utc.substring(2, 4) + ":" + time_utc.substring(4, 6);
}

String gps::get_val()
/*
   クラス内の値を結合して返す
*/
{
  return "time" + time_jp + "latitude"  + latitude + "longitude" + longitude;
}


void gps::update_val()
/*
   gpsからの値でクラス内の変数を更新

*/
{
  String line = mySerial.readStringUntil('\n'); //gpsの値を取得

  // StringListを作る準備
  int i;
  int index = 0;
  int len = line.length();
  String str = "";

  // StringListの生成、初期化
  String list[30];
  for (i = 0; i < 30; i++) {
    list[i] = "";
  }

  // 「,」を区切り文字として文字列を配列にする
  for (i = 0; i < len; i++) {
    if (line[i] == ',') {
      list[index++] = str;
      str = "";
      continue;
    }
    str += line[i];
  }

  if (list[0] == "$GPGGA") // $GPGGAセンテンスのみ読み込む
  {
    if (list[6] != 0) //正常に取得できているか判定、できてたら値更新
    {
      time_jp = time_to_jp(list[1]);
      latitude = NMEA_to_DMS(list[2].toFloat());
      longitude = NMEA_to_DMS(list[4].toFloat());
    }
    else
    {
      time_jp = "不明";
      latitude = "不明";
      longitude = "不明";
      Serial.println("測位できませんでした");
    }
  }
  delay(1000);
}

void gps::print_val()
{
  Serial.println("time" + time_jp);
  Serial.println("latitude" + latitude);
  Serial.println("longitude" + longitude);
}

void setup()
{
  Serial.begin(9600);
}

void loop()
{
  gps mygps;
  mygps.update_val();
  Serial.println(mygps.get_val());
  
}
