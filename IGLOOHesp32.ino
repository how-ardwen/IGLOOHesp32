#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>

// SDA and SCL pins for the decibel meter module
#define I2C_SDA                 21
#define I2C_SCL                 22

// I2C address for the module
#define DBM_ADDR                0x48

// Device registers
#define   DBM_REG_VERSION       0x00
#define   DBM_REG_ID3           0x01
#define   DBM_REG_ID2           0x02
#define   DBM_REG_ID1           0x03
#define   DBM_REG_ID0           0x04
#define   DBM_REG_SCRATCH       0x05
#define   DBM_REG_CONTROL       0x06
#define   DBM_REG_TAVG_HIGH     0x07
#define   DBM_REG_TAVG_LOW      0x08
#define   DBM_REG_RESET         0x09
#define   DBM_REG_DECIBEL       0x0A
#define   DBM_REG_MIN           0x0B
#define   DBM_REG_MAX           0x0C
#define   DBM_REG_THR_MIN       0x0D
#define   DBM_REG_THR_MAX       0x0E
#define   DBM_REG_HISTORY_0     0x14
#define   DBM_REG_HISTORY_99    0x77

TwoWire dbmeter = TwoWire(0);

// Function to read a register from decibel meter
uint8_t dbmeter_readreg (TwoWire *dev, uint8_t regaddr)
{
  dev->beginTransmission (DBM_ADDR);
  dev->write (regaddr);
  dev->endTransmission();
  dev->requestFrom (DBM_ADDR, 1);
  delay (10);
  return dev->read();
}

void setup() {
  Serial.begin (115200);

  // Wait and set up Wi-Fi connection
  delay (6000);
  WiFi.begin ("Townhouse 14", "CVTH07299");

  while (WiFi.status() != WL_CONNECTED)
  {
    delay (5000);
    Serial.println ("Connecting to WiFi network 'Townhouse 14'...");
  }
  Serial.println ("Connected!");
}

void loop() {
  // Initialize I2C at 10kHz
  dbmeter.begin (I2C_SDA, I2C_SCL, 10000);

  // Read version register
  uint8_t version = dbmeter_readreg (&dbmeter, DBM_REG_VERSION);
  Serial.printf ("Version = 0x%02X\r\n", version);

  // Read ID registers
  uint8_t id[4];
  id[0] = dbmeter_readreg (&dbmeter, DBM_REG_ID3);
  id[1] = dbmeter_readreg (&dbmeter, DBM_REG_ID2);
  id[2] = dbmeter_readreg (&dbmeter, DBM_REG_ID1);
  id[3] = dbmeter_readreg (&dbmeter, DBM_REG_ID0);
  Serial.printf ("Unique ID = %02X %02X %02X %02X\r\n", id[3], id[2], id[1], id[0]);

  uint8_t db, dbmin, dbmax;
  String DBMjson;
  while (1)
  {
    // Read decibel, min and max
    db = dbmeter_readreg (&dbmeter, DBM_REG_DECIBEL);
    if (db == 255)
      continue;
    dbmin = dbmeter_readreg (&dbmeter, DBM_REG_MIN);
    dbmax = dbmeter_readreg (&dbmeter, DBM_REG_MAX);
    Serial.printf ("dB reading = %03d \t [MIN: %03d \tMAX: %03d] \r\n", db, dbmin, dbmax);
    
    // Assemble JSON with dB SPL reading
    DBMjson = "{\"db\": " + String(db) + "}";
    Serial.println ("JSON: \n" + DBMjson);
    
    // Make a POST request with the data
    if ((WiFi.status() == WL_CONNECTED))
    {
      //Check the current connection status
      HTTPClient http;
      
      http.begin("https://demo.thingsboard.io/api/v1/MpvD4JYOpDvbKIJLvFif/telemetry");
      http.addHeader("Content-Type", "application/json");
      int httpResponseCode = http.POST(DBMjson);   //Send the actual POST request
  
      if(httpResponseCode>0)
      {
        //Get the response to the request
        String response = http.getString();
        Serial.println(httpResponseCode);   //Print return code
        Serial.println(response);           //Print request answer
      }
      else
      {
        Serial.print("Error on sending POST: ");
        Serial.println(httpResponseCode);
      }
      
      http.end();  //Free resources
    }
    else
    {
      Serial.println ("Something wrong with WiFi?");
    }
        
    // Wait for 5 seconds before posting another reading
    delay (1000);
  }
}
