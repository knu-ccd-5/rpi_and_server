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
import spidev, time
import serial
import urllib.request
import json
import time
import socket
import threading

spi = spidev.SpiDev()
spi.open(0, 0)
measurePin = 0 # 측정 핀이 MCP3008에서 CH0
ledPower = 14 # led 전원공급 핀: GPIO 14
servoPin = 15 # 서보모터 핀

# samplingTime = 280
# deltaTime = 40
# sleepTime = 9680
samplingTime = 0.00028
deltaTime = 0.00004
sleepTime = 0.00968

voMeasured = 0
calcVoltage = 0
dustDensity = 0

dustFactor = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(ledPower, GPIO.OUT)
GPIO.setup(servoPin, GPIO.OUT)
GPIO.output(ledPower, False)

def analog_read(channel):
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    adc_out = ((r[1]&3) << 8) + r[2]
    return adc_out


def sync(url, dustFactor):
    ''' 라즈베리파이의 현재 ip 얻기 '''
    # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # s.connect(('8.8.8.8', 1))
    # rpiIp = s.getsockname()[0] # 라즈베리파이의 ip

    #url = url + "/rpi/sync/" + rpiIp + "/" + str(dustFactor)
    url = url + "/rpi/sync/" + str(dustFactor)
    print("DEBUG: url: " + url)
    response = urllib.request.urlopen(url).read().decode('utf-8')

    response = json.loads(response) # 결과를 딕셔너리 타입으로 변환
    print(response)
    #print(response)
    threading.Timer(3, sync, dustFactor).start() # 주기적으로 실행하도록 예약
    return response

windowIsOpen = True
dustFactor = 0
requiredToClose = False
command = 0
url = "http://soooserver.azurewebsites.net"

p = GPIO.PWM(servoPin, 50)
p.start(0)
response = sync(url, dustFactor)

# 계속 실행
while True:
    #time.sleep(3) # 3초간 쉬기
    time.sleep(1)

    GPIO.output(ledPower, False) # LED 전원 끄기
    time.sleep(samplingTime)

    voMeasured = analog_read(measurePin) # read the dust value
    dustFactor = voMeasured
    print(dustFactor)
    time.sleep(deltaTime)
    GPIO.output(ledPower, True)
    time.sleep(sleepTime)
    #calcVoltage = voMeasured * (3.3 / 1024)
    #dustDensity = (0.17 * calcVoltage - 0.1) * 1000
    #print(voMeasured)
    #print("Reading = %f\tVoltage = %f\tdustFactor = %f" % (voMeasured, calcVoltage, dustFactor))
    # 서버와 sync

    print(response)

    '''창문을 열어야 하는지 판단 '''
    dustDensityFromServer = int(response['dust'][:-3])
    mDustDensityFromServer = int(response['mdust'][:-3])


    if (dustFactor > 500) or (dustDensityFromServer > 100) or (mDustDensityFromServer > 35):
        requiredToClose = True
    else:
        requiredToClose = False


    if requiredToClose == True:
        # if windowIsOpen == True: # 창문이 열려있을 때
        GPIO.setup(servoPin, GPIO.OUT)
        p.ChangeDutyCycle(7.5)
        GPIO.setup(servoPin, GPIO.IN)
        print("모터 구동")
        windowIsOpen = False # 창문이 닫혔다고 설정
    else:
        # if windowIsOpen == False: # 창문이 닫혀있을 떄
        GPIO.setup(servoPin, GPIO.OUT)
        p.ChangeDutyCycle(2.5)
        GPIO.setup(servoPin, GPIO.IN)
        windowIsOpen = True # 창문이 열려있다고 설정
    time.sleep(0.5)

    print("DEBUG: checking 'requiredToOpen'")
    print("DEBUG: requiredToOpen: %d" % requiredToClose)



# def sendInfo(url, dataType, success, dustValue):
#     global requiredToOpen
#     print("DEBUG: sendInfo(%d, %d, %d)" % (dataType, success, dustValue))
#     url = url + "/inputFromRPi/" + str(dataType) + "/" + str(success) + "/" + str(dustValue) + "/100"
#     response = urllib.request.urlopen(url).read().decode('utf-8')
#     #threading.Timer(30, sendInfo).start() # 주기적으로 실행하도록 예약

#     #requiredToOpen = int(response) # 창문을 열어야 하는지 업데이트
#     print("requiredToOpen: %d" % requiredToOpen)

# def request(url):
#     global requiredToOpen
#     global command
#     print("DEBUG: request()")
#     url = "http://127.0.0.1:5000/requestFromRPi"
#     response = urllib.request.urlopen(url).read().decode('utf-8')
#     threading.Timer(3, request).start()

#     response = json.loads(response)
#     requiredToOpen = response['requiredToOpen']
#     command = response['command']
#     weather = response['weatherInfo']


    # print()
    # print()
    # print("DEBUG: requiredToOpen: %d" % requiredToOpen)
    # print("DEBUG: command: %d" % command)
    # print("DEBUG: 날씨: %s" % weather)
    # # print("DEBUG: 날씨: %s" % weather['weatherTable'])
    # # print("DEBUG: 현재 온도: %d" % weather['tempTable'])
    # # print("DEBUG: 미세먼지: %d" % weather['dust'])
    # # print("DEBUG: 초미세먼지: %d" % weather['mdust'])

    # print()
    # print()
    # print()


    

    


# 서버에서 주기적으로 값을 받아오는 스케쥴러 실행
#    dataType
#    0: 모터 상태, 미세먼지 측정값 전송 (주기적인 로그 전송)
#    1: 모터 작동여부 전송
#    2: command(재부팅, 종료 등) 성공여부 전송
# print("DEBUG: sendInfo(0, 1, dustValue)")
# #sendInfo(0, 1, dustValue)
# request(


        # threading.Timer(3, request).start()