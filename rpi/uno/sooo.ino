/* *
 * dustsensor.ino
 * optimized by John Choe
 * 
 * 2019-11-16
 * */

/*
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
 */
 
/*********************
 * 핀 연결 정보
 * Vcc: 5V
 * 측정 핀: Analog 0
 * LED : Digital 12
**********************/
#include <Servo.h>

Servo servo;

int servoPin = 5; // 서보모터 연결
int measurePin = 0; // 측정 핀을 Analog 5에서 Analog 0으로 변경
int ledPower = 12;

int samplingTime = 280;
int deltaTime = 40;
int sleepTime = 9680;

int minVal = 544;
int maxVal = 2400;

float voMeasured = 0;
float calcVoltage = 0;
float dustDensity = 0;

void setup()
{
	Serial.begin(9600);
	Serial.println("Servo Value = ?");
	servo.attach(pin, minVal, maxVal);
	servo.write(180);
	pinMode(ledPower,OUTPUT);
}

void loop()
{
	if(Serial.available() > 0)
	{
		int servoVal = Serial.parseInt();
		if(servoVal != 0)
		{
			servo.write(servoVal);
			Serial.println(servoVal);
		}
	}
	digitalWrite(ledPower,LOW); // power on the LED
	delayMicroseconds(samplingTime);

	voMeasured = analogRead(measurePin); // read the dust value

	delayMicroseconds(deltaTime);
	digitalWrite(ledPower,HIGH); // turn the LED off
	delayMicroseconds(sleepTime);

	// 0 - 5.0V mapped to 0 - 1023 integer values 
	calcVoltage = voMeasured * (5.0 / 1024); 

	// linear eqaution taken from http://www.howmuchsnow.com/arduino/airquality/
	// Chris Nafis (c) 2012
	dustDensity = (0.17 * calcVoltage - 0.1)*1000; 

	// Serial.print("Raw Signal Value (0-1023): ");
	Serial.println(voMeasured); // 시리얼 통신으로 raw data 출력하기

	delay(1000);
}