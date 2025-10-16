#include <ESP8266WiFi.h>
#include <TinyGPS++.h>
#include <SoftwareSerial.h>
#include <ESP8266WebServer.h>

// Wi-Fi credentials
const char* ssid = "Live_Map";
const char* password = "livemap@pass";

// GPS pins
SoftwareSerial gpsSerial(D6, D7); // RX, TX
TinyGPSPlus gps;

// Web server
ESP8266WebServer server(80);

// Handle /gps endpoint
void handleGPS() {
  String response = "{";
  if (gps.location.isValid()) {
    response += "\"lat\":" + String(gps.location.lat(), 6) + ",";
    response += "\"lon\":" + String(gps.location.lng(), 6) + ",";
    response += "\"satellites\":" + String(gps.satellites.value());
  } else {
    response += "\"lat\":null,\"lon\":null,\"satellites\":0";
  }
  response += "}";
  server.send(200, "application/json", response);
}

void setup() {
  Serial.begin(9600);

  // GPS baud rate (try 115200 for faster data if supported)
  gpsSerial.begin(9600);

  // Connect Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected! ESP IP: " + WiFi.localIP().toString());

  // Set up web server
  server.on("/gps", handleGPS);
  server.begin();
  Serial.println("Server started. Access /gps to get GPS data.");

  // Fast cold start: keep reading GPS until first fix
  Serial.println("Waiting for first GPS fix...");
  unsigned long start = millis();
  while (!gps.location.isValid()) {
    while (gpsSerial.available()) {
      gps.encode(gpsSerial.read()); // feed raw data
    }
    if (millis() - start > 5000) { // timeout every 5s
      Serial.print("Satellites: ");
      Serial.println(gps.satellites.value());
      start = millis();
    }
  }
  Serial.println("GPS fix acquired!");
  Serial.print("Lat: "); Serial.print(gps.location.lat(), 6);
  Serial.print(" | Lon: "); Serial.println(gps.location.lng(), 6);
}

void loop() {
  // Continuously read raw GPS bytes
  while (gpsSerial.available()) {
    gps.encode(gpsSerial.read());
  }

  // Debug: show satellites count every 2 seconds
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 2000) {
    lastPrint = millis();
    Serial.print("Satellites: ");
    Serial.println(gps.satellites.value());
    if (gps.location.isValid()) {
      Serial.print("Lat: "); Serial.print(gps.location.lat(), 6);
      Serial.print(" | Lon: "); Serial.println(gps.location.lng(), 6);
    } else {
      Serial.println("Waiting for fix...");
    }
  }

  // Handle web requests
  server.handleClient();
}
