/**
 * @file      012.const.c
 * @author    The ArchC Team
 *            http://www.archc.org/
 *
 *            Computer Systems Laboratory (LSC)
 *            IC-UNICAMP
 *            http://www.lsc.ic.unicamp.br
 *
 * @version   1.0
 * @date      Mon, 19 Jun 2006 15:33:22 -0300
 * @brief     It is a simple main function that uses unsigned char and returns 0.
 *
 * @attention Copyright (C) 2002-2006 --- The ArchC Team
 * 
 * This program is free software; you can redistribute it and/or modify 
 * it under the terms of the GNU General Public License as published by 
 * the Free Software Foundation; either version 2 of the License, or 
 * (at your option) any later version. 
 * 
 * This program is distributed in the hope that it will be useful, 
 * but WITHOUT ANY WARRANTY; without even the implied warranty of 
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
 * GNU General Public License for more details. 
 * 
 * You should have received a copy of the GNU General Public License 
 * along with this program; if not, write to the Free Software 
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 */
// TESTES FLOAT-DOUBLE DOUBLE-FLOAT CONVERSION
#include <math.h>
#define LOG(x) (float)log((double)(x))

/* The file begin.h is included if compiler flag -DBEGINCODE is used */
#ifdef BEGINCODE
#include "begin.h"
#endif

int main() {
  float uc=1.0,ua=1.0, Two=2.0, Four=4.0;
  float t = 0;

  t = LOG(Two);
  t = LOG(Four);
  t = LOG(uc);
  t = LOG(Two + Four);
  t = LOG(Two + Four + ua);
  t = LOG(Two + Four + Two);
  t = LOG(Two + Four + Two + ua);
  t = LOG(Two * Four + ua);
  t = LOG(Two / Four + ua);
  t = LOG(Two + Four / (ua+ua));
  t = LOG(Two * -Four * -ua);
  t = LOG(Two * Two * Two);
  t = LOG(Two * Four * ua);
  t = LOG(Two / Four / Two);
  t = LOG(ua + ua + ua);
  t = LOG(ua * ua * ua);
  t = LOG(ua / Four + ua);
  t = LOG(ua / (Four + Two));


  return 0; 
  /* Return 0 */
}

/* The file end.h is included if compiler flag -DENDCODE is used */
#ifdef ENDCODE
#include "end.h"
#endif
