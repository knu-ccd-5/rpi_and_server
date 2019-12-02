# -*- coding: utf-8 -*-
'''
 * dustsensor.ino -> dustsensor.py
 * optimized by John Choe
 * 
 * 2019-11-16
 '''

'''
 Standalone Sketch to use with a Arduino Fio and a 
 Sharp Optical Dust Sensor GP2Y1010AU0F
 
 Blog: http://arduinodev.woofex.net/2012/12/01/standalone-sharp-dust-sensor/
 Code: https://github.com/Trefex/arduino-airquality/

 For Pin connections, please check the Blog or the github project page
 Authors: Cyrille Médard de Chardon (serialC), Christophe Trefois (Trefex)
 Changelog:
   2012-Dec-01: Cleaned up code
   2012-Dec-13: Converted mg/m3 to ug/m3 which seems to be the accepted standard

 This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License. 
 To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter 
 to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA. 
'''

'''
pi@raspberrypi:~ $ pinout
,--------------------------------.
| oooooooooooooooooooo J8     +====
| 1ooooooooooooooooooo        | USB
|                             +====
|      Pi Model 3B  V1.2         |
|      +----+                 +====
| |D|  |SoC |                 | USB
| |S|  |    |                 +====
| |I|  +----+                    |
|                   |C|     +======
|                   |S|     |   Net
| pwr        |HDMI| |I||A|  +======
`-| |--------|    |----|V|-------'

Revision           : a32082
SoC                : BCM2837
RAM                : 1024Mb
Storage            : MicroSD
USB ports          : 4 (excluding power)
Ethernet ports     : 1
Wi-fi              : True
Bluetooth          : True
Camera ports (CSI) : 1
Display ports (DSI): 1

J8:
   3V3  (1) (2)  5V    
 GPIO2  (3) (4)  5V    
 GPIO3  (5) (6)  GND   
 GPIO4  (7) (8)  GPIO14
   GND  (9) (10) GPIO15
GPIO17 (11) (12) GPIO18
GPIO27 (13) (14) GND   
GPIO22 (15) (16) GPIO23
   3V3 (17) (18) GPIO24
GPIO10 (19) (20) GND   
 GPIO9 (21) (22) GPIO25
GPIO11 (23) (24) GPIO8 
   GND (25) (26) GPIO7 
 GPIO0 (27) (28) GPIO1 
 GPIO5 (29) (30) GND   
 GPIO6 (31) (32) GPIO12
GPIO13 (33) (34) GND   
GPIO19 (35) (36) GPIO16
GPIO26 (37) (38) GPIO20
   GND (39) (40) GPIO21

For further information, please refer to https://pinout.xyz/
'''

'''
 * 핀 연결 정보 (아두이노 우노 R3 기준)
 * Vcc: 5V(매우 중요!!)
 * 측정 핀: Analog 0
 * LED : Digital 12
'''

import RPi.GPIO as GPIO
import spidev
import urllib.request
import json
import serial
import time
import socket
import threading

PORT = '/dev/ttyACM0' # default COM PORT of Aruino Uno
baudrate = 9600
measurePin = 0 # 측정 핀이 MCP3008에서 CH0
ledPower = 4 # led 전원공급 핀: GPIO 14
servoPin = 17 # 서보모터 연결 핀: GPIO 17

''' constants from .ino '''
# samplingTime = 280
# deltaTime = 40
# sleepTime = 9680
''' to python '''
samplingTime = 0.00028
deltaTime = 0.00004
sleepTime = 0.00968
#voMeasured = 0
dustFactor = 0 # Dust Factor. 매우 중요!!
#calcVoltage = 0


''' 서버 관련 변수들 '''
isFirst = True # 처음 서버에 연결하는가?
response = None # 서버 응답 값

dustDensityFromServer = 0 # 웹서버에서 가져온 미세먼지 값
mDustDensityFromServer = 0 # 웹서버에서 가져온 초미세먼지 값
dustConditionFromServer = 10000 # 웹서버에서 가져온 창문 열기 조건값 (미세먼지)
mdustConditionFromServer = 10000 # 웹서버에서 가져온 창문 열기 조건값 (초미세먼지)

windowIsOpen = True # 창문이 열려있는가?
requiredToClose = False # 창문을 닫을 필요가 있는가?
windowCommand = 0 # 창문 명령. 2 : 열기, 3: 닫기


''' 아날로그 input 세팅 '''
spi = spidev.SpiDev()
spi.open(0, 0)
#spi.max_speed_hz = 1350000

''' GPIO 핀 모드 세팅 '''
GPIO.setmode(GPIO.BCM) # BCM GPIO 핀 배열을 사용하도록 지정
GPIO.setup(ledPower, GPIO.OUT) # 미세먼지 센서의 LED 핀 설정
GPIO.setup(servoPin, GPIO.OUT)
p = GPIO.PWM(servoPin, 50) # 서보모터 설정
p.start(0)
p.ChangeDutyCycle(5)

''' 시리얼 통신 세팅 '''
ARD = serial.Serial(PORT, baudrate)

''' 아날로그 input 함수 '''
def analog_read(channel):
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    adc_out = ((r[1]&3) << 8) + r[2]
    return adc_out

''' 서버와의 연동 '''
def sync():
   ''' 어쩔 수 없다..'''
   global isFirst
   global response
   global dustFactor

   global windowCommand
   global dustDensityFromServer
   global mDustDensityFromServer
   global dustConditionFromServer
   global mdustConditionFromServer

   url = "https://soooserver.azurewebsites.net/rpi/sync/" + str(dustFactor) + "/" + str(int(isFirst))
   isFirst = False
   print("DEBUG: url: " + url)
   response = urllib.request.urlopen(url).read().decode('utf-8')

   response = json.loads(response) # 결과를 딕셔너리 타입으로 변환
   print()
   print()
   print("response: " + str(response))
   print("싱크 완료")
   print()
   print()
   #print(response)

   windowCommand = int(response['command'])
   dustDensityFromServer = int(response['dust'])
   mDustDensityFromServer = int(response['mdust'])
   dustConditionFromServer = int(response['dustCondition'])
   mdustConditionFromServer = int(response['mDustCondition'])

   threading.Timer(5, sync).start() # 주기적으로 실행하도록 예약



''' 메인실행 '''
sync() # 싱크는 딱 한번만 실행

# 계속 실행

try:
   while True:
      ''' dustFactor 받아오기 '''
      if ARD.readable():
         dustFactor = int(float(ARD.readline().decode()))

         print("dustFactor: %d" % dustFactor)
      else:
         print("dustSensor read error")

      ''' 창문을 닫아야 하는지 판단하기 '''
      
         
      if(dustFactor > 500) or (dustDensityFromServer > dustConditionFromServer) or (mDustDensityFromServer > mdustConditionFromServer):
         requiredToClose = True
      else:
         requiredToClose = False

      ''' 명령 강제 실행 '''
      if windowCommand == 3: #창문 닫기
         p.ChangeDutyCycle(11.5)
         time.sleep(10)
         continue
      elif windowCommand == 2: # 창문 열기
         p.ChangeDutyCycle(5)
         time.sleep(10)
         continue
      

      ''' 창문을 진짜 열까? '''
      if (requiredToClose == True) and (windowIsOpen == True):
         print("창문 닫기")
         #GPIO.setup(servoPin, GPIO.OUT)
         p.ChangeDutyCycle(11.5) # -90도
        ## GPIO.setup(servoPin, GPIO.IN)
         windowIsOpen = False
      elif (requiredToClose == False) and (windowIsOpen == False):
         print("창문 열기")
         #GPIO.setup(servoPin, GPIO.OUT)
         p.ChangeDutyCycle(5) # +90도
        # GPIO.setup(servoPin, GPIO.IN)
         windowIsOpen = True


      print("현재 상태: 창문을 닫아야 하나: %d 창문이 열려있나: %d" % (int(requiredToClose), int(windowIsOpen)))
      time.sleep(1)

except KeyboardInterrupt: # If Ctrl + C is pressed, exit cleanly
   print("Keyboard Interrupt")
   p.stop()

except:
   print("some error")

finally:
   print("Clean Up GPIO PINs")
   GPIO.cleanup()