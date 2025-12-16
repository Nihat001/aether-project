# src/aether/sensor_manager.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

import pandas as pd

from .sensor import SensorInfo, SensorReading
from .data_cleaning import DataCleaner
from . import persistance


class UnauthorizedSensorError(Exception):
    pass


class InvalidReadingError(Exception):
    def __init__(self, errors: List[str]):
        super().__init__("Invalid reading")
        self.errors = errors


class SensorManager:
    """
    Core business logic: ingestion, status, data aggregation.
    Framework-agnostic; no FastAPI imports here.
    """

    def __init__(
        self,
        config: dict,
        sensors: Dict[str, SensorInfo],
        historical_df: pd.DataFrame,
        realtime_storage_path: str,
    ):
        self._config = config
        self._sensors = sensors
        self._historical_df = historical_df
        self._realtime_storage_path = realtime_storage_path

        self._start_time = datetime.now(timezone.utc)
        self._total_readings = 0
        self._last_update: Optional[datetime] = None

        self._realtime: List[dict] = persistance.load_realtime_storage(
            realtime_storage_path
        )
        # hydrate counts and last_update from realtime if available
        if self._realtime:
            self._total_readings = len(self._realtime)
            last_ts = max(
                datetime.fromisoformat(r["timestamp"]) for r in self._realtime
            )
            self._last_update = last_ts
            # hydrate sensor objects with most recent reading per sensor
            for rec in self._realtime:
                sid = rec.get("sensor_id")
                if sid in self._sensors:
                    try:
                        ts = datetime.fromisoformat(rec.get("timestamp"))
                    except Exception:
                        continue
                    current_last = self._sensors[sid].last_update
                    if (current_last is None) or (ts > current_last):
                        # use SensorReading.from_dict for robust parsing
                        try:
                            reading = SensorReading.from_dict(rec)
                        except Exception:
                            # fallback to manual construction
                            reading = SensorReading(sid, rec.get("readings", {}), ts)
                        self._sensors[sid].last_reading = reading
                        self._sensors[sid].last_update = ts

    # ------------ ingestion ------------

    def ingest(self, sensor_id: str, readings: Dict[str, float]) -> SensorReading:
        if sensor_id not in self._sensors:
            raise UnauthorizedSensorError(sensor_id)

        ok, errors = DataCleaner.validate_readings(readings)
        if not ok:
            raise InvalidReadingError(errors)

        now = datetime.now(timezone.utc)
        reading = SensorReading(sensor_id, readings, now)

        # Store raw in memory + JSON
        record = reading.to_dict()
        self._realtime.append(record)
        persistance.save_realtime_storage(self._realtime_storage_path, self._realtime)

        # Update sensor state
        info = self._sensors[sensor_id]
        info.last_reading = reading
        info.last_update = now

        self._total_readings += 1
        self._last_update = now

        return reading

    # ------------ status ------------

    def get_status(self) -> Dict[str, Any]:
        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        active_sensors = sum(
            1 for s in self._sensors.values() if s.last_reading is not None
        )
        status = "healthy"

        return {
            "status": status,
            "uptime_seconds": uptime,
            "active_sensors": active_sensors,
            "total_readings": self._total_readings,
            "last_update": self._last_update,
        }

    # ------------ map data ------------

    def get_map_dataframe(self) -> pd.DataFrame:
        """
        Build a DataFrame combining sensor location + latest pm25, pm10, no2, o3.
        Falls back to historical latest values if realtime unavailable.
        """
        rows = []
        for sensor in self._sensors.values():
            pm25 = None
            pm10 = None
            no2 = None
            o3 = None
            ts = None

            # Try realtime reading first
            if sensor.last_reading:
                pm25 = sensor.last_reading.readings.get("pm25")
                pm10 = sensor.last_reading.readings.get("pm10")
                no2 = sensor.last_reading.readings.get("no2")
                o3 = sensor.last_reading.readings.get("o3")
                ts = sensor.last_reading.timestamp
            else:
                # Fallback to historical latest values
                hist = self._historical_df[self._historical_df["sensor_id"] == sensor.id]
                if not hist.empty:
                    latest = hist.sort_values("timestamp").iloc[-1]
                    pm25 = None if pd.isna(latest.get("pm25")) else latest.get("pm25")
                    pm10 = None if pd.isna(latest.get("pm10")) else latest.get("pm10")
                    no2 = None if pd.isna(latest.get("no2")) else latest.get("no2")
                    o3 = None if pd.isna(latest.get("o3")) else latest.get("o3")
                    ts = latest.get("timestamp")

            rows.append(
                {
                    "sensor_id": sensor.id,
                    "lat": sensor.latitude,
                    "lon": sensor.longitude,
                    "pm25": pm25,
                    "pm10": pm10,
                    "no2": no2,
                    "o3": o3,
                    "last_update": ts,
                    "province": sensor.metadata.get("province"),
                    "region": sensor.metadata.get("region"),
                }
            )
        return pd.DataFrame(rows)

    # ------------ history ------------

    def get_sensor_history(self, sensor_id: str) -> pd.DataFrame:
        if sensor_id not in self._sensors:
            raise KeyError(sensor_id)

        df = self._historical_df
        hist = df[df["sensor_id"] == sensor_id].sort_values("timestamp")
        if hist.empty:
            raise KeyError(sensor_id)
        return hist

    # ------------ distribution ------------

    def get_distribution_dataframe(self, year: int, month: int) -> pd.DataFrame:
        if not (1 <= month <= 12):
            raise ValueError("Invalid month")

        df = self._historical_df
        df = df.copy()

        df["year"] = df["timestamp"].dt.year
        df["month"] = df["timestamp"].dt.month

        sub = df[(df["year"] == year) & (df["month"] == month)]
        if sub.empty:
            raise KeyError("No data")

        # Map sensor_id -> province from whitelist metadata
        province_map = {
            sid: s.metadata.get("province", "Unknown")
            for sid, s in self._sensors.items()
        }
        sub["province"] = sub["sensor_id"].map(province_map).fillna("Unknown")

        # Categorize by PM2.5 thresholds from config
        thr = self._config["thresholds"]
        safe = thr["pm25_safe"]
        moderate = thr["pm25_moderate"]
        danger = thr["pm25_danger"]

        def categorize(pm25: float) -> str:
            if pd.isna(pm25):
                return "No data"
            if pm25 <= safe:
                return "Safe"
            if pm25 <= moderate:
                return "Moderate"
            if pm25 <= danger:
                return "Unhealthy"
            return "Dangerous"

        sub["category"] = sub["pm25"].apply(categorize)

        # Count per province + category
        counts = (
            sub.groupby(["province", "category"])
            .size()
            .reset_index(name="count")
        )

        # Convert to percentage per province
        total_per_province = counts.groupby("province")["count"].transform("sum")
        counts["percentage"] = counts["count"] / total_per_province * 100
        return counts

    # ------------ helpers ------------

    @property
    def config(self) -> dict:
        return self._config

    @property
    def sensors(self) -> Dict[str, SensorInfo]:
        return self._sensors
