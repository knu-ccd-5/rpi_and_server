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
@app.route("/rpi/sync/<rpiIp>/<dustFactor>")
def rpiSync(rpiIp, dustFactor):
    ''' 연결 기록하기 '''
    with codecs.open("isRpiConnected", "w", "utf-8") as file:
        file.write("1" + '\n') # 연결되었다고 기록
        file.write(rpiIp) #라즈베리파이의 ip 기록
    
    ''' 라즈베리가 측정한 먼지 척도를 기록 '''
    with codecs.open("rpiDust", "w", "utf-8") as file:
        file.write(dustFactor)

    ''' 라즈베리파이에 먼지 값 전달 '''
    return getWeather()




''' 기기 '''
# isRpiConnected
''' 명령을 받으면 기기로 보냄 '''
@app.route("/app/pushCommandFromApp/<int:command>")
def pushCommandFromApp(command):
    with open("isRpiConnected", "r") as file:
        connected = (file.readline())[:-1] # 연결됨: 1, 연결 안됨: 0
        url = "http://" + file.readline() + ":5000/pushCommand/" + str(command) # 라즈베리파이의 최근 접속 ip
    
    if int(float(connected)) == True:
        response = urllib.request.urlopen(url).read().decode('utf-8') # 라즈베리파이에 명령 전달
        returnData = "complete"
    else:
        returnData = "RaspberryPi is offline"

    return returnData

''' 기기에서 로그를 요청하면 반환 '''
@app.route("/app/requestLogFromApp")
def requestLogFromApp():
    with open("mainLog", "r") as file:
        log = file.read() # 파일 전체 읽기
    return log

''' 기기에서 날씨를 요청하면 반환 '''
@app.route("/app/requestWeatherFromApp")
def requestWeatherFromApp():
    return getWeather()




''' 서버 내부 '''
''' 서버에 저장된 날씨 정보를 반환하는 함수 '''
def getWeather():
    with codecs.open("weatherData", "r", 'utf-8') as file:
        data = {'weatherTable': (file.readline())[:-1], 'tempTable': (file.readline())[:-1], 'dust': (file.readline())[:-1], 'mdust': (file.readline())[:-1]}
        return jsonify(data)

''' 현재 시간을 반환하는 함수 '''
def nowDate():
    now = datetime.now()
    return now.year + "년" + now.month + "월" + now.day + "일" + now.hour + "시" + now.minute + "분" + now.second + "초"
    # return {'YEAR': now.year, 'MONTH': now.month, 'DAY': now.day, 'HOUR': now.hour, 'MINUTE': now.minute,
    #         'SECOND': now.second}


''' 날씨를 크롤링하는 함수'''
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
    threading.Timer(3, crawling).start() # 3초마다 한 번 실행하도록 예약
    return weatherTable, tempTable, dust, rainTable

@app.route('/ip', methods=['GET'])
def name():
    return request.environ.get('HTTP_X_REAL_IP', request.remote_addr) #return jsonify({'ip': request.remote_addr}), 200 #return jsonify({'ip': request.environ['REMOTE_ADDR']}), 200


if __name__ == '__main__':
    crawling()
    # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # s.connect(('8.8.8.8', 1))
    # print(s.getsockname()[0])
    app.run()