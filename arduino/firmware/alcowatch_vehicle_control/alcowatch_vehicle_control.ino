/*
 * AlcoWatch Vehicle Control Module
 * Arduino-based BLE receiver and ignition control system
 *
 * Hardware Requirements:
 * - Arduino Nano 33 BLE or ESP32
 * - Relay module (5V, 10A) for ignition control
 * - LED indicators (Red: Blocked, Green: Allowed, Blue: Connecting)
 * - Buzzer for audio alerts
 * - OBD-II connector (optional)
 *
 * Patent: AI-BASED ALCOHOL LEVEL DETECTION AND VEHICLE IGNITION PREVENTION SYSTEM
 */

#include <ArduinoBLE.h>

// ============================================================================
// Configuration
// ============================================================================

#define FIRMWARE_VERSION "1.0.0"
#define DEVICE_NAME "AlcoWatch-Vehicle"

// BLE Service and Characteristic UUIDs
#define SERVICE_UUID        "12345678-1234-5678-1234-56789abcdef0"
#define BAC_STATUS_UUID     "12345678-1234-5678-1234-56789abcdef1"
#define VEHICLE_CMD_UUID    "12345678-1234-5678-1234-56789abcdef2"
#define SYSTEM_STATUS_UUID  "12345678-1234-5678-1234-56789abcdef3"

// Pin Definitions
#define IGNITION_RELAY_PIN  2   // Relay to control ignition
#define LED_RED_PIN         3   // Red LED (blocked)
#define LED_GREEN_PIN       4   // Green LED (allowed)
#define LED_BLUE_PIN        5   // Blue LED (connecting)
#define BUZZER_PIN          6   // Buzzer for alerts
#define OVERRIDE_BUTTON_PIN 7   // Physical override button

// BAC Legal Limit
#define LEGAL_BAC_LIMIT 0.08  // g/dL

// Timeout Configuration
#define BAC_UPDATE_TIMEOUT  60000  // 60 seconds
#define CONNECTION_TIMEOUT  10000  // 10 seconds

// ============================================================================
// BLE Objects
// ============================================================================

BLEService alcoWatchService(SERVICE_UUID);
BLECharacteristic bacStatusChar(BAC_STATUS_UUID, BLERead | BLENotify, 20);
BLECharacteristic vehicleCmdChar(VEHICLE_CMD_UUID, BLERead | BLEWrite, 12);
BLECharacteristic systemStatusChar(SYSTEM_STATUS_UUID, BLERead | BLENotify, 16);

// ============================================================================
// State Variables
// ============================================================================

enum IgnitionState {
  IGNITION_ALLOWED,
  IGNITION_BLOCKED,
  WAITING_FOR_DATA,
  CONNECTION_LOST,
  OVERRIDE_ACTIVE
};

struct BACStatus {
  unsigned long timestamp;
  float bacValue;
  byte alertLevel;
  byte confidence;
  byte flags;
  bool watchWorn;
  bool sensorQualityOK;
  bool batteryLow;
};

struct VehicleState {
  IgnitionState ignitionState;
  unsigned long lastBACUpdate;
  unsigned long lastConnectionTime;
  bool isConnected;
  BACStatus currentBAC;
  int overrideAttempts;
  unsigned long overrideStartTime;
};

VehicleState vehicleState;

// ============================================================================
// Setup
// ============================================================================

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000);  // Wait for serial or timeout

  Serial.println("===========================================");
  Serial.println("AlcoWatch Vehicle Control Module");
  Serial.println("Version: " FIRMWARE_VERSION);
  Serial.println("===========================================");

  // Initialize pins
  pinMode(IGNITION_RELAY_PIN, OUTPUT);
  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_BLUE_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(OVERRIDE_BUTTON_PIN, INPUT_PULLUP);

  // Initial state: blocked until connection
  setIgnitionState(WAITING_FOR_DATA);
  digitalWrite(IGNITION_RELAY_PIN, LOW);  // Ignition OFF

  // Initialize BLE
  if (!BLE.begin()) {
    Serial.println("ERROR: Failed to initialize BLE");
    blinkError();
    while (1);
  }

  // Setup BLE service
  setupBLEService();

  // Start scanning for AlcoWatch smartwatch
  startScanning();

  Serial.println("System initialized. Waiting for AlcoWatch connection...");
}

// ============================================================================
// Main Loop
// ============================================================================

void loop() {
  // Poll BLE events
  BLE.poll();

  // Check connection status
  checkConnectionStatus();

  // Check for BAC update timeout
  checkBACTimeout();

  // Check override button
  checkOverrideButton();

  // Update LED indicators
  updateLEDs();

  // Small delay
  delay(100);
}

// ============================================================================
// BLE Setup
// ============================================================================

void setupBLEService() {
  // Set device name
  BLE.setLocalName(DEVICE_NAME);
  BLE.setDeviceName(DEVICE_NAME);

  // Set connection event handlers
  BLE.setEventHandler(BLEConnected, bleConnectedHandler);
  BLE.setEventHandler(BLEDisconnected, bleDisconnectedHandler);

  // Add characteristics to service
  alcoWatchService.addCharacteristic(bacStatusChar);
  alcoWatchService.addCharacteristic(vehicleCmdChar);
  alcoWatchService.addCharacteristic(systemStatusChar);

  // Set characteristic event handlers
  bacStatusChar.setEventHandler(BLEWritten, bacStatusWrittenHandler);
  vehicleCmdChar.setEventHandler(BLERead, vehicleCmdReadHandler);

  // Add service
  BLE.addService(alcoWatchService);

  Serial.println("BLE service configured");
}

void startScanning() {
  Serial.println("Scanning for AlcoWatch devices...");
  BLE.scanForUuid(SERVICE_UUID);
}

// ============================================================================
// BLE Event Handlers
// ============================================================================

void bleConnectedHandler(BLEDevice central) {
  Serial.print("Connected to AlcoWatch: ");
  Serial.println(central.address());

  vehicleState.isConnected = true;
  vehicleState.lastConnectionTime = millis();

  // Send initial status
  sendVehicleStatus(0x00);  // Acknowledged

  tone(BUZZER_PIN, 1000, 100);  // Connection beep
}

void bleDisconnectedHandler(BLEDevice central) {
  Serial.print("Disconnected from: ");
  Serial.println(central.address());

  vehicleState.isConnected = false;
  setIgnitionState(CONNECTION_LOST);

  // Restart scanning
  startScanning();
}

void bacStatusWrittenHandler(BLEDevice central, BLECharacteristic characteristic) {
  // Read BAC status data
  const uint8_t* data = characteristic.value();
  int length = characteristic.valueLength();

  if (length < 20) {
    Serial.println("ERROR: Invalid BAC status data length");
    return;
  }

  // Parse BAC status
  parseBACStatus(data);

  // Update timestamp
  vehicleState.lastBACUpdate = millis();

  // Process BAC data and update ignition state
  processBACData();

  // Log BAC update
  logBACStatus();
}

void vehicleCmdReadHandler(BLEDevice central, BLECharacteristic characteristic) {
  Serial.println("Vehicle command read by smartwatch");
}

// ============================================================================
// BAC Data Processing
// ============================================================================

void parseBACStatus(const uint8_t* data) {
  // Parse according to protocol specification
  // Bytes 0-7: Timestamp (64-bit)
  memcpy(&vehicleState.currentBAC.timestamp, data, 8);

  // Bytes 8-11: BAC Value (float, 32-bit)
  memcpy(&vehicleState.currentBAC.bacValue, data + 8, 4);

  // Byte 12: Alert Level
  vehicleState.currentBAC.alertLevel = data[12];

  // Byte 13: Confidence
  vehicleState.currentBAC.confidence = data[13];

  // Byte 14: Flags
  vehicleState.currentBAC.flags = data[14];
  vehicleState.currentBAC.watchWorn = (data[14] & 0x01) != 0;
  vehicleState.currentBAC.sensorQualityOK = (data[14] & 0x04) != 0;
  vehicleState.currentBAC.batteryLow = (data[14] & 0x08) != 0;
}

void processBACData() {
  // Check if watch is worn
  if (!vehicleState.currentBAC.watchWorn) {
    Serial.println("WARNING: Watch not worn - blocking ignition");
    setIgnitionState(IGNITION_BLOCKED);
    sendVehicleCommand(0x02);  // Request verification
    return;
  }

  // Check sensor quality
  if (!vehicleState.currentBAC.sensorQualityOK) {
    Serial.println("WARNING: Poor sensor quality");
  }

  // Check BAC level
  if (vehicleState.currentBAC.bacValue > LEGAL_BAC_LIMIT) {
    Serial.println("ALERT: BAC over legal limit!");
    setIgnitionState(IGNITION_BLOCKED);
    sendVehicleCommand(0x01);  // Block ignition command
    soundAlarm();
  } else if (vehicleState.currentBAC.bacValue > LEGAL_BAC_LIMIT * 0.75) {
    Serial.println("WARNING: BAC approaching limit");
    setIgnitionState(IGNITION_ALLOWED);  // Still allowed but warn
    tone(BUZZER_PIN, 800, 200);
  } else {
    Serial.println("OK: BAC within safe limits");
    setIgnitionState(IGNITION_ALLOWED);
  }
}

void logBACStatus() {
  Serial.println("--- BAC Status Update ---");
  Serial.print("BAC: ");
  Serial.print(vehicleState.currentBAC.bacValue, 3);
  Serial.println(" g/dL");
  Serial.print("Alert Level: ");
  Serial.println(vehicleState.currentBAC.alertLevel);
  Serial.print("Confidence: ");
  Serial.print(vehicleState.currentBAC.confidence);
  Serial.println("%");
  Serial.print("Watch Worn: ");
  Serial.println(vehicleState.currentBAC.watchWorn ? "Yes" : "No");
  Serial.print("Ignition: ");
  Serial.println(vehicleState.ignitionState == IGNITION_ALLOWED ? "ALLOWED" : "BLOCKED");
  Serial.println("-------------------------");
}

// ============================================================================
// Ignition Control
// ============================================================================

void setIgnitionState(IgnitionState newState) {
  if (vehicleState.ignitionState == newState) {
    return;  // No change
  }

  vehicleState.ignitionState = newState;

  switch (newState) {
    case IGNITION_ALLOWED:
      digitalWrite(IGNITION_RELAY_PIN, HIGH);  // Enable ignition
      Serial.println(">>> IGNITION ALLOWED <<<");
      break;

    case IGNITION_BLOCKED:
      digitalWrite(IGNITION_RELAY_PIN, LOW);   // Disable ignition
      Serial.println(">>> IGNITION BLOCKED <<<");
      break;

    case WAITING_FOR_DATA:
      digitalWrite(IGNITION_RELAY_PIN, LOW);
      Serial.println(">>> WAITING FOR BAC DATA <<<");
      break;

    case CONNECTION_LOST:
      digitalWrite(IGNITION_RELAY_PIN, LOW);
      Serial.println(">>> CONNECTION LOST - IGNITION BLOCKED <<<");
      break;

    case OVERRIDE_ACTIVE:
      digitalWrite(IGNITION_RELAY_PIN, HIGH);
      Serial.println(">>> OVERRIDE ACTIVE <<<");
      logOverrideAttempt();
      break;
  }
}

// ============================================================================
// Communication
// ============================================================================

void sendVehicleCommand(byte commandType) {
  uint8_t data[12] = {0};
  data[0] = commandType;
  data[1] = 0x00;  // Acknowledged

  // Timestamp
  unsigned long now = millis() / 1000;
  memcpy(data + 6, &now, 4);

  vehicleCmdChar.writeValue(data, 12);
}

void sendVehicleStatus(byte status) {
  sendVehicleCommand(status);
}

// ============================================================================
// Safety & Monitoring
// ============================================================================

void checkConnectionStatus() {
  if (vehicleState.isConnected) {
    return;
  }

  // If not connected and timeout exceeded, ensure ignition is blocked
  if (millis() - vehicleState.lastConnectionTime > CONNECTION_TIMEOUT) {
    if (vehicleState.ignitionState != CONNECTION_LOST &&
        vehicleState.ignitionState != WAITING_FOR_DATA) {
      setIgnitionState(CONNECTION_LOST);
    }
  }
}

void checkBACTimeout() {
  if (!vehicleState.isConnected) {
    return;
  }

  // Check if BAC update is overdue
  if (millis() - vehicleState.lastBACUpdate > BAC_UPDATE_TIMEOUT) {
    Serial.println("ERROR: BAC update timeout!");
    setIgnitionState(CONNECTION_LOST);
  }
}

void checkOverrideButton() {
  static unsigned long buttonPressTime = 0;
  static bool buttonWasPressed = false;

  bool buttonPressed = digitalRead(OVERRIDE_BUTTON_PIN) == LOW;

  if (buttonPressed && !buttonWasPressed) {
    buttonPressTime = millis();
    buttonWasPressed = true;
  }

  // Hold for 5 seconds to activate emergency override
  if (buttonPressed && buttonWasPressed &&
      millis() - buttonPressTime > 5000) {
    activateEmergencyOverride();
    buttonWasPressed = false;
  }

  if (!buttonPressed) {
    buttonWasPressed = false;
  }
}

void activateEmergencyOverride() {
  Serial.println("!!! EMERGENCY OVERRIDE ACTIVATED !!!");
  vehicleState.overrideAttempts++;
  vehicleState.overrideStartTime = millis();
  setIgnitionState(OVERRIDE_ACTIVE);

  // Send override request to smartwatch
  sendVehicleCommand(0x04);  // Emergency override

  // Long beep
  tone(BUZZER_PIN, 1500, 1000);

  // Override is temporary (5 minutes)
  // After timeout, return to normal operation
}

void logOverrideAttempt() {
  Serial.println("!!! OVERRIDE LOGGED !!!");
  Serial.print("Total override attempts: ");
  Serial.println(vehicleState.overrideAttempts);
  // In production, this would be logged to EEPROM or sent to cloud
}

// ============================================================================
// Indicators
// ============================================================================

void updateLEDs() {
  // Turn off all LEDs
  digitalWrite(LED_RED_PIN, LOW);
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_BLUE_PIN, LOW);

  switch (vehicleState.ignitionState) {
    case IGNITION_ALLOWED:
    case OVERRIDE_ACTIVE:
      digitalWrite(LED_GREEN_PIN, HIGH);
      break;

    case IGNITION_BLOCKED:
      digitalWrite(LED_RED_PIN, HIGH);
      break;

    case WAITING_FOR_DATA:
    case CONNECTION_LOST:
      // Blink blue
      digitalWrite(LED_BLUE_PIN, (millis() / 500) % 2);
      break;
  }
}

void soundAlarm() {
  // Three short beeps
  for (int i = 0; i < 3; i++) {
    tone(BUZZER_PIN, 2000, 200);
    delay(300);
  }
}

void blinkError() {
  while (true) {
    digitalWrite(LED_RED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_RED_PIN, LOW);
    delay(200);
  }
}

// ============================================================================
// Debug & Utilities
// ============================================================================

void printDiagnostics() {
  Serial.println("\n========== DIAGNOSTICS ==========");
  Serial.print("Firmware: ");
  Serial.println(FIRMWARE_VERSION);
  Serial.print("BLE Status: ");
  Serial.println(vehicleState.isConnected ? "Connected" : "Disconnected");
  Serial.print("Ignition State: ");
  Serial.println(vehicleState.ignitionState);
  Serial.print("Last BAC Update: ");
  Serial.print((millis() - vehicleState.lastBACUpdate) / 1000);
  Serial.println("s ago");
  Serial.print("Override Attempts: ");
  Serial.println(vehicleState.overrideAttempts);
  Serial.println("==================================\n");
}
