#include <SoftwareSerial.h>
#include <TinyGPS++.h>

static const int RXPin = 4, TXPin = 3; // GPS module connected here
static const uint32_t GPSBaud = 9600;

TinyGPSPlus gps;
SoftwareSerial gpsSerial(RXPin, TXPin);

void setup() {
  Serial.begin(9600);
  gpsSerial.begin(GPSBaud);
  Serial.println("Waiting for GPS signal...");
}

void loop() {
  while (gpsSerial.available() > 0) {
    char c = gpsSerial.read();
    gps.encode(c);

    if (gps.location.isUpdated()) {
      double latitude = gps.location.lat();
      double longitude = gps.location.lng();
      double speed = gps.speed.kmph();
      double altitude = gps.altitude.meters();

      // Send data in required format
      Serial.print(latitude, 6);
      Serial.print(",");
      Serial.print(longitude, 6);
      Serial.print(",");
      Serial.print(speed, 2);
      Serial.print(",");
      Serial.println(altitude, 2);
    }
  }
}
