from flask import Flask, request
from flask.json import jsonify
from datetime import datetime
import time
import threading

app = Flask(__name__)

''' 현재 날짜(시간)을 반환하는 함수 '''
def nowDate():
    now = datetime.now()
    return { 'YEAR': now.year, 'MONTH': now.month, 'DAY': now.day, 'HOUR': now.hour, 'MINUTE': now.minute, 'SECOND': now.second }

''' 메인 로그 저장 함수 '''
'''
    where: 어느 함수에서 호출되었는가?
    dataType: 로그의 타입; 정보(i), 경고(w), 에러(e), 심각(f)
    value: 로그가 가진 값
    isSuccess:
'''
def makeLog(where, dataType, value, isSuccess):
    now = datetime.now()

    log = {'YEAR': now.year, 'MONTH': now.month, 'DAY': now.day, 'HOUR': now.hour, 'MINUTE': now.minute, 'SECOND': now.second, 'dataType': dataType, 'value': value, 'isSuccess': isSuccess} # 현재 시간, 로그 타입, 성공 여부 저장

    logStr = str((log))
    with open("mainLog", "a") as file:
        file.write(logStr + '\n')

''' 앱에서 온 명령을 입력받기 '''
'''
    command value
    0: 아무것도 안함
    1: 라즈베리파이 재부팅
    2: 라즈베리파이 끄기
    3: 창문 열기
    4: 창문 닫기
'''
@app.route('/inputFromAPP/<int:command>/')
def inputFromAPP(command):
    with open("commandContext", "w") as file: # commandContext에 command를 저장
        file.write(str(command) + "\n")
    
    makeLog(inputFromAPP, "i", "command: " + command, "YES") # 로그 기록

''' command를 반환 '''
def getCommand():
    with open("commandContext", "r") as file:
        command = file.read()
    command = command[:-1] # 마지막 '\n' 삭제
    return command

''' 날씨 정보를 반환 '''
def getWeather():
    pass

''' 대기 정보를 반환 '''
def getAirInfo():
    pass

def getRequiredToOpen():
    with open("requiredToOpen", "r") as file:
        requiredToOpen = file.read()
    return requiredToOpen


''' 라즈베리파이에서 전송된 데이터를 입력받기 '''
#    dataType
#    0: 모터 상태, 미세먼지 측정값 전송 (주기적인 로그 전송)
#    1: 모터 작동여부 전송
#    2: command(재부팅, 종료 등) 성공여부 전송
@app.route('/inputFromRPi/<int:dataType>/<int:success>/<int:dustValue>/<int:motorValue>')
def inputFromRPi(dataType, success, dustValue, motorValue):
    if dataType == 0:
        value = "dustValue: " + str(dustValue) + " motorValue: " + str(motorValue)
        log = nowDate()
        log['dustValue'] = dustValue
        log['motorValue'] = motorValue
        with open("RPiLog", "a") as file:
            file.write(str(log) + '\n')

        makeLog("inputFromRPi", "i", value, "YES")
        return '200' # 성공 코드 리턴

    elif dataType == 1:
        if success == True:
            value = "motorValue: " + str(motorValue) + " Success: SUCCESS"
        else:
            value = "motorValue: " + str(motorValue) + " Success: FAIL"
        
        log = nowDate()
        log['value'] = value
        with open("motorLog", "a") as file:
            file.write(str(log) + '\n')

        makeLog("inputFromRPi", 'i', value, "YES")
        return '200'
    
    elif dataType == 2:
        pass
    
    else:
        makeLog("inputFromRPi", 'e', "type: " + str(dataType), "NO")
        return '404'

''' 라즈베리파이에서 주기적으로 데이터를 요청함 '''
''' 전달 할 것: 날씨정보, 대기정보, 앱에서 온 명령 '''
@app.route('/requestFromRPi')
def requestFromRPi():
    data = {'weatherInfo': getWeather(), 'airInfo': getAirInfo(), 'command': getCommand(), 'requiredToOpen': getRequiredToOpen()}
    return jsonify(data)

# 아래는 수정하지 말 것
if __name__ == '__main__':
    app.run()