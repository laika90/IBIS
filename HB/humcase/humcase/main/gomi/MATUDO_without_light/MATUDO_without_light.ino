#include <class_light.h>
#include <class_pres3.h>
#include <EEPROM.h>

#define motor1 2
#define motor2 3
#define motor3 4

#define deploy_open_time_ms = 5000;
#define open_separate_time_ms = 5000;
#define open_motor_time_ms = 2000;
#define deploy_motor_time_ms = 1500;
#define separate_motor_time_ms = 1500;

void setup_motor() {
  pinMode(motor3, OUTPUT);
  pinMode(motor2, OUTPUT);
  pinMode(motor1, OUTPUT);
}

void run_motor(unsigned long t, int motor_num) {
  digitalWrite(motor_num, HIGH);
  delay(t);
  digitalWrite(motor_num, LOW);
}



void main_rising_and_falling()
{
  /*
     上昇及び落下中に気圧せんさの値をとって、必要に応じて展開
  */
  pres start_p;
  int adress = 0;
  start_p.set_ground_value();
  Serial.println(start_p.get_alt());
  digitalWrite(LED_BUILTIN, HIGH);


  while (true) //目標高度到達で展開
  {
      float alt = start_p.get_alt();
      EEPROM.put(adress, alt);
      Serial.print("write eeprom: ");
      Serial.println(alt);
      if (adress + sizeof(alt) >= 512)
      {
        adress = 0;
      }
      else{
        adress += sizeof(alt);
      }

    if (start_p.judge_alt_to_ground())
    {
      break;
    }

    ////落下検知で展開
    // if (start_p.judge_alt_down());
    // {
    //   break;
    // }
  }

  run_motor(open_motor_time_ms, motor1); //開傘、展開
  delay(deploy_open_time_ms);
  run_motor(deploy_motor_time_ms, motor2);
  delay(open_separate_time_ms);
  run_motor(separate_motor_time_ms, motor3); //分離
  EEPROM.put(0,111.111);
  
}

void setup()
{
  setup_motor();
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  int adress = 0;
  Serial.println("reading data...");

  while (true)
  {
    float a;
    float data = EEPROM.get(adress, a);
    Serial.println(data);
    adress += sizeof(data);
    if (adress > 508)
    {
      break;
    }
  }
  
  for (int i=0; i < 512; i++)
  {
    EEPROM.put(i, 0);
  }
  Serial.println("finish reading");
}




void loop()
{
  main_rising_and_falling();
  while (true)
  {

  }
}