/*GPS TX → D4
GPS RX → D3
GPS VCC → 5V
GPS GND → GND

HC-05 TX → Arduino RX (pin 0)
HC-05 RX → Arduino TX (pin 1)
HC-05 VCC → 5V
HC-05 GND → GND
*/

#include <SoftwareSerial.h>
#include <TinyGPS++.h>

// GPS pins
static const int RXPin = 4; // Arduino receives GPS TX
static const int TXPin = 3; // Arduino sends to GPS RX (optional)
static const uint32_t GPSBaud = 9600;

TinyGPSPlus gps;
SoftwareSerial gpsSerial(RXPin, TXPin); // SoftwareSerial for GPS

void setup() {
  Serial.begin(9600);        // Hardware Serial → HC-05 Bluetooth
  gpsSerial.begin(GPSBaud);  // Start GPS communication
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

      // Send GPS data via Bluetooth (HC-05)
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
