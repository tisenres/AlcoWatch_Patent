# AlcoWatch Simulation - No Hardware Required

## Quick Start (30 seconds)

### Option 1: Using the Launcher Script (EASIEST)

From the project root directory:

```bash
./RUN_SIMULATION.sh
```

### Option 2: Direct Python Execution

```bash
cd arduino/simulation
python3 run_simulation.py
```

That's it! No installation required (Python 3 is all you need).

---

## What This Simulator Does

This simulation runs the **complete AlcoWatch system** without any physical hardware:

✅ **Smartwatch Component:**
- Simulates PPG sensor (heart rate)
- Simulates EDA sensor (skin conductance)
- Simulates temperature sensor
- Runs AI/ML BAC estimation
- Sends BLE updates every 10 seconds

✅ **Arduino Vehicle Component:**
- Receives BAC data
- Processes ignition control logic
- Shows LED status (Red/Green/Blue)
- Triggers buzzer alerts
- Detects tamper attempts
- Monitors connection timeouts

---

## Test Scenarios Available

### 1. Sober Driver Test
Tests normal operation with low BAC levels (0.01-0.02 g/dL).
- **Expected:** Green LED, Ignition ALLOWED

### 2. Intoxicated Driver Test ⭐ (Demonstrated above)
Simulates drinking progression: sober → 1 drink → 2 drinks → peak.
- **Expected:** Starts GREEN, turns RED when BAC > 0.08, buzzer sounds

### 3. Tamper Detection Test
Simulates watch removal while driving.
- **Expected:** Immediate RED LED, Ignition BLOCKED

### 4. Realistic Drinking Scenario
Full drinking cycle: sober → drinking → peak → metabolizing → sobering.
- **Expected:** Dynamic state changes based on BAC curve

### 5. Safety Edge Cases
Tests boundary conditions (0.075, 0.085, 0.15 g/dL).
- **Expected:** Correct threshold detection

### 6. Run ALL Scenarios (Demo Mode)
Runs all 5 scenarios sequentially.
- **Duration:** ~5 minutes

---

## How to Use

### Interactive Mode

1. Run the simulator:
   ```bash
   python3 run_simulation.py
   ```

2. Choose a scenario (1-6):
   ```
   Select Test Scenario:
     1. Sober Driver Test
     2. Intoxicated Driver Test
     3. Tamper Detection Test
     4. Realistic Drinking Scenario
     5. Safety Edge Cases
     6. Run ALL scenarios (demo mode)
     q. Quit

   Enter choice (1-6 or q): 2
   ```

3. Watch the simulation run with real-time output showing:
   - Smartwatch sensor data
   - AI BAC estimation
   - Vehicle response
   - LED status
   - Buzzer alerts

### Understanding the Output

```
[SMARTWATCH]
  Sensors: HR=69.7 bpm, EDA=3.45 µS, Temp=33.9°C
  AI Model: BAC=0.018 g/dL (confidence: 89.8%)
  Alert Level: SAFE

[VEHICLE MODULE]
  Received BAC: 0.018 g/dL
  Watch worn: True
  LED: 🟢 GREEN
  ✓ BAC within safe limits
  ✓ IGNITION: ALLOWED
```

**Legend:**
- 🟢 GREEN = Ignition ALLOWED (safe to drive)
- 🔴 RED = Ignition BLOCKED (BAC too high or tamper)
- 🔵 BLUE = Connecting (not shown in this simulator)
- 🔊 BUZZER = Audio alert when BAC exceeds limit

---

## Validation Results

After running the simulation, you'll see:

```
✓ System validated without hardware
✓ All components working correctly
✓ Safety features operational

Final Vehicle State:
  Ignition: BLOCKED (or ALLOWED)
  Last BAC update: X seconds ago
```

This confirms the entire software system is working correctly!

---

## What Gets Tested

| Feature | Tested |
|---------|--------|
| Sensor data collection | ✅ |
| AI BAC estimation | ✅ |
| BLE communication | ✅ |
| Ignition control logic | ✅ |
| Legal limit detection (0.08 g/dL) | ✅ |
| Tamper detection | ✅ |
| Connection timeout | ✅ |
| Alert levels | ✅ |
| LED status indicators | ✅ |
| Buzzer alerts | ✅ |

---

## Requirements

**Minimal:**
- Python 3.6+ (asyncio is built-in)
- Terminal/command line

**No additional packages needed!** The simulator uses only Python standard library.

---

## Advantages Over Hardware Testing

✅ **Instant Testing** - No hardware setup required
✅ **Repeatable** - Same scenarios every time
✅ **Safe** - No real alcohol consumption needed
✅ **Fast** - Complete test suite in minutes
✅ **Comprehensive** - Test edge cases easily
✅ **Free** - No hardware costs

---

## Example Output (Intoxicated Driver Test)

```
► After 2 drinks
  Duration: 30 seconds

[SMARTWATCH]
  Sensors: HR=70.1 bpm, EDA=3.84 µS, Temp=33.9°C
  AI Model: BAC=0.095 g/dL (confidence: 89.1%)
  Alert Level: DANGER

[VEHICLE MODULE]
  Received BAC: 0.095 g/dL
  Watch worn: True
  LED: 🔴 RED
  🔊 BUZZER: ♪♪♪ Alarm sounding
  🚨 ALERT: BAC over legal limit (0.08 g/dL)
  🔒 IGNITION: BLOCKED
```

---

## Next Steps After Simulation

Once you've validated the software works:

1. **Deploy to real hardware:**
   - Upload Arduino firmware to Arduino Nano 33 BLE
   - Build Wear OS app in Android Studio
   - Test with physical devices

2. **Real-world testing:**
   - Collect real sensor data
   - Validate BAC estimation accuracy
   - Conduct pilot studies

3. **Production deployment:**
   - Professional hardware installation
   - Regulatory approval
   - Clinical validation

---

## Troubleshooting

**Problem:** Script won't run
**Solution:** Make sure you have Python 3.6+
```bash
python3 --version
```

**Problem:** Permission denied
**Solution:** Make script executable
```bash
chmod +x run_simulation.py
```

**Problem:** Want to change test durations
**Solution:** Edit the scenario data in `run_simulation.py` (lines 120-160)

---

## Architecture

```
Smartwatch Simulator          Vehicle Simulator
┌─────────────────┐          ┌──────────────────┐
│ Sensor Data     │          │ BLE Receiver     │
│ ├─ PPG (HR)     │  ────>   │ ├─ BAC Processing│
│ ├─ EDA          │  BLE     │ ├─ Logic Control │
│ └─ Temperature  │  Data    │ └─ Ignition Relay│
│                 │          │                  │
│ AI Inference    │          │ LED Indicators   │
│ └─ BAC Est.     │          │ └─ Red/Green/Blue│
└─────────────────┘          └──────────────────┘
```

---

## Files

- `run_simulation.py` - Main simulator (400+ lines)
- `ble_simulator.py` - Original BLE tester (also works)
- `wokwi_diagram.json` - Hardware diagram for Wokwi
- `README_SIMULATION.md` - This file

---

## Success Criteria

After running simulations, you should see:

✅ **Sober driver:** Ignition stays ALLOWED
✅ **Intoxicated driver:** Ignition switches to BLOCKED at 0.08 g/dL
✅ **Tamper:** Ignition BLOCKS immediately when watch removed
✅ **Realistic scenario:** Proper state transitions throughout drinking cycle
✅ **Edge cases:** Correct behavior at threshold boundaries

If all scenarios pass → **Software implementation validated!**

---

## Questions?

See main documentation:
- `docs/QUICK_START.md` - 30-minute setup guide
- `docs/IMPLEMENTATION_GUIDE.md` - Complete system guide
- `docs/SYSTEM_SUMMARY.md` - Technical details

---

**Ready to test? Run this now:**

```bash
python3 run_simulation.py
```

Choose scenario **2** (Intoxicated Driver Test) to see the system block ignition when BAC exceeds 0.08 g/dL!
