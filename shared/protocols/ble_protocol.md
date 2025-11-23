# AlcoWatch BLE Communication Protocol Specification

## Overview
Secure Bluetooth Low Energy (BLE) protocol for communication between the Wear OS smartwatch and Arduino vehicle control module.

## Protocol Version
**Version:** 1.0
**Last Updated:** 2025-11-23

## Architecture

### Roles
- **Peripheral (Server):** Wear OS Smartwatch - broadcasts BAC data
- **Central (Client):** Arduino Vehicle Module - receives BAC data and sends status

### Security
- **Encryption:** AES-256-GCM
- **Authentication:** Mutual authentication with pre-shared keys
- **Anti-replay:** Timestamp and nonce-based protection
- **Pairing:** Secure pairing with PIN or biometric confirmation

## GATT Services and Characteristics

### Service: AlcoWatch BAC Monitoring Service
**UUID:** `12345678-1234-5678-1234-56789abcdef0`

#### Characteristic 1: BAC Status (Read/Notify)
**UUID:** `12345678-1234-5678-1234-56789abcdef1`
**Properties:** Read, Notify
**Security:** Encrypted, Authenticated

**Data Format (20 bytes):**
```
Byte 0-7:   Timestamp (Unix epoch, 64-bit)
Byte 8-11:  BAC Value (float, 32-bit) in g/dL
Byte 12:    Alert Level (uint8)
            0x00 = SAFE
            0x01 = WARNING
            0x02 = DANGER
            0x03 = CRITICAL
Byte 13:    Confidence (uint8, 0-100%)
Byte 14:    Flags (bitfield)
            Bit 0: Wear detected
            Bit 1: Biometric authenticated
            Bit 2: Sensor quality OK
            Bit 3: Battery low
            Bit 4-7: Reserved
Byte 15-19: Message Authentication Code (MAC, first 5 bytes)
```

#### Characteristic 2: Vehicle Command (Read/Write)
**UUID:** `12345678-1234-5678-1234-56789abcdef2`
**Properties:** Read, Write
**Security:** Encrypted, Authenticated

**Data Format (12 bytes):**
```
Byte 0:     Command Type
            0x00 = ALLOW_IGNITION
            0x01 = BLOCK_IGNITION
            0x02 = REQUEST_VERIFICATION
            0x03 = OVERRIDE_REQUEST
            0x04 = EMERGENCY_OVERRIDE
Byte 1:     Status
            0x00 = Acknowledged
            0x01 = Rejected
            0x02 = Pending
Byte 2-5:   Override Code (32-bit, if applicable)
Byte 6-9:   Timestamp (Unix epoch, 32-bit)
Byte 10-11: Checksum (CRC-16)
```

#### Characteristic 3: System Status (Read/Notify)
**UUID:** `12345678-1234-5678-1234-56789abcdef3`
**Properties:** Read, Notify
**Security:** Encrypted, Authenticated

**Data Format (16 bytes):**
```
Byte 0:     Device Status
            0x00 = Operational
            0x01 = Error
            0x02 = Calibrating
            0x03 = Low Battery
Byte 1-4:   Battery Level (float, 0-100%)
Byte 5-8:   Last BAC Update (Unix timestamp, 32-bit)
Byte 9:     Connection Quality (uint8, 0-100%)
Byte 10:    Tamper Status
            0x00 = No tamper
            0x01 = Watch removed
            0x02 = Signal spoofing detected
            0x03 = Unauthorized access
Byte 11-15: Reserved
```

## Communication Flow

### 1. Initialization and Pairing
```
Smartwatch                          Arduino Module
    |                                     |
    |-------- Advertise BLE ------------>|
    |                                     |
    |<------- Connect Request ------------|
    |                                     |
    |--- Challenge (Random Nonce) ------>|
    |                                     |
    |<-- Response (Encrypted w/ PSK) -----|
    |                                     |
    |--- Confirmation (Session Key) ---->|
    |                                     |
    [Secure Channel Established]
```

### 2. Normal Operation (BAC Monitoring)
```
Smartwatch                          Arduino Module
    |                                     |
    |--- BAC Update (Notify) ----------->|
    |    [Every 30 seconds]               |
    |                                     |
    |                                     |- Check BAC Value
    |                                     |- Update Ignition Status
    |                                     |
    |<-- Status Acknowledgment -----------|
    |                                     |
```

### 3. Over-Limit Detection
```
Smartwatch                          Arduino Module
    |                                     |
    |--- BAC Update (DANGER) ----------->|
    |                                     |
    |                                     |- Block Ignition
    |                                     |- Activate Warning
    |                                     |
    |<-- Command: BLOCK_IGNITION ---------|
    |                                     |
    |--- Acknowledgment ---------------->|
    |                                     |
    |                                     [Ignition Disabled]
```

### 4. Override Request (Emergency)
```
User/Mobile App                Smartwatch            Arduino Module
    |                             |                        |
    |-- Request Override -------->|                        |
    |   [With Auth Code]          |                        |
    |                             |                        |
    |                             |- Verify Biometric      |
    |                             |- Check BAC             |
    |                             |                        |
    |                             |--- OVERRIDE_REQUEST -->|
    |                             |    [With Code]         |
    |                             |                        |
    |                             |                        |- Verify Code
    |                             |                        |- Log Override
    |                             |                        |- Enable Ignition
    |                             |                        |  (Temporary)
    |                             |<-- ALLOW_IGNITION -----|
    |                             |                        |
```

### 5. Tamper Detection
```
Smartwatch                          Arduino Module
    |                                     |
    |- Detect Watch Removal               |
    |                                     |
    |--- Status Update (Tamper) -------->|
    |                                     |
    |                                     |- Block Ignition
    |                                     |- Send Alert
    |                                     |
    |<-- REQUEST_VERIFICATION ------------|
    |                                     |
```

## Error Handling

### Connection Loss
- **Behavior:** Arduino assumes DANGER state and blocks ignition
- **Timeout:** 60 seconds without BAC update
- **Recovery:** Automatic reconnection with re-authentication

### Invalid Data
- **Behavior:** Reject packet, request retransmission
- **Max Retries:** 3 attempts
- **Fallback:** Enter safe mode (block ignition)

### Authentication Failure
- **Behavior:** Disconnect immediately
- **Logging:** Log attempt with timestamp
- **Recovery:** Require full re-pairing

## Timing Requirements

- **BAC Update Frequency:** Every 30 seconds during normal operation
- **Connection Timeout:** 60 seconds max
- **Command Response Time:** < 1 second
- **Reconnection Attempt:** Every 5 seconds after disconnect

## Security Considerations

### Threat Model
1. **Replay Attacks:** Mitigated by timestamps and nonces
2. **MITM Attacks:** Prevented by encryption and mutual authentication
3. **Spoofing:** Detected through biometric verification
4. **Jamming:** Logged and reported, fail-safe to blocked state

### Key Management
- **Pre-Shared Key (PSK):** 256-bit key established during initial pairing
- **Session Keys:** Rotated every 24 hours
- **Key Storage:** Secure element on both devices

### Encryption Details
- **Algorithm:** AES-256-GCM
- **IV/Nonce:** 96-bit random, unique per message
- **MAC:** 128-bit authentication tag

## Testing Procedures

### Protocol Compliance Tests
1. Connection establishment and pairing
2. Normal BAC update transmission
3. Over-limit detection and response
4. Override request handling
5. Tamper detection
6. Connection loss recovery
7. Invalid data handling
8. Security attack scenarios

### Performance Metrics
- Latency: < 100ms for BAC updates
- Packet loss: < 1% under normal conditions
- Battery impact: < 5% additional drain
- Range: Minimum 5 meters reliable connection

## Implementation Notes

### Smartwatch (Peripheral)
- Use Android BLE Peripheral APIs
- Implement GATT server with defined characteristics
- Handle notifications efficiently to minimize battery drain
- Implement secure storage for PSK

### Arduino (Central)
- Use Arduino BLE library or ESP32 BLE
- Implement GATT client
- Handle connection state machine
- Implement watchdog timer for connection monitoring

## Future Enhancements (v2.0)
- Multi-device support (multiple vehicles)
- Cloud backup of override attempts
- Extended biometric authentication (fingerprint)
- Adaptive update frequency based on BAC trends
- Vehicle telemetry integration (speed, location)
