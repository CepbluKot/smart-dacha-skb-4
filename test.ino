#include "DHT.h"
#define DHTPIN 2                    // пин подключения контакта DATA
#define DHTTYPE DHT11               // DHT 11
#include <Wire.h>                   // библиотека для управления устройствами по I2C
#include <LiquidCrystal_I2C.h>      // подключаем библиотеку для QAPASS 1602
LiquidCrystal_I2C LCD(0x27, 20, 4); // присваиваем имя LCD для дисплея

DHT dht(DHTPIN, DHTTYPE);
void setup()
{
    LCD.init();      // инициализация LCD дисплея
    LCD.backlight(); // включение подсветки дисплея
    dht.begin();
    Serial.begin(9600);
}
void loop()
{
    float h = dht.readHumidity();
    float t = dht.readTemperature();

    String trigger;
    while (Serial.available() > 0)
    {
        LCD.clear();
        LCD.setCursor(1, 0);
        String trigger = (Serial.readString());
        if (trigger == "temp")
        {
            trigger += ": " + String(t);
        }
        if (trigger == "hum")
        {
            trigger += ": " + String(h);
        }
        LCD.print(trigger);
        Serial.println(trigger);
    }
    LCD.print(trigger);
}
