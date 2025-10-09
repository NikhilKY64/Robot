#include <WiFi.h>
#include <HTTPClient.h>
#include <TinyGPS++.h>
#include <HardwareSerial.h>

// Wi-Fi credentials
const char* ssid = "YourSchoolWiFi";
const char* password = "WiFiPassword";

// Flask server URL
const char* serverURL = "http://192.168.1.100:5000/update"; // replace with PC IP

// GPS setup
TinyGPSPlus gps;
HardwareSerial gpsSerial(1); // Use Serial1: RX1=16, TX1=17

void setup() {
  Serial.begin(115200);
  gpsSerial.begin(9600, SERIAL_8N1, 16, 17); // RX=16, TX=17

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
}

void loop() {
  while (gpsSerial.available() > 0) {
    char c = gpsSerial.read();
    gps.encode(c);

    if (gps.location.isUpdated()) {
      double lat = gps.location.lat();
      double lon = gps.location.lng();
      double speed = gps.speed.kmph();
      double alt = gps.altitude.meters();

      // Send GPS data to Flask server
      if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        String url = String(serverURL) + "?lat=" + String(lat,6) + "&lon=" + String(lon,6);
        http.begin(url);
        int httpResponseCode = http.GET();
        http.end();
      }

      Serial.print("Sent: ");
      Serial.print(lat,6); Serial.print(","); Serial.println(lon,6);
      delay(1000); // 1-second delay between updates
    }
  }
}
