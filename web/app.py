#-*- coding:utf-8 -*-
import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')

from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import threading
import urllib.request
import socket
import codecs

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello Flask, on Azure App Service for Linux"

@app.route("/aaa")
def hello2():
    return "Hello Flask, on Azure App Service for "


''' 라즈베리파이 '''
''' 라즈베리파이의 주기적인 sync '''
@app.route("/rpi/sync/<dustFactor>/<int:isFirst>")
def rpiSync(dustFactor, isFirst):
    genLog("라즈베리파이와 동기화를 진행합니다.")
    if isFirst == True:
        ''' 처음 접속이면 날씨 크롤링 -> 크롤링 함수는 한 번만 실행하면 됨 '''
        genLog("라즈베리파이의 부팅 후 첫 접속")
        crawling()

    ''' 연결 기록하기 '''
    with codecs.open("isRpiConnected", "w", "utf-8") as file:
        file.write("1") # 연결되었다고 기록
        #file.write(rpiIp) #라즈베리파이의 ip 기록
    
    ''' 라즈베리가 측정한 먼지 척도를 기록 '''
    with codecs.open("rpiDust", "w", "utf-8") as file:
        file.write(dustFactor)


    ''' 라즈베리파이에 먼지 값, 조건 전달 '''
    with open("dustConditionToClose", "r") as file:
                dustCondition = (file.readline())[:-1]
                mDustCondition = file.readline()


    ''' command를 얻고 windowCommand를 초기화 '''
    with open("windowCommand", "r") as file: # 읽기 & 쓰기 모드. 내용을 완전히 지우고 새로 씀.
        commandContext = file.read()
    with open("windowCommand", "w") as file:
        file.write("0")

    ''' 날씨 정보 얻기 '''
    weatherContext = getWeather()
    print(weatherContext)
    dustValue = (weatherContext['dust'])[:-3]
    mdustValue = (weatherContext['mdust'])[:-3]

    ''' 반환할 데이터 생성 '''
    returnData = {'dust': dustValue, 'mdust': mdustValue, 'dustCondition': dustCondition, 'mDustCondition': mDustCondition, 'command': commandContext}
    return jsonify(returnData)



''' 기기 '''
''' 현재 창문 닫기 조건을 얻기 '''
@app.route("/app/getCloseCondition")
def getCloseCondition():
    connected = isRpiConnected()
    
    ''' 라즈베리파이가 서버와 연결되어 있지 않으면 '''
    if connected == False:
        return "RaspberryPi is Offline" # 함수 종료

    with open("dustConditionToClose", "r") as file:
        dustCondition = (file.readline())[:-1]
        mDustCondition = file.readline()

    return "미세먼지: " + str(dustCondition) + "㎍/㎥, 초미세먼지: " + str(mDustCondition) + "㎍/㎥"


''' 환기 조건(창문을 닫을 조건) 설정 '''
@app.route("/app/setCloseCondition/<int:dustCondition>/<int:mDustCondition>")
def setCloseCondition(dustCondition, mDustCondition):
    ''' 라즈베리파이가 서버와 연결되어 있지 않으면 '''
    if isRpiConnected == False:
        return "RaspberryPi is Offline" # 함수 종료

    with open("dustConditionToClose", "w") as file:
        file.write(str(dustCondition) + "\n" + str(mDustCondition))
    
    genLog("창문 닫기 설정을 미세먼지 " + str(dustCondition) + "㎍/㎥, 초미세먼지 " + str(mDustCondition) + "㎍/㎥로 지정했습니다.") # 로그 생성
    return "set dust condition: dust: " + str(dustCondition) + " mdust: " + str(mDustCondition)

    
# isRpiConnected
''' 창문 열기 명령을 받으면 기기로 보냄 '''
@app.route("/app/pushCommand/<int:command>")
def pushCommand(command):
    ''' 라즈베리파이가 서버와 연결되어 있는지 확인 '''
    connected = isRpiConnected()
    genLog("창문 열기 명령: 라즈베리파이 연결이 확인되었습니다.")
    ''' 라즈베리파이가 오프라인 상태이면 함수 종료 '''
    if connected == False:
        # response = urllib.request.urlopen(url).read().decode('utf-8') # 라즈베리파이에 명령 전달
        return "Raspberry Pi is Offline"

    ''' 
    command 2: 창문 열기
    command 3: 창문 닫기
    '''
    if command == 2:
        with open("windowCommand", "w") as file:
            file.write("2")
        genLog("창문 열기 명령: 창문을 열도록 설정합니다.")
        return "set to window open"
    elif command == 3:
        with open("windowCommand", "w") as file:
            file.write("3")
        genLog("창문 열기 명령: 창문을 닫도록 설정합니다.")
        return "set to window close"
    else:
        genLog("창문 열기 명령: 올바르지 않은 명령어입니다.")
        return "invalid command"

''' 기기에서 로그를 요청하면 반환 '''
@app.route("/app/requestLog")
def requestLog():
    with open("mainLog", "r") as file:
        log = file.read() # 파일 전체 읽기!
    genLog("기기에서 로그를 요청하였습니다")
    return log

''' 기기에서 날씨를 요청하면 반환 '''
@app.route("/app/requestWeather")
def requestWeather():
    genLog("앱에서 날씨 정보를 요청했습니다.") # 로그 생성
    return getWeather()


''' 서버 내부 '''
''' 서버에 저장된 날씨 정보를 반환하는 함수 '''
def getWeather():
    with codecs.open("weatherData", "r", 'utf-8') as file:
        data = {'weatherTable': (file.readline())[:-1], 'tempTable': (file.readline())[:-1], 'dust': (file.readline())[:-1], 'mdust': (file.readline())}
    print(data)
    return data

''' 현재 시간을 반환하는 함수 '''
def nowDate():
    now = datetime.now()
    return str(now.year) + "년" + str(now.month) + "월" + str(now.day) + "일" + str(now.hour) + "시" + str(now.minute) + "분" + str(now.second) + "초: "
    # return {'YEAR': now.year, 'MONTH': now.month, 'DAY': now.day, 'HOUR': now.hour, 'MINUTE': now.minute,
    #         'SECOND': now.second}

''' 라즈베리파이가 연결되어 있는지 체크하는 함수'''
def isRpiConnected():
        with open("isRpiConnected", "r") as file:
            connected = int(file.read()) # 연결됨: 1, 연결 안됨: 0
            # url = "http://" + file.readline() + ":5000/pushCommand/" + str(command) # 라즈베리파이의 최근 접속 ip
        if connected == 1:
            return True
        else:
            return False

''' 로그 생성 함수 '''
def genLog(stream):
    with codecs.open("mainLog", "a", "utf-8") as file:
        stream = nowDate() + stream
        file.write(stream + '\n')

@app.route('/ip', methods=['GET'])
def name():
    return request.environ.get('HTTP_X_REAL_IP', request.remote_addr) #return jsonify({'ip': request.remote_addr}), 200 #return jsonify({'ip': request.environ['REMOTE_ADDR']}), 200


''' 날씨를 크롤링하는 함수'''
''' 꼬이지 않도록 단 한번만 호출되어야 함 '''
def crawling():
    print("DEBUG: crawling from naver search result")
    URL = "https://search.naver.com/search.naver?sm=top_hty&fbm=1&ie=utf8&query=%EB%8C%80%EA%B5%AC+%EB%82%A0%EC%94%A8" # 네이버 검색 '대구 날씨'
    html = requests.get(URL).text
    soup = BeautifulSoup(html, 'html.parser')
    weatherTable = soup.find_all("p", class_="cast_txt")
    tempTable = soup.find_all("span", class_="todaytemp")
    dust = soup.find_all("span", class_="num")
    rainTable = soup.find_all("span", class_="weather_item_dotWrapper")
    print("DEBUG: crawling success")

    with codecs.open("weatherData", "w", "utf-8") as file:
        file.write(str(weatherTable[0].text) + '\n') # 흐림, 어제보다 낮아요
        file.write(str(tempTable[0].text) + '\n') # 현재 온도
        file.write(str(dust[4].text) + '\n') # 미세먼지
        file.write(str(dust[5].text)) # 초미세먼지
    print("DEBUG: writing success")
    genLog("날씨 정보를 서버에서 크롤링했습니다.") # 로그 생성
    threading.Timer(1800, crawling).start() # 1800초마다 한 번 실행하도록 예약
    return weatherTable, tempTable, dust, rainTable


if __name__ == '__main__':
    crawling()
    # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # s.connect(('8.8.8.8', 1))
    # print(s.getsockname()[0])
    app.run()