import serial
import urllib.request
import schedule
import threading
import json

# Set a PORT Number & Baudrate
PORT = '/dev/ttyACM0' # default COM PORT of Arduino on RaspberryPi
baudrate = 9600

ARD = serial.Serial(PORT, baudrate)

dustValue = 0
requiredToOpen = False

def sendInfo(dataType, success, dustValue):
    url = "http://127.0.0.1/inputFromRpi/" + str(dataType) + "/" + str(dustValue) + "/100"
    response = urllib.request.urlopen(url).read().decode('utf-8')
    threading.Timer(30, sendInfo).start() # 주기적으로 실행하도록 예약

    requiredToOpen = response['requiredToOpen'] # 창문을 열어야 하는지 업데이트

def request(url):
    response = urllib.request.urlopen(url).read().decode('utf-8')
    return response

# 서버에서 주기적으로 값을 받아오는 스케쥴러 실행
sendInfo(0, 1, dustValue)

# 계속 실행
while True:
    ''' 시리얼 통신으로 먼지 값 받아오기 '''
    if ARD.readable():
        LINE = ARD.readline().decode()
        print(LINE)
        dustValue = int(LINE)

    else:
        print("읽기 실패")

    ''' 창문을 열어야 하는지 판단 '''
    if requiredToOpen == True:
        #모터 구동
        sendInfo(1, 1, dustValue)