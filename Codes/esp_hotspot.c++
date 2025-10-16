#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <SoftwareSerial.h>

// ---------------- Wi-Fi Settings ----------------
const char* ssid = "Live_Map";
const char* password = "livemap@pass";

// ---------------- Pins ----------------
#define UNO_RX D7  // ESP RX <- Arduino TX
#define UNO_TX D6  // ESP TX -> Arduino RX (optional)
SoftwareSerial unoSerial(UNO_RX, UNO_TX);

// ---------------- TCP Settings ----------------
WiFiServer server(80);  // TCP server on port 80
WiFiClient client;

unsigned long previousMillis = 0;
const long interval = 50; // ms between sending readings

// ---------------- Globals ----------------
String distanceStr = "";
char distanceChar[10];
IPAddress pcIP;  // not really needed in TCP server mode

void setup() {
  Serial.begin(115200);
  unoSerial.begin(9600);

  // Connect to Wi-Fi
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ssid, password);
  Serial.println("Wi-Fi AP started!");
  Serial.print("ESP IP: "); Serial.println(WiFi.softAPIP());

  // Start TCP server
  server.begin();
  Serial.println("TCP server started on port 80");
}

void loop() {
  // Step 1: Accept new TCP client
  if (!client || !client.connected()) {
    client = server.available();
  }

  // Step 2: Read distance from Arduino via SoftwareSerial
  while (unoSerial.available()) {
    char c = unoSerial.read();
    if (c == '\n') {
      distanceStr.trim();  // remove \r or spaces
      if (distanceStr.length() > 0) {
        Serial.println("Distance: " + distanceStr);
        distanceStr.toCharArray(distanceChar, sizeof(distanceChar));
        previousMillis = millis();
      }
      distanceStr = "";
    } else if (c != '\r') {
      distanceStr += c;
    }
  }

  // Step 3: Send to TCP client every interval
  if (client && client.connected() && distanceChar[0] != 0) {
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= interval) {
      previousMillis = currentMillis;
      client.println(distanceChar);
      // clear after sending
      distanceChar[0] = 0;
    }
  }
}
