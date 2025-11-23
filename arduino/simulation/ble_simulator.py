"""
BLE Communication Simulator for AlcoWatch
Simulates smartwatch BLE peripheral communicating with Arduino vehicle module
"""

import asyncio
import struct
import time
from typing import Optional
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic


class BLESimulator:
    """
    Simulates AlcoWatch smartwatch BLE communication
    Used for testing Arduino vehicle module without physical smartwatch
    """

    # BLE UUIDs
    SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
    BAC_STATUS_UUID = "12345678-1234-5678-1234-56789abcdef1"
    VEHICLE_CMD_UUID = "12345678-1234-5678-1234-56789abcdef2"
    SYSTEM_STATUS_UUID = "12345678-1234-5678-1234-56789abcdef3"

    def __init__(self):
        self.client: Optional[BleakClient] = None
        self.is_connected = False
        self.device_address = None

    async def scan_for_vehicle(self, timeout: float = 10.0):
        """Scan for AlcoWatch vehicle module"""
        print(f"Scanning for AlcoWatch vehicle module (timeout: {timeout}s)...")

        devices = await BleakScanner.discover(timeout=timeout)

        for device in devices:
            if "AlcoWatch" in (device.name or ""):
                print(f"Found AlcoWatch device: {device.name} ({device.address})")
                self.device_address = device.address
                return device

        print("No AlcoWatch vehicle module found")
        return None

    async def connect(self, address: Optional[str] = None):
        """Connect to vehicle module"""
        if address:
            self.device_address = address

        if not self.device_address:
            print("ERROR: No device address specified")
            return False

        try:
            print(f"Connecting to {self.device_address}...")
            self.client = BleakClient(self.device_address)
            await self.client.connect()
            self.is_connected = True
            print("Connected successfully!")

            # Subscribe to vehicle commands
            await self.client.start_notify(
                self.VEHICLE_CMD_UUID,
                self._vehicle_command_handler
            )

            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect from vehicle module"""
        if self.client and self.is_connected:
            await self.client.disconnect()
            self.is_connected = False
            print("Disconnected")

    async def send_bac_status(
        self,
        bac_value: float,
        alert_level: int,
        confidence: int,
        watch_worn: bool = True,
        sensor_quality: bool = True,
        battery_low: bool = False
    ):
        """
        Send BAC status update to vehicle

        Args:
            bac_value: BAC in g/dL (e.g., 0.08)
            alert_level: 0=SAFE, 1=WARNING, 2=DANGER, 3=CRITICAL
            confidence: Confidence percentage (0-100)
            watch_worn: Whether watch is being worn
            sensor_quality: Whether sensor quality is good
            battery_low: Whether battery is low
        """
        if not self.is_connected:
            print("ERROR: Not connected")
            return

        # Build BAC status packet (20 bytes)
        timestamp = int(time.time() * 1000)  # milliseconds

        # Flags byte
        flags = 0
        if watch_worn:
            flags |= 0x01
        if sensor_quality:
            flags |= 0x04
        if battery_low:
            flags |= 0x08

        # Pack data
        data = struct.pack(
            '<Qfbbbxxxxx',
            timestamp,  # 8 bytes: timestamp
            bac_value,  # 4 bytes: BAC value
            alert_level,  # 1 byte: alert level
            confidence,  # 1 byte: confidence
            flags  # 1 byte: flags
            # 5 bytes: MAC (filled with zeros for simulation)
        )

        try:
            await self.client.write_gatt_char(self.BAC_STATUS_UUID, data)
            print(f"Sent BAC status: {bac_value:.3f} g/dL (Alert: {alert_level})")
        except Exception as e:
            print(f"Failed to send BAC status: {e}")

    async def send_system_status(
        self,
        battery_level: float,
        watch_worn: bool,
        last_bac_update: int
    ):
        """Send system status update"""
        if not self.is_connected:
            print("ERROR: Not connected")
            return

        # Build system status packet (16 bytes)
        device_status = 0  # Operational
        connection_quality = 95
        tamper_status = 0 if watch_worn else 1

        data = struct.pack(
            '<bfIbbxxxxx',
            device_status,
            battery_level,
            last_bac_update,
            connection_quality,
            tamper_status
        )

        try:
            await self.client.write_gatt_char(self.SYSTEM_STATUS_UUID, data)
            print(f"Sent system status (Battery: {battery_level:.1f}%)")
        except Exception as e:
            print(f"Failed to send system status: {e}")

    def _vehicle_command_handler(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        """Handle vehicle commands"""
        if len(data) < 1:
            return

        command_type = data[0]

        commands = {
            0x00: "ALLOW_IGNITION",
            0x01: "BLOCK_IGNITION",
            0x02: "REQUEST_VERIFICATION",
            0x03: "OVERRIDE_REQUEST",
            0x04: "EMERGENCY_OVERRIDE"
        }

        command_name = commands.get(command_type, f"UNKNOWN({command_type})")
        print(f"<< Received vehicle command: {command_name}")

    async def simulate_sober_driver(self, duration: int = 60):
        """Simulate a sober driver (BAC < 0.05)"""
        print(f"\n=== Simulating SOBER driver for {duration} seconds ===\n")

        start_time = time.time()
        update_count = 0

        while time.time() - start_time < duration:
            bac = 0.02 + (0.01 * (update_count % 3))  # Vary slightly: 0.02-0.04
            await self.send_bac_status(
                bac_value=bac,
                alert_level=0,  # SAFE
                confidence=95,
                watch_worn=True,
                sensor_quality=True
            )

            update_count += 1
            await asyncio.sleep(30)  # Update every 30 seconds

    async def simulate_intoxicated_driver(self, duration: int = 60):
        """Simulate an intoxicated driver (BAC > 0.08)"""
        print(f"\n=== Simulating INTOXICATED driver for {duration} seconds ===\n")

        start_time = time.time()
        update_count = 0

        while time.time() - start_time < duration:
            bac = 0.10 + (0.02 * (update_count % 3))  # Vary: 0.10-0.14
            await self.send_bac_status(
                bac_value=bac,
                alert_level=2,  # DANGER
                confidence=92,
                watch_worn=True,
                sensor_quality=True
            )

            update_count += 1
            await asyncio.sleep(30)

    async def simulate_drinking_scenario(self):
        """Simulate realistic drinking scenario: sober -> intoxicated -> sobering"""
        print("\n=== Simulating REALISTIC drinking scenario ===\n")

        scenarios = [
            ("Baseline (Sober)", 0.01, 0, 30),
            ("One drink", 0.03, 0, 30),
            ("Two drinks", 0.06, 1, 30),
            ("Three drinks", 0.09, 2, 30),
            ("Peak intoxication", 0.12, 2, 60),
            ("Metabolizing", 0.09, 2, 30),
            ("Sobering up", 0.06, 1, 30),
            ("Near sober", 0.03, 0, 30),
        ]

        for scenario_name, bac, alert_level, duration in scenarios:
            print(f"\n--- {scenario_name}: BAC={bac:.2f} g/dL ---")

            start = time.time()
            while time.time() - start < duration:
                await self.send_bac_status(
                    bac_value=bac,
                    alert_level=alert_level,
                    confidence=90,
                    watch_worn=True,
                    sensor_quality=True
                )
                await asyncio.sleep(10)

    async def simulate_tamper_detection(self):
        """Simulate watch removal (tamper)"""
        print("\n=== Simulating TAMPER scenario (watch removed) ===\n")

        # Normal operation
        print("Normal operation...")
        for _ in range(3):
            await self.send_bac_status(
                bac_value=0.03,
                alert_level=0,
                confidence=95,
                watch_worn=True,
                sensor_quality=True
            )
            await asyncio.sleep(10)

        # Watch removed
        print("\n!!! Watch removed !!!")
        for _ in range(5):
            await self.send_bac_status(
                bac_value=0.03,
                alert_level=0,
                confidence=50,
                watch_worn=False,  # Tamper detected
                sensor_quality=False
            )
            await asyncio.sleep(10)

        # Watch worn again
        print("\nWatch worn again")
        for _ in range(3):
            await self.send_bac_status(
                bac_value=0.03,
                alert_level=0,
                confidence=95,
                watch_worn=True,
                sensor_quality=True
            )
            await asyncio.sleep(10)


async def interactive_mode():
    """Interactive testing mode"""
    simulator = BLESimulator()

    # Scan and connect
    device = await simulator.scan_for_vehicle(timeout=10.0)
    if not device:
        print("No device found. Make sure Arduino is running.")
        return

    if not await simulator.connect():
        print("Connection failed")
        return

    print("\n" + "=" * 50)
    print("AlcoWatch BLE Simulator - Interactive Mode")
    print("=" * 50)
    print("\nCommands:")
    print("  1 - Simulate sober driver (60s)")
    print("  2 - Simulate intoxicated driver (60s)")
    print("  3 - Simulate realistic drinking scenario")
    print("  4 - Simulate tamper detection")
    print("  5 - Send custom BAC value")
    print("  q - Quit")
    print()

    try:
        while True:
            choice = input("Enter command: ").strip().lower()

            if choice == '1':
                await simulator.simulate_sober_driver(60)
            elif choice == '2':
                await simulator.simulate_intoxicated_driver(60)
            elif choice == '3':
                await simulator.simulate_drinking_scenario()
            elif choice == '4':
                await simulator.simulate_tamper_detection()
            elif choice == '5':
                try:
                    bac = float(input("Enter BAC value (g/dL): "))
                    alert = 0 if bac < 0.05 else (1 if bac < 0.08 else 2)
                    await simulator.send_bac_status(bac, alert, 90)
                except ValueError:
                    print("Invalid BAC value")
            elif choice == 'q':
                break
            else:
                print("Unknown command")

    finally:
        await simulator.disconnect()


async def automated_test():
    """Automated test sequence"""
    simulator = BLESimulator()

    device = await simulator.scan_for_vehicle(timeout=10.0)
    if not device:
        print("No device found")
        return

    if not await simulator.connect():
        return

    try:
        # Run all scenarios
        await simulator.simulate_sober_driver(60)
        await asyncio.sleep(5)

        await simulator.simulate_intoxicated_driver(60)
        await asyncio.sleep(5)

        await simulator.simulate_tamper_detection()
        await asyncio.sleep(5)

        await simulator.simulate_drinking_scenario()

    finally:
        await simulator.disconnect()


if __name__ == "__main__":
    print("AlcoWatch BLE Simulator")
    print("=" * 50)
    print("\nMode:")
    print("  1 - Interactive mode")
    print("  2 - Automated test")
    print()

    mode = input("Select mode (1/2): ").strip()

    if mode == '1':
        asyncio.run(interactive_mode())
    elif mode == '2':
        asyncio.run(automated_test())
    else:
        print("Invalid mode selected")
