#ifndef _CLASS_LIGHT_H_
#define _CLASS_LIGHT_H_
#include <arduino.h>
#define cds A0

class light
{
  int threshold = 120;
  public:
  light();
  bool judge_light1();
  bool judge_light2();
};
#endif
