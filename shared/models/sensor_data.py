"""
Shared data models for AlcoWatch system
Defines the structure of sensor data, BAC estimates, and communication messages
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum


class AlertLevel(Enum):
    """BAC alert levels"""
    SAFE = "SAFE"  # BAC < legal limit
    WARNING = "WARNING"  # BAC approaching limit
    DANGER = "DANGER"  # BAC > legal limit
    CRITICAL = "CRITICAL"  # BAC significantly over limit


class VehicleStatus(Enum):
    """Vehicle ignition status"""
    IGNITION_ALLOWED = "IGNITION_ALLOWED"
    IGNITION_BLOCKED = "IGNITION_BLOCKED"
    OVERRIDE_REQUESTED = "OVERRIDE_REQUESTED"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    TAMPER_DETECTED = "TAMPER_DETECTED"


@dataclass
class SensorReading:
    """Raw sensor data from smartwatch"""
    timestamp: datetime
    ppg_value: float  # Photoplethysmography (heart rate/blood flow)
    ppg_quality: float  # Signal quality 0-1
    eda_value: float  # Electrodermal activity (skin conductance in µS)
    temperature: float  # Skin temperature in Celsius
    ambient_temp: Optional[float] = None  # Ambient temperature
    humidity: Optional[float] = None  # Ambient humidity
    device_id: Optional[str] = None

    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'ppg_value': self.ppg_value,
            'ppg_quality': self.ppg_quality,
            'eda_value': self.eda_value,
            'temperature': self.temperature,
            'ambient_temp': self.ambient_temp,
            'humidity': self.humidity,
            'device_id': self.device_id
        }


@dataclass
class BACEstimate:
    """Blood Alcohol Concentration estimation"""
    timestamp: datetime
    bac_value: float  # BAC in g/dL (e.g., 0.08 = 0.08%)
    confidence: float  # Confidence score 0-1
    alert_level: AlertLevel
    sensor_readings: SensorReading
    model_version: str = "v1.0"
    calibration_offset: float = 0.0  # Climate adjustment

    def is_over_limit(self, legal_limit: float = 0.08) -> bool:
        """Check if BAC exceeds legal limit"""
        return self.bac_value > legal_limit

    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'bac_value': self.bac_value,
            'confidence': self.confidence,
            'alert_level': self.alert_level.value,
            'sensor_readings': self.sensor_readings.to_dict(),
            'model_version': self.model_version,
            'calibration_offset': self.calibration_offset
        }


@dataclass
class BiometricAuth:
    """Biometric authentication data"""
    user_id: str
    heartrate_pattern: List[float]  # Heart rate variability pattern
    motion_signature: List[float]  # Movement pattern
    timestamp: datetime
    is_authenticated: bool = False
    confidence: float = 0.0


@dataclass
class BLEMessage:
    """BLE communication message structure"""
    message_type: str  # "BAC_UPDATE", "VEHICLE_STATUS", "OVERRIDE_REQUEST", etc.
    payload: dict
    timestamp: datetime
    sender_id: str
    message_id: str
    encryption_enabled: bool = True
    signature: Optional[str] = None  # Message authentication code

    def to_bytes(self) -> bytes:
        """Convert message to bytes for BLE transmission"""
        import json
        data = {
            'type': self.message_type,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'sender': self.sender_id,
            'id': self.message_id
        }
        return json.dumps(data).encode('utf-8')


@dataclass
class VehicleCommand:
    """Command sent to vehicle control module"""
    command: VehicleStatus
    bac_estimate: Optional[BACEstimate] = None
    override_code: Optional[str] = None
    emergency: bool = False
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ClimateCalibration:
    """Climate-specific calibration parameters"""
    region: str  # e.g., "Central_Asia", "Europe", "North_America"
    base_temp: float  # Base temperature for calibration
    temp_coefficient: float  # Temperature adjustment factor
    humidity_coefficient: float  # Humidity adjustment factor
    altitude: Optional[float] = None  # Altitude in meters

    # Predefined regions
    CENTRAL_ASIA = {
        'region': 'Central_Asia',
        'base_temp': 30.0,
        'temp_coefficient': 0.012,
        'humidity_coefficient': 0.008
    }

    EUROPE = {
        'region': 'Europe',
        'base_temp': 20.0,
        'temp_coefficient': 0.010,
        'humidity_coefficient': 0.006
    }


@dataclass
class UserProfile:
    """User profile for personalized BAC estimation"""
    user_id: str
    age: int
    weight: float  # kg
    height: float  # cm
    gender: str  # "M", "F", "Other"
    bac_baseline: Optional[float] = None  # Baseline BAC when sober
    calibration: Optional[ClimateCalibration] = None
    medical_conditions: List[str] = None

    def __post_init__(self):
        if self.medical_conditions is None:
            self.medical_conditions = []


# Constants
LEGAL_BAC_LIMIT_US = 0.08  # g/dL
LEGAL_BAC_LIMIT_EU = 0.05  # g/dL
LEGAL_BAC_LIMIT_ZERO = 0.02  # Zero tolerance countries

# Sensor sampling rates (Hz)
PPG_SAMPLING_RATE = 64  # 64 Hz typical for smartwatches
EDA_SAMPLING_RATE = 4   # 4 Hz typical for EDA
TEMP_SAMPLING_RATE = 1  # 1 Hz for temperature

# BLE communication
BLE_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
BLE_BAC_CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef1"
BLE_COMMAND_CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef2"
BLE_STATUS_CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef3"
