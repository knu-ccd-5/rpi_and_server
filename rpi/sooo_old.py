import serial
import urllib.request
import schedule
import threading
import json
import time
import socket


def sync(url, dustFactor):
    ''' 라즈베리파이의 현재 ip 얻기 '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 1))
    rpiIp = s.getsockname()[0] # 라즈베리파이의 ip

    url = url + "/rpi/sync/" + rpiIp + "/" + str(dustFactor)
    print("DEBUG: url: " + url + '\n' + "DEBUG: ip: " + rpiIp)
    response = urllib.request.urlopen(url).read().decode('utf-8')


    response = json.loads(response) # 결과를 딕셔너리 타입으로 변환
    print(response)
    #print(response)
    return response



#Set a PORT Number & Baudrate
#PORT = '/dev/ttyACM0' # default COM PORT of Arduino on RaspberryPi
PORT = 'COM8' # debug
ARD = serial.Serial(PORT, baudrate = 9600, timeout = None)
dustFactor = 0
requiredToClose = False
command = 0
url = "http://127.0.0.1:5000"

# 계속 실행
while True:
    time.sleep(3) # 3초간 쉬기
    
    ''' 시리얼 통신으로 먼지 값 받아오기 '''
    if ARD.readable():
        LINE = ARD.readline().decode()       
        dustFactor = float(LINE)
        print(dustFactor)
        if dustFactor > 500:
            requiredToClose = True
        else:
            requiredToClose = False

    else:
        print("읽기 실패")


    '''창문을 열어야 하는지 판단 '''
    print("DEBUG: checking 'requiredToOpen'")
    print("DEBUG: requiredToOpen: %d" % requiredToClose)
    if requiredToClose == True:
        #모터 구동
        # sendInfo(1, 1, dustValue)
        pass

    # 서버와 sync
    response = sync(url, dustFactor)
    #print(response)






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