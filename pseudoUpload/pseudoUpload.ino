#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "BELL882";
const char* password = "37E26FF916A6";

void setup() {
    Serial.begin(115200);
    WiFi.begin(ssid, password);

    // Wait until the ESP32 connects to WiFi
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("Connected to WiFi");
}

void loop() {
  int delayTime = 5000;
  int db = 50;;
  float temperature = 26.7;
  String DBMjson;
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
