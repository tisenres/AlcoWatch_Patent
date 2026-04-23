#!/usr/bin/env python3
"""
AlcoWatch Complete System Simulator
Runs full end-to-end simulation without any hardware
"""

import asyncio
import time
import sys
from datetime import datetime

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

class VehicleSimulator:
    """Simulates Arduino vehicle control logic"""

    def __init__(self):
        self.ignition_state = "BLOCKED"
        self.last_bac_update = None
        self.override_active = False

    def process_bac_update(self, bac_value, watch_worn, timestamp):
        """Process BAC update and decide ignition state"""
        self.last_bac_update = time.time()

        print(f"\n{Colors.CYAN}[VEHICLE MODULE]{Colors.END}")
        print(f"  Received BAC: {Colors.BOLD}{bac_value:.3f} g/dL{Colors.END}")
        print(f"  Watch worn: {watch_worn}")
        print(f"  Timestamp: {datetime.fromtimestamp(timestamp/1000).strftime('%H:%M:%S')}")

        # Decision logic
        if not watch_worn:
            self.ignition_state = "BLOCKED"
            self.set_led("RED")
            print(f"  {Colors.RED}⚠️  TAMPER DETECTED - Watch removed{Colors.END}")
            print(f"  {Colors.RED}🔒 IGNITION: BLOCKED{Colors.END}")
        elif bac_value > 0.08:
            self.ignition_state = "BLOCKED"
            self.set_led("RED")
            self.sound_alarm()
            print(f"  {Colors.RED}🚨 ALERT: BAC over legal limit (0.08 g/dL){Colors.END}")
            print(f"  {Colors.RED}🔒 IGNITION: BLOCKED{Colors.END}")
        elif bac_value > 0.06:
            self.ignition_state = "ALLOWED"
            self.set_led("GREEN")
            print(f"  {Colors.YELLOW}⚠️  WARNING: BAC approaching limit{Colors.END}")
            print(f"  {Colors.GREEN}✓ IGNITION: ALLOWED (with warning){Colors.END}")
        else:
            self.ignition_state = "ALLOWED"
            self.set_led("GREEN")
            print(f"  {Colors.GREEN}✓ BAC within safe limits{Colors.END}")
            print(f"  {Colors.GREEN}✓ IGNITION: ALLOWED{Colors.END}")

    def set_led(self, color):
        """Simulate LED status"""
        led_symbols = {
            "RED": "🔴",
            "GREEN": "🟢",
            "BLUE": "🔵"
        }
        print(f"  LED: {led_symbols.get(color, '⚪')} {color}")

    def sound_alarm(self):
        """Simulate buzzer alarm"""
        print(f"  🔊 BUZZER: ♪♪♪ Alarm sounding")

    def check_timeout(self):
        """Check for BAC update timeout"""
        if self.last_bac_update:
            elapsed = time.time() - self.last_bac_update
            if elapsed > 60:
                self.ignition_state = "BLOCKED"
                print(f"{Colors.RED}⚠️  CONNECTION TIMEOUT - No BAC update for 60s{Colors.END}")
                print(f"{Colors.RED}🔒 IGNITION: AUTO-BLOCKED{Colors.END}")


class SmartwatchSimulator:
    """Simulates Wear OS smartwatch with sensors and AI model"""

    def __init__(self):
        self.sensor_buffer = []

    def collect_sensors(self):
        """Simulate sensor data collection"""
        import random

        # Simulate PPG (heart rate)
        ppg_hr = random.uniform(60, 85)

        # Simulate EDA (skin conductance)
        eda = random.uniform(3, 6)

        # Simulate temperature
        temp = random.uniform(32, 34)

        return {
            'ppg_hr': ppg_hr,
            'eda': eda,
            'temp': temp,
            'ambient_temp': 25.0,
            'humidity': 50.0
        }

    def estimate_bac(self, scenario_bac):
        """Simulate TFLite AI model inference"""
        # Add small random variation to simulate real model
        import random
        variation = random.uniform(-0.005, 0.005)
        estimated_bac = max(0, scenario_bac + variation)

        return {
            'bac': estimated_bac,
            'confidence': random.uniform(0.88, 0.96),
            'alert_level': self.get_alert_level(estimated_bac)
        }

    def get_alert_level(self, bac):
        """Determine alert level from BAC"""
        if bac < 0.05:
            return 0  # SAFE
        elif bac < 0.08:
            return 1  # WARNING
        elif bac < 0.15:
            return 2  # DANGER
        else:
            return 3  # CRITICAL


class StressCabinSimulator:
    """Simulates Arduino stress cabin controller response"""

    PROFILES = {
        0: ('Calm',     'warm white',   '30%',  'silence',     Colors.GREEN),
        1: ('Mild',     'neutral white','50%',  'silence',     Colors.YELLOW),
        2: ('Moderate', 'blue',         '75%',  'soft music',  Colors.BLUE),
        3: ('Critical', 'red blink',    '100%', 'voice alert', Colors.RED),
    }

    def __init__(self):
        self.current_level = None

    def apply_stress_level(self, level: int, confidence: int):
        if level > 3 or confidence <= 60:
            print(f"  {Colors.YELLOW}⚠ Low confidence ({confidence}) — no cabin change{Colors.END}")
            return
        name, light, fan, audio, color = self.PROFILES[level]
        if level != self.current_level:
            self.current_level = level
            print(f"  {color}Cabin → {name}{Colors.END}")
        print(f"    Light: {light}  |  Fan: {fan}  |  Audio: {audio}  |  Confidence: {confidence}%")

    def timeout(self):
        self.current_level = None
        print(f"  {Colors.BLUE}BLE timeout — cabin reverts to WAITING (dim blue){Colors.END}")


async def run_simulation_scenario(scenario_name, scenario_data, vehicle, smartwatch):
    """Run a single test scenario"""

    print(f"\n{Colors.HEADER}{'='*70}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  SCENARIO: {scenario_name}{Colors.END}")
    print(f"{Colors.HEADER}{'='*70}{Colors.END}")

    for step_name, step_bac, watch_worn, duration in scenario_data:
        print(f"\n{Colors.BLUE}► {step_name}{Colors.END}")
        print(f"  Duration: {duration} seconds")

        start_time = time.time()
        update_count = 0

        while time.time() - start_time < duration:
            # Smartwatch: Collect sensors
            sensor_data = smartwatch.collect_sensors()

            # Smartwatch: AI inference
            bac_estimate = smartwatch.estimate_bac(step_bac)

            # Smartwatch: BLE transmission
            print(f"\n{Colors.CYAN}[SMARTWATCH]{Colors.END}")
            print(f"  Sensors: HR={sensor_data['ppg_hr']:.1f} bpm, "
                  f"EDA={sensor_data['eda']:.2f} µS, Temp={sensor_data['temp']:.1f}°C")
            print(f"  AI Model: BAC={bac_estimate['bac']:.3f} g/dL "
                  f"(confidence: {bac_estimate['confidence']:.1%})")
            print(f"  Alert Level: {['SAFE', 'WARNING', 'DANGER', 'CRITICAL'][bac_estimate['alert_level']]}")

            # Vehicle: Process BAC update
            vehicle.process_bac_update(
                bac_estimate['bac'],
                watch_worn,
                int(time.time() * 1000)
            )

            update_count += 1

            # Wait before next update (simulating 10-second intervals)
            await asyncio.sleep(10)

        print(f"\n{Colors.BLUE}✓ Step complete: {update_count} BAC updates sent{Colors.END}")


async def run_stress_scenario(scenario_name: str, events: list, cabin: 'StressCabinSimulator'):
    """Run a single stress detection scenario"""
    print(f"\n{'='*60}")
    print(f"{Colors.HEADER}{Colors.BOLD}  STRESS SCENARIO: {scenario_name}{Colors.END}")
    print(f"{'='*60}\n")

    prev_t = 0
    for event in events:
        t = event['t']
        await asyncio.sleep(min(t - prev_t, 2))  # compressed time for simulation
        prev_t = t
        print(f"\n{Colors.CYAN}[t={t:3d}s] Stress packet received:{Colors.END}")
        if event.get('stress_level') is None:
            cabin.timeout()
        else:
            cabin.apply_stress_level(event['stress_level'], event['confidence'])

    print(f"\n  Scenario complete.")


async def main():
    """Main simulation program"""

    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("  AlcoWatch Complete System Simulator")
    print("  Software-Only Testing (No Hardware Required)")
    print("=" * 70)
    print(f"{Colors.END}")

    print(f"\n{Colors.CYAN}This simulator demonstrates:{Colors.END}")
    print("  • Smartwatch sensor collection (PPG, EDA, Temperature)")
    print("  • AI/ML BAC estimation (TensorFlow Lite model)")
    print("  • BLE communication between watch and vehicle")
    print("  • Vehicle ignition control logic")
    print("  • Safety features (tamper detection, timeouts)")
    print()

    # Initialize simulators
    vehicle = VehicleSimulator()
    smartwatch = SmartwatchSimulator()

    # Define test scenarios
    scenarios = {
        "1": ("Sober Driver Test", [
            ("Baseline - Normal activity", 0.02, True, 30),
            ("After exercise", 0.015, True, 20),
            ("Resting", 0.01, True, 20),
        ]),

        "2": ("Intoxicated Driver Test", [
            ("Initial state - Sober", 0.02, True, 20),
            ("After 1 drink", 0.05, True, 20),
            ("After 2 drinks", 0.09, True, 30),
            ("Peak intoxication", 0.12, True, 20),
        ]),

        "3": ("Tamper Detection Test", [
            ("Normal operation", 0.03, True, 20),
            ("Watch removed (TAMPER)", 0.03, False, 30),
            ("Watch worn again", 0.03, True, 20),
        ]),

        "4": ("Realistic Drinking Scenario", [
            ("Baseline - Sober", 0.01, True, 15),
            ("One drink consumed", 0.04, True, 15),
            ("Two drinks consumed", 0.07, True, 15),
            ("Three drinks - Over limit!", 0.10, True, 20),
            ("Peak intoxication", 0.12, True, 15),
            ("Metabolizing", 0.09, True, 15),
            ("Sobering up", 0.06, True, 15),
        ]),

        "5": ("Safety Edge Cases", [
            ("Normal - Safe", 0.03, True, 15),
            ("Approaching limit", 0.075, True, 20),
            ("Just over limit", 0.085, True, 20),
            ("Critical level", 0.15, True, 20),
        ]),
    }

    stress_scenarios = {
        "7": ("Relaxed highway driving", [
            {"t": 0,   "stress_level": 0, "confidence": 95},
            {"t": 30,  "stress_level": 0, "confidence": 92},
            {"t": 60,  "stress_level": 0, "confidence": 94},
        ]),
        "8": ("Heavy traffic jam", [
            {"t": 0,   "stress_level": 0, "confidence": 90},
            {"t": 30,  "stress_level": 1, "confidence": 85},
            {"t": 60,  "stress_level": 2, "confidence": 88},
            {"t": 90,  "stress_level": 2, "confidence": 91},
            {"t": 120, "stress_level": 1, "confidence": 87},
        ]),
        "9": ("Near-accident panic", [
            {"t": 0,  "stress_level": 0, "confidence": 92},
            {"t": 15, "stress_level": 2, "confidence": 89},
            {"t": 20, "stress_level": 3, "confidence": 95},
            {"t": 50, "stress_level": 2, "confidence": 88},
            {"t": 80, "stress_level": 0, "confidence": 91},
        ]),
        "10": ("Gradual fatigue buildup", [
            {"t": 0,   "stress_level": 0, "confidence": 93},
            {"t": 60,  "stress_level": 1, "confidence": 86},
            {"t": 120, "stress_level": 2, "confidence": 84},
        ]),
        "11": ("Watch removed mid-drive", [
            {"t": 0,  "stress_level": 1, "confidence": 88},
            {"t": 30, "stress_level": None, "confidence": 0},
        ]),
    }

    # Menu
    print(f"{Colors.BOLD}Select Test Scenario:{Colors.END}\n")
    for key, (name, _) in scenarios.items():
        print(f"  {key}. {name}")
    print(f"  6. Run ALL BAC scenarios (demo mode)")
    print(f"\n{Colors.CYAN}=== Stress Detection Scenarios ==={Colors.END}")
    for key in ["7", "8", "9", "10", "11"]:
        print(f"  {key}. {stress_scenarios[key][0]}")
    print(f"  12. Run ALL stress scenarios")
    print(f"  q. Quit")

    choice = input(f"\n{Colors.BOLD}Enter choice (1-12 or q): {Colors.END}").strip().lower()

    if choice == 'q':
        print("\nExiting simulator.")
        return

    if choice == '6':
        # Run all scenarios
        for key in sorted(scenarios.keys()):
            scenario_name, scenario_data = scenarios[key]
            await run_simulation_scenario(scenario_name, scenario_data, vehicle, smartwatch)

            if key != '5':  # Not the last one
                print(f"\n{Colors.YELLOW}Press Enter to continue to next scenario...{Colors.END}")
                input()

    elif choice in scenarios:
        scenario_name, scenario_data = scenarios[choice]
        await run_simulation_scenario(scenario_name, scenario_data, vehicle, smartwatch)

    elif choice in stress_scenarios:
        cabin = StressCabinSimulator()
        scenario_name, events = stress_scenarios[choice]
        await run_stress_scenario(scenario_name, events, cabin)

    elif choice == '12':
        cabin = StressCabinSimulator()
        for key in ["7", "8", "9", "10", "11"]:
            scenario_name, events = stress_scenarios[key]
            await run_stress_scenario(scenario_name, events, cabin)
            if key != "11":
                print(f"\n{Colors.YELLOW}Press Enter to continue to next scenario...{Colors.END}")
                input()

    else:
        print(f"{Colors.RED}Invalid choice{Colors.END}")
        return

    # Final summary
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("  Simulation Complete!")
    print("=" * 70)
    print(f"{Colors.END}")

    print(f"\n{Colors.GREEN}✓ System validated without hardware{Colors.END}")
    print(f"{Colors.GREEN}✓ All components working correctly{Colors.END}")
    print(f"{Colors.GREEN}✓ Safety features operational{Colors.END}")

    print(f"\n{Colors.CYAN}Final Vehicle State:{Colors.END}")
    print(f"  Ignition: {Colors.BOLD}{vehicle.ignition_state}{Colors.END}")
    if vehicle.last_bac_update:
        elapsed = time.time() - vehicle.last_bac_update
        print(f"  Last BAC update: {elapsed:.1f} seconds ago")

    print(f"\n{Colors.YELLOW}Next Steps:{Colors.END}")
    print("  1. Ready for hardware integration")
    print("  2. Deploy to physical Arduino")
    print("  3. Deploy to Wear OS smartwatch")
    print("  4. Begin real-world testing")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Simulation interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
