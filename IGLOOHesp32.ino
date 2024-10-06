/*
IGLOOH ESP32 proof of concept code
Howard Wen
July 2024
*/

// LIBRARIES
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <WiFi.h>
#include <HTTPClient.h>

// CONSTANTS
// SPI pins
#define MOSI 23
#define MISO 19
#define SCK 18
#define BME_CS 5
// SDA and SCL pins for the decibel meter module + RTC
#define I2C_SDA 21
#define I2C_SCL 22
#define WIFI_NAME "BELL882"
#define WIFI_PW "37E26FF916A6"


// CONSTANTS
#define SEALEVELPRESSURE_HPA (1013.25)

// I2C address for the DM module
#define DBM_ADDR 0x48
// DM device registers
#define DBM_REG_VERSION 0x00
#define DBM_REG_ID3 0x01
#define DBM_REG_ID2 0x02
#define DBM_REG_ID1 0x03
#define DBM_REG_ID0 0x04
#define DBM_REG_SCRATCH 0x05
#define DBM_REG_CONTROL 0x06
#define DBM_REG_TAVG_HIGH 0x07
#define DBM_REG_TAVG_LOW 0x08
#define DBM_REG_RESET 0x09
#define DBM_REG_DECIBEL 0x0A
#define DBM_REG_MIN 0x0B
#define DBM_REG_MAX 0x0C
#define DBM_REG_THR_MIN 0x0D
#define DBM_REG_THR_MAX 0x0E
#define DBM_REG_HISTORY_0 0x14
#define DBM_REG_HISTORY_99 0x77

// OBJECTS
// Adafruit_BME280 bme; // I2C
//Adafruit_BME280 bme(BME_CS, BME_MOSI, BME_MISO, BME_SCK); // software SPI
Adafruit_BME280 bme(BME_CS);   // hardware SPI
TwoWire dbmeter = TwoWire(0);  // dB meter i2c connection

// VARIABLES
unsigned long delayTime;

void setup() {
  Serial.begin(115200);
  while (!Serial)
    ;  // time to get serial running

  // start BME 280
  Serial.println(F("BME280 test"));
  unsigned bme_status;

  // default settings
  bme_status = bme.begin();
  // You can also pass in a Wire library object like &Wire2
  // status = bme.begin(0x76, &Wire2)
  if (!bme_status) {
    Serial.println("Could not find a valid BME280 sensor, check wiring, address, sensor ID!");
    Serial.print("SensorID was: 0x");
    Serial.println(bme.sensorID(), 16);
    Serial.print("        ID of 0xFF probably means a bad address, a BMP 180 or BMP 085\n");
    Serial.print("   ID of 0x56-0x58 represents a BMP 280,\n");
    Serial.print("        ID of 0x60 represents a BME 280.\n");
    Serial.print("        ID of 0x61 represents a BME 680.\n");
    while (1) delay(10);
  }

  Serial.println("-- Default Test --");

  // start decibel meter
  Serial.println(F("Decibel Meter test"));
  // Wait and set up Wi-Fi connection
  delay(2000);
  WiFi.begin(WIFI_NAME, WIFI_PW);

  while (WiFi.status() != WL_CONNECTED) {
    delay(5000);
    Serial.printf("Connecting to WiFi network %s ...\n", WIFI_NAME);
  }
  Serial.println("Connected!");
  // Initialize I2C at 10kHz
  dbmeter.begin(I2C_SDA, I2C_SCL, 10000);

  // Read version register
  uint8_t version = dbmeter_readreg(&dbmeter, DBM_REG_VERSION);
  Serial.printf("Version = 0x%02X\r\n", version);

  // Read ID registers
  uint8_t id[4];
  id[0] = dbmeter_readreg(&dbmeter, DBM_REG_ID3);
  id[1] = dbmeter_readreg(&dbmeter, DBM_REG_ID2);
  id[2] = dbmeter_readreg(&dbmeter, DBM_REG_ID1);
  id[3] = dbmeter_readreg(&dbmeter, DBM_REG_ID0);
  Serial.printf("Unique ID = %02X %02X %02X %02X\r\n", id[3], id[2], id[1], id[0]);


  delayTime = 2500;
  Serial.println();
}


void loop() {
  uint8_t db, dbmin, dbmax;
  float temperature, pressure, rh;

  printValues(&temperature, &pressure, &rh);
  String DBMjson;
  // Read decibel, min and max
  db = dbmeter_readreg(&dbmeter, DBM_REG_DECIBEL);
  if (db != 255){
    dbmin = dbmeter_readreg(&dbmeter, DBM_REG_MIN);
    dbmax = dbmeter_readreg(&dbmeter, DBM_REG_MAX);
    Serial.printf("dB reading = %03d \t [MIN: %03d \tMAX: %03d] \r\n", db, dbmin, dbmax);

    // Assemble JSON with dB SPL reading
    DBMjson = "{\"db\": " + String(db) + ", \"temperature\": " + String(temperature) + "}";
    Serial.println("JSON: \n" + DBMjson);

    // Make a POST request with the data
    if ((WiFi.status() == WL_CONNECTED)) {
      //Check the current connection status
      HTTPClient http;

      http.begin("https://demo.thingsboard.io/api/v1/MpvD4JYOpDvbKIJLvFif/telemetry");
      http.addHeader("Content-Type", "application/json");
      int httpResponseCode = http.POST(DBMjson);  //Send the actual POST request

      if (httpResponseCode > 0) {
        //Get the response to the request
        String response = http.getString();
        Serial.println(httpResponseCode);  //Print return code
        Serial.println(response);          //Print request answer
      } else {
        Serial.print("Error on sending POST: ");
        Serial.println(httpResponseCode);
      }

      http.end();  //Free resources
    } else {
      Serial.println("Something wrong with WiFi?");
    }
    delay(delayTime);
  }
}


void printValues(float* temp_address, float* pressure_address, float* rh_address) {
    *temp_address = bme.readTemperature();
    Serial.printf("Temperature: %.2f °C\n", *temp_address);

    *pressure_address = bme.readPressure();
    Serial.printf("Pressure: %.2f hPa\n", *pressure_address);

    *rh_address = bme.readHumidity();
    Serial.printf("Relative Humidity: %.2f%\n", *rh_address);

    Serial.println();
}


// Function to read a register from decibel meter
uint8_t dbmeter_readreg(TwoWire *dev, uint8_t regaddr) {
  dev->beginTransmission(DBM_ADDR);
  dev->write(regaddr);
  dev->endTransmission();
  dev->requestFrom(DBM_ADDR, 1);
  delay(10);
  return dev->read();
}
