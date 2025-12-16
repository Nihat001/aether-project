# src/aether/sensor.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


class SensorReading:
    """
    Domain model: single sensor reading.
    No validation here – store raw values.
    """

    def __init__(self, sensor_id: str, readings: Dict[str, Any], timestamp: datetime):
        self.sensor_id = sensor_id
        self.readings = readings  # raw, possibly invalid
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "readings": self.readings,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SensorReading":
        """Construct a SensorReading from a dict produced by `to_dict()`.

        Accepts ISO-formatted timestamp strings.
        """
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)

        return cls(sensor_id=data.get("sensor_id"), readings=data.get("readings", {}), timestamp=ts)


class SensorInfo:
    """
    Domain model: static info + last reading for a sensor.
    """

    def __init__(
        self,
        sensor_id: str,
        location: str,
        latitude: float,
        longitude: float,
        metadata: Dict[str, Any],
        last_reading: Optional[SensorReading] = None,
        last_update: Optional[datetime] = None,
    ):
        self.id = sensor_id
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        self.metadata = metadata
        self.last_reading = last_reading
        self.last_update = last_update
