#ifndef eeprom_utility_h
#define eeprom_utility_h
#include <EEPROM.h>
#include "Arduino.h"

void SET_MENU();
bool CHECK(int val_low, int val_high, byte dist_array);
bool SET_ADD(int dist_array, byte msg);
bool SET_VAL(int dist_array, byte msg, bool limit);
void WRITE_VAL(int ads_low, int ads_high, long val);
void WRITE_VAL_ALL(int val);
byte SERIAL_VAL();
void PRINT_SPACE(byte times);
void PRINT_CD();
void PRINT_CURSOR(byte msg);
void PRINT_MENU();
void PRINT_ERROR(byte types);
void LIST(int s_pos, int e_pos);
void SHOW_LIST(int s_val, int e_val, bool pattern);
void DISP_ROMSIZE();
void eeprom_utility_setup();
void eeprom_utility_main();

#endif
