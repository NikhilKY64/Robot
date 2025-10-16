#include <ESP8266WiFi.h>
#include <SoftwareSerial.h>

// ---------------- Wi-Fi Credentials ----------------
const char* ssid = "Live_Map";       // 🔹 Your Wi-Fi SSID
const char* password = "livemap@pass"; // 🔹 Your Wi-Fi Password

// ---------------- Pins ----------------
#define UNO_RX D7  // ESP RX <- Arduino TX
#define UNO_TX D6  // ESP TX -> Arduino RX (optional)
SoftwareSerial unoSerial(UNO_RX, UNO_TX);

// ---------------- TCP Settings ----------------
WiFiServer server(80);   // Python will connect to port 80

void setup() {
  Serial.begin(115200);
  unoSerial.begin(9600);

  Serial.println();
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(ssid);

  // Connect to existing Wi-Fi
  WiFi.begin(ssid, password);

  // Wait until connected
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi connected!");
  Serial.print("ESP IP: ");
  Serial.println(WiFi.localIP()); // ⚠️ Use this IP in your Python script

  // Start TCP server
  server.begin();
  Serial.println("TCP server started on port 80");
}

void loop() {
  WiFiClient client = server.available();
  if (client) {
    Serial.println("Client connected");
    while (client.connected()) {
      if (unoSerial.available()) {
        String distance = unoSerial.readStringUntil('\n');
        distance.trim();
        if (distance.length() > 0) {
          Serial.println("Distance: " + distance);
          client.println(distance);  // send data to Python client
        }
      }
    }
    client.stop();
    Serial.println("Client disconnected");
  }
}
