
#define motor1_start_time 1
//ボタンを押してからモーター1が回り始めるまでの時間ms。
#define motor2_start_time 120000//ボタンを押してからモーター2が回り始めるまでの時間ms。
#define motor3_start_time 120000//ボタンを押してからモーター2が回り始めるまでの時間ms。
#define motor1_run_time 2000//モーター1が回り続ける時間ms。回したくなかったら0
#define motor2_run_time 0//モーター2が回り続ける時間ms。回したくなかったら0
#define motor3_run_time 0//モーター2が回り続ける時間ms。回したくなかったら0



#define motor1_pin 2//ピンの名前はいじらない
#define motor2_pin 3//ピンの名前はいじらない
#define motor3_pin 4//ピンの名前はいじらない


void setup() {
  pinMode(motor1_pin,OUTPUT);
  pinMode(motor2_pin,OUTPUT);
  pinMode(motor3_pin,OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  
  
}

void loop() {
  
  digitalWrite(motor1_pin,LOW);
  digitalWrite(motor2_pin,LOW);
  digitalWrite(motor3_pin,LOW);
  int motor1_flag=0;
  int motor2_flag=0;
  int motor3_flag=0;
  unsigned long TIME;
  
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  
  if(motor1_run_time==0){
    motor1_flag+=1;
    }
    
  if(motor2_run_time==0){
    motor2_flag+=1;
    }
    
  while(true){
    TIME = millis();
    if(motor1_flag == 0){
      if(TIME>motor1_start_time){
        digitalWrite(motor1_pin,HIGH);
        motor1_flag=1;
      }
    }
    
    else{
      if(TIME>motor1_start_time+motor1_run_time){
        digitalWrite(motor1_pin,LOW);
      }
    }
    
    if(motor2_flag==0){
      if(TIME>motor2_start_time){
        digitalWrite(motor2_pin,HIGH);
        motor2_flag=1;
      }
    }
    
    else{
      if(TIME>motor2_start_time+motor2_run_time){
        digitalWrite(motor2_pin,LOW);
      }
    }
    
    if(motor3_flag==0){
      if(TIME>motor3_start_time){
        digitalWrite(motor3_pin,HIGH);
        motor3_flag=1;
      }
    }
    
    else{
      if(TIME>motor3_start_time+motor3_run_time){
        digitalWrite(motor3_pin,LOW);
      }
    }
  }
}
