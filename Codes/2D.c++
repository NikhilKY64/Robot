// code for Arduino Uno
#include <NewPing.h>

#define TRIGGER_PIN 15
#define ECHO_PIN 14
#define MAX_DISTANCE 200

NewPing sonar(TRIGGER_PIN, ECHO_PIN, MAX_DISTANCE);

void setup() {
  Serial.begin(9600);
}

void loop() {
  unsigned int distance = sonar.ping_cm();  // distance in cm
  if (distance == 0) {
    Serial.println("No echo");  // better than just 0
  } else {
    Serial.println(distance);
  }
  delay(500);
}