#include "eeprom_utility.h"

#define BPS 74880

char cmd;
long input_val;
long tgt_val[4];
byte menu;
int  eep_size;
bool error;
#define RET_IS_CMD 1
#define RET_IS_VAL 2

#define M_HOME   0
#define M_LIST   1
#define M_LISTAL 2
#define M_VALUE  3
#define M_VALUES 4
#define M_VALALL 5

#define MENU_SIZE 6
#define M_TXT_NUM 17
char command_menu[MENU_SIZE + 1][M_TXT_NUM] {
  "HOME",
  "EEPROM List",
  "EEPROM List All",
  "Set a Value",
  "Set Values",
  "Set Vaule to All",
  "Back to menu"
};
const byte m_crn [MENU_SIZE + 1] = {12, 5, 1, 5, 6, 0, 4};

#define CUR_MODE   0
#define ASK_ADRS   1
#define ASK_VAL    2
#define ASK_S_ADRS 3
#define ASK_E_ADRS 4

char msg_parts[4][8] {
  /*0*/  "value",
  /*1*/  "command",
  /*2*/  "mode",
  /*3*/  "address"
};

char command_alp[MENU_SIZE + 1] = {'0', 'l', 'a', 'v', 's', 'r', 'z'};
char icons [5] = {' ', '>', '[', ']', ':'};
char pros[2][11] = {"processing", "done"};

void SET_MENU() {
  menu = M_HOME;
  Serial.println();
  PRINT_MENU();
  PRINT_CD();
  PRINT_CURSOR(CUR_MODE);
}

bool CHECK(int val_low, int val_high, byte dist_array) {
  if (tgt_val[dist_array] >= val_low && tgt_val[dist_array] <= val_high && !error)
  {
    menu++;
    Serial.println();
    return true;
  } else {
    if (!error) PRINT_ERROR(0);
  }
  return false;
}

bool SET_ADD(int dist_array, byte msg) {
  if (CHECK (0, eep_size - 1, dist_array))
  {
    if (dist_array == 2)
    {
      if (tgt_val[1] > tgt_val[2])
      {
        int temp = tgt_val[1];
        tgt_val[1] = tgt_val[2];
        tgt_val[2] = temp;
      }
    }
    return true;
  } else {
    PRINT_CURSOR(msg);
    return false;
  }
}

bool SET_VAL(int dist_array, byte msg, bool limit) {
  if (CHECK (0, 255, dist_array))
  {
    return true;
  } else {
    PRINT_CURSOR(msg);
    return false;
  }
}

void WRITE_VAL(int ads_low, int ads_high, long val) {
  int times = ads_high - ads_low;

  Serial.println();
  Serial.print("address :");
  Serial.print(ads_low);
  if (times > 1)
  {
    Serial.print("-");
    Serial.print(ads_high);
  }
  Serial.println();
  Serial.print("value   :");
  Serial.print(val);
  Serial.println();
  delay(1500);
  
  for (int i = ads_low ; i <= ads_high ; i++)
  {
    for (byte ii = 0 ; ii < 2 ; ii++)
    {
      LIST(i, i);
      Serial.print(" - ");
      delay(30);
      Serial.println(pros[ii]);
      if (ii == 0) EEPROM[i] = val;
    }
  }
  delay(1000);
  SET_MENU();
}

void WRITE_VAL_ALL(int val) {
  Serial.print("-write ");
  Serial.print(val);
  Serial.print(" to all address");
  Serial.print("    ");
  delay(500);
  Serial.print(pros[0]);
  for (int i = 0 ; i < eep_size ; i++)
  {
    EEPROM[i] = val;
    if ((i % (eep_size / 3)) == 0)
    {
      Serial.print(".");
      delay(50);
    }
  }
  Serial.println(pros[1]);
  delay(1000);
  Serial.println();
  LIST(0, eep_size);
  Serial.println();
  Serial.println();
  delay(1000);
  SET_MENU();
}

byte SERIAL_VAL() {

  if (Serial.available() > 0)
  {
    delay(20);

    byte data_size = Serial.available();
    byte buf[data_size], degree = 1;
    long recv_data = 0, dub = 1;
    bool minus = 0;

    for (byte i = 0 ; i < data_size ; i++)
    {
      buf[i] = Serial.read();
      if (buf[i] >= '0' && buf[i] <= '9') buf[i] -= '0';
      else {
        if (buf[0] == '-') minus = 1;
        else {
          cmd = buf[i];
          degree = 0;
        }
      }
    }
    if (degree == 1) degree = data_size - minus;

    for (byte i = 0 ; i < degree ; i++)
    {
      recv_data += buf[(data_size - 1) - i] * dub;
      dub *= 10;
    }
    if (minus) recv_data *= -1;

    if (degree != 0)
    {
      input_val = recv_data;
      return RET_IS_VAL;
    } else {
      return RET_IS_CMD;
    }
  }
  return 0;
}

void PRINT_SPACE(byte times) {
  for (byte spc = 0 ; spc < times ; spc++) Serial.print(icons[0]);
}

void PRINT_CD() {
  Serial.print(msg_parts[2]);
  for (byte i = 0 ; i < 2 ; i++) Serial.print(icons[4]);
  Serial.print(command_menu[menu / 10]);
  Serial.println();
  delay(500);
}

void PRINT_CURSOR(byte msg) {

  if (msg == CUR_MODE) Serial.print("select command");
  if (msg == ASK_VAL)
  {
    Serial.print("set value");
    Serial.print(" (0-255) ");
  }
  else if (msg >= ASK_ADRS)
  {
    if (msg == ASK_ADRS)  Serial.print("set address");
    if (msg == ASK_S_ADRS) Serial.print("set start address");
    if (msg == ASK_E_ADRS) Serial.print("set end address");
    Serial.print(" (0-");
    Serial.print(eep_size - 1);
    Serial.print(")");
  }

  PRINT_SPACE(1);
  for (byte i = 1 ; i <= 2 ; i++) Serial.print(icons[i % 2]);
}

void PRINT_MENU() {
  Serial.println();
  for (byte i = 1 ; i <= MENU_SIZE ; i++)
  {
    Serial.print(icons[2]);
    Serial.print(command_alp[i]);
    Serial.print(icons[3]);
    Serial.print(command_menu[i]);
    PRINT_SPACE(m_crn[i]);
    if (i == 3) Serial.println();
    else PRINT_SPACE(3);
  }
  Serial.println();
}

void PRINT_ERROR(byte types) {
  Serial.print(" - Invalid ");
  Serial.print(msg_parts[types]);
  Serial.print(" !");
  Serial.println();
  delay(700);
}

void LIST(int s_pos, int e_pos) {

  for (int i = s_pos ; i <= e_pos ; i++)
  {
    byte val = EEPROM[i];

    Serial.print(icons[2]);

    // fill by 0
    for (byte zro = 1; zro < 4; zro++) if (i < pow(10, zro)) Serial.print("0");

    Serial.print(i);          // address number
    Serial.print(icons[3]);

    // fill by 0
    for (byte zro = 1; zro < 3; zro++) if (val < pow(10, zro)) Serial.print("0");

    Serial.print(val);  // value

    if (((i - s_pos  + 1) % 10) == 0) Serial.println();
    else PRINT_SPACE(2);
  }
}

void SHOW_LIST(int s_val, int e_val, bool pattern) {
  Serial.println();
  if (pattern)
  {
    Serial.print("-List from ");
    Serial.print(tgt_val[1]);
    Serial.print(" to ");
    Serial.println(tgt_val[2]);
    delay(700);
  }
  LIST(s_val, e_val);
  Serial.println();
  delay(1000);
  SET_MENU();
}

void DISP_ROMSIZE() {
  Serial.print("EEPROM size:");
  Serial.println(eep_size);
  delay(1000);
}

void eeprom_utility_setup(){
  Serial.print("<< EEPROM utility  ARLISS 2022 version  >>");
  PRINT_SPACE(1);
  Serial.print("by Kai Nakamura featuring jumbleat.com");
  PRINT_SPACE(3);
  Serial.println("2022.07.07");

  Serial.println();
  eep_size = EEPROM.length();
  DISP_ROMSIZE();
  SET_MENU();
}

void eeprom_utility_main(){
  byte ret = SERIAL_VAL();

  if (ret > 0)
  {
    if (ret == RET_IS_VAL)
    {
      Serial.print(input_val);
      tgt_val[menu % 10] = input_val;
    } else if (ret == RET_IS_CMD) {
      Serial.print(cmd);
      if (cmd == command_alp[1]) menu = M_LIST * 10;
      else if (cmd == command_alp[2]) menu = M_LISTAL * 10;
      else if (cmd == command_alp[3]) menu = M_VALUE * 10;
      else if (cmd == command_alp[4]) menu = M_VALUES * 10;
      else if (cmd == command_alp[5]) menu = M_VALALL * 10;
      else if (cmd == command_alp[6]) menu = M_HOME;
      else
      {
        error = true;
        PRINT_ERROR(1);
      }
    }

    if (menu == M_HOME)
    {
      if (ret == RET_IS_VAL) PRINT_ERROR(0);
      SET_MENU();
    } else if (menu >= 10) {

      if ((menu % 10) == 0)
      {
        Serial.println();
        Serial.println();
        PRINT_CD();
      }
      input_val = 0;

      // set all values in EEPROM
      if (menu >= (M_VALALL * 10))
      {
        if (menu == (M_VALALL * 10))
        {
          PRINT_CURSOR(ASK_VAL);
          menu++;
        } else if (menu == ((M_VALALL * 10) + 1)) {
          if (SET_VAL (1, ASK_VAL, 1)) WRITE_VAL_ALL(tgt_val[1]);
        }

        // set values to pointed address
      } else if (menu >= (M_VALUES * 10)) {

        if (menu == (M_VALUES * 10))
        {
          PRINT_CURSOR(ASK_S_ADRS);
          menu++;
        } else if (menu == ((M_VALUES * 10) + 1)) {
          if (SET_ADD (1, ASK_S_ADRS)) PRINT_CURSOR(ASK_E_ADRS);
        } else if (menu == ((M_VALUES * 10) + 2)) {
          if (SET_ADD (2, ASK_E_ADRS))
          {
            Serial.println();
            LIST(tgt_val[1], tgt_val[2]);
            Serial.println();
            PRINT_CURSOR(ASK_VAL);
          }
        } else if (menu == ((M_VALUES * 10) + 3)) {
          if (SET_VAL (3, ASK_VAL, 1)) WRITE_VAL(tgt_val[1], tgt_val[2], tgt_val[3]);
        }

        // set value to single EEPROM address
      } else if (menu >= (M_VALUE * 10)) {

        if (menu == (M_VALUE * 10))
        {
          PRINT_CURSOR(ASK_ADRS);
          menu++;
        } else if (menu == ((M_VALUE * 10) + 1)) {
          if (SET_ADD (1, ASK_ADRS))
          {
            LIST(tgt_val[1], tgt_val[1]);
            PRINT_CURSOR(ASK_VAL);
          }
        } else if (menu == ((M_VALUE * 10) + 2)) {
          if (SET_VAL (2, ASK_VAL, 1)) WRITE_VAL(tgt_val[1], tgt_val[1], tgt_val[2]);
        }

        // display list of all EEPROM value
      } else if (menu >= (M_LISTAL * 10)) {

        SHOW_LIST(0, eep_size - 1, 0);

        // display list of pointed EEPROM address
      } else if (menu >= (M_LIST * 10)) {

        if (menu == (M_LIST * 10))
        {
          PRINT_CURSOR(ASK_S_ADRS);
          menu++;
        } else if (menu == ((M_LIST * 10) + 1)) {
          if (SET_ADD (1, ASK_S_ADRS)) PRINT_CURSOR(ASK_E_ADRS);
        } else if (menu == ((M_LIST * 10) + 2)) {
          if (SET_ADD (2, ASK_E_ADRS)) SHOW_LIST(tgt_val[1], tgt_val[2], 1);
        }
      }
    }
  }
  error = false;
}
