# ATI Mini40 data bank
# Author: Tony Blake
# Date: March 2021
# Notes:
#
# Script for supplying Mini40 data on demand. The setup used used the controller box from ATI.

def ati_mini40_data_bank(ser):
    
   lineATI=ser.readline() #reading serial port   
      
   dec=lineATI.decode()
      
   sp=dec.split(',')
    
   if (len(sp) == 7):
      fx = int(sp[1])/200;
      fy = int(sp[2])/200;
      fz = int(sp[3])/200;
      tx = int(sp[4])/8000;
      ty = int(sp[5])/8000;
      tz = int(sp[6])/8000;
              
   else:         
      fx = 'Nan';
      fy = 'Nan';
      fz = 'Nan';
      tx = 'Nan';
      ty = 'Nan';
      tz = 'Nan';                                              

   return [fx,fy,fz,tx,ty,tz]
                                