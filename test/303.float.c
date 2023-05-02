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

/* The file begin.h is included if compiler flag -DBEGINCODE is used */
#ifdef BEGINCODE
#include "begin.h"
#endif
int compare_float(float f1, float f2)
{
  if (f1 == f2)
   {
    return 1;
   }
  else
   {
    return 0;
   }
}

int main() {
  float uc=1.0,ua=1.0, Two=2.0, Four=4.0;
  char t = 0;

  if(Four + Two * (-Two) == 0){
    t = 1;
  }
  /* t = 1 */ t = 0;

  if(compare_float(ua, 1.0001) == 0){
    t = 1;
  }
  /* t = 0 */ t = 0;

  if(compare_float(0.0, 0.0) == 1){
    t = 1;
  }
  /* t = 1 */ t = 0;

  if(compare_float(ua, 1.0) == 1){
    t = 1;
  }
  /* t = 1 */ t = 0;

  if(compare_float(ua, 1.0) == 1){
    t = 1;
  }
  /* t = 1 */ t = 0;

  return 0; 
  /* Return 0 */
}

/* The file end.h is included if compiler flag -DENDCODE is used */
#ifdef ENDCODE
#include "end.h"
#endif
