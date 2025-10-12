#include <ESP8266WiFi.h>
#include <TinyGPS++.h>
#include <SoftwareSerial.h>
#include <ESP8266WebServer.h>

// Wi-Fi credentials
const char* ssid = "Realme Narzo 60x 5G";
const char* password = "885854032";

// GPS pins
SoftwareSerial gpsSerial(D6, D7); // RX, TX
TinyGPSPlus gps;

// Web server
ESP8266WebServer server(80);

void handleGPS() {
  String response = "{";
  response += "\"lat\":" + String(gps.location.lat(), 6) + ",";
  response += "\"lon\":" + String(gps.location.lng(), 6) + ",";
  response += "\"satellites\":" + String(gps.satellites.value());
  response += "}";
  server.send(200, "application/json", response);
}

void setup() {
  Serial.begin(9600);
  gpsSerial.begin(9600);

  // Connect Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected! ESP IP: " + WiFi.localIP().toString());

  server.on("/gps", handleGPS);
  server.begin();
}

void loop() {
  server.handleClient();
  while (gpsSerial.available()) {
    gps.encode(gpsSerial.read());
  }
}
