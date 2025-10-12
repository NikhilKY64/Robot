#include <SoftwareSerial.h>
#include <TinyGPS++.h>

// GPS connected to Arduino pins 4 (RX) and 3 (TX)
SoftwareSerial gpsSerial(4, 3); // RX, TX
TinyGPSPlus gps;

void setup() {
  Serial.begin(9600);       // Serial Monitor
  gpsSerial.begin(9600);    // GPS module baud rate
  Serial.println("GPS module is ready. Waiting for data...");
}

void loop() {
  while (gpsSerial.available() > 0) {
    char c = gpsSerial.read();
    // Feed data to TinyGPS++
    gps.encode(c);
  }

  // Only print when a valid location is available
  if (gps.location.isUpdated()) {
    Serial.print("Latitude: ");
    Serial.println(gps.location.lat(), 6); // 6 decimal places
    Serial.print("Longitude: ");
    Serial.println(gps.location.lng(), 6);
    Serial.print("Satellites in use: ");
    Serial.println(gps.satellites.value());
    Serial.println("---------------------------");
  }
}
