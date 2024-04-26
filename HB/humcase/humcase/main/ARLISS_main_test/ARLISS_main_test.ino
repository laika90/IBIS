#include <class_pres_ARLISS_test.h>
#include <EEPROM.h>

#define motor1 2
#define motor2 3
#define motor3 4

#define open_deploy_time_ms 5000
#define deploy_separate_time_ms 3700

#define motor_open_time_ms 2000
#define motor_deploy_time_ms 1500
#define motor_separate_time_ms 1500

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
  int address = 0;
  start_p.set_ground_value();
  Serial.println(start_p.get_alt());
  digitalWrite(LED_BUILTIN, HIGH);
  
  while (true) //目標高度到達でbreak
  {
      float alt = start_p.get_alt();
      EEPROM.put(address, alt);
      Serial.print("write eeprom: ");
      Serial.println(alt);
      
      if (address + sizeof(alt) >= 512)
      {
        address = 0;
      }
      else{
        address += sizeof(alt);
      }

    if (start_p.judge_alt_to_ground())
    {
      break;
    }
  }

  run_motor(motor_open_time_ms, motor1); //開傘
  delay(open_deploy_time_ms);
  
  run_motor(motor_deploy_time_ms, motor2); //展開
  delay(deploy_separate_time_ms);
  
  run_motor(motor_separate_time_ms, motor3); //分離
  EEPROM.put(0,111.111);
  EEPROM.put(sizeof(111.111), start_p.get_alt());
}

void setup()
{
  setup_motor();
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  
  int address = 0;
  Serial.println("reading data...");
  delay(5000);
  
  float type_float; //EEPROMの型指定に利用
  float is_drive_motor = EEPROM.get(0, type_float);
  if (is_drive_motor == 111.111)
  {
    Serial.println("detection successes");
    Serial.print("drived motor:");
    float final_value = EEPROM.get(sizeof(111.111), type_float);
    Serial.print(final_value);
    Serial.println("m");
  }
  else
  {
    Serial.println("detect failed");
  }
  delay(20000);
  
  while (true)
  {
    float type_float;
    float data = EEPROM.get(address, type_float);
    Serial.println(data);
    address += sizeof(data);
    if (address > 512 - sizeof(data))
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
  { }
}
