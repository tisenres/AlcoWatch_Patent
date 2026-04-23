// arduino/stress_cabin_control/stress_cabin_control.ino
/*
 * Driver Stress Adaptive Cabin Control
 * Receives 12-byte stress packet via BLE, responds:
 *   Level 0 (Calm)     → warm white LED, 30% fan, silence
 *   Level 1 (Mild)     → neutral white, 50% fan
 *   Level 2 (Moderate) → blue LED, 75% fan, soft music
 *   Level 3 (Critical) → red blink, 100% fan, voice alert
 *
 * Hardware: Arduino Nano 33 BLE
 * Pins: 9=LED_R, 10=LED_G, 11=LED_B, 6=FAN, Serial1=DFPlayer Mini
 */

#include <ArduinoBLE.h>

#define PIN_LED_R   9
#define PIN_LED_G  10
#define PIN_LED_B  11
#define PIN_FAN     6
#define PIN_OVERRIDE 7

#define SERVICE_UUID     "ABCD1234-1234-5678-1234-56789abcdef0"
#define STRESS_CHAR_UUID "ABCD1235-1234-5678-1234-56789abcdef0"
#define BLE_TIMEOUT_MS   60000UL

BLEService        cabinService(SERVICE_UUID);
BLECharacteristic stressChar(STRESS_CHAR_UUID, BLEWrite | BLENotify, 12);

enum CabinState : uint8_t {
  CALM     = 0,
  MILD     = 1,
  MODERATE = 2,
  CRITICAL = 3,
  WAITING  = 4,
};

struct Profile { uint8_t r, g, b, fan, audio; };
const Profile PROFILES[4] = {
  {255, 200, 100,  76, 0},  // CALM
  {255, 255, 200, 127, 0},  // MILD
  { 50,  50, 255, 191, 1},  // MODERATE
  {255,   0,   0, 255, 2},  // CRITICAL
};

CabinState currentState = WAITING;
unsigned long lastUpdateMs = 0;
unsigned long lastBlinkMs  = 0;
bool blinkOn = false;

void setLED(uint8_t r, uint8_t g, uint8_t b) {
  analogWrite(PIN_LED_R, r);
  analogWrite(PIN_LED_G, g);
  analogWrite(PIN_LED_B, b);
}

void dfplayerCmd(uint8_t cmd, uint8_t p1, uint8_t p2) {
  uint16_t sum = (~(uint16_t)(0xFF + 0x06 + cmd + p1 + p2)) + 1;
  uint8_t msg[] = {0x7E, 0xFF, 0x06, cmd, 0x00, p1, p2,
                   (uint8_t)(sum >> 8), (uint8_t)(sum & 0xFF), 0xEF};
  Serial1.write(msg, 10);
}

void applyProfile(CabinState s) {
  if (s >= 4) return;
  const Profile& p = PROFILES[s];
  setLED(p.r, p.g, p.b);
  analogWrite(PIN_FAN, p.fan);
  if (p.audio == 0) dfplayerCmd(0x16, 0, 0);       // stop
  else              dfplayerCmd(0x03, 0, p.audio);  // play track
}

void transitionTo(CabinState next) {
  if (next == currentState) return;
  currentState = next;
  applyProfile(next);
  Serial.print("State → "); Serial.println(next);
}

void setup() {
  Serial.begin(115200);
  Serial1.begin(9600);
  pinMode(PIN_LED_R, OUTPUT); pinMode(PIN_LED_G, OUTPUT);
  pinMode(PIN_LED_B, OUTPUT); pinMode(PIN_FAN, OUTPUT);
  pinMode(PIN_OVERRIDE, INPUT_PULLUP);
  setLED(0, 0, 50); analogWrite(PIN_FAN, 0);  // waiting: dim blue

  if (!BLE.begin()) { Serial.println("BLE failed"); while (1); }
  BLE.setLocalName("StressCabin");
  BLE.setAdvertisedService(cabinService);
  cabinService.addCharacteristic(stressChar);
  BLE.addService(cabinService);
  BLE.advertise();
  Serial.println("Cabin control ready.");
  lastUpdateMs = millis();
}

void loop() {
  BLEDevice central = BLE.central();

  if (central && central.connected()) {
    lastUpdateMs = millis();
    if (stressChar.written()) {
      uint8_t buf[12] = {};
      stressChar.readValue(buf, 12);
      uint8_t level      = buf[8];
      uint8_t confidence = buf[9];
      if (level <= 3 && confidence > 60) {
        transitionTo((CabinState)level);
      }
    }
    if (currentState == CRITICAL && millis() - lastBlinkMs > 250) {
      blinkOn = !blinkOn;
      setLED(blinkOn ? 255 : 80, 0, 0);
      lastBlinkMs = millis();
    }
  }

  if (millis() - lastUpdateMs > BLE_TIMEOUT_MS && currentState != WAITING) {
    Serial.println("BLE timeout.");
    currentState = WAITING;
    setLED(0, 0, 50);
    analogWrite(PIN_FAN, 0);
  }
}
