# src/aether/persistence.py

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .sensor import SensorInfo
from .data_cleaning import DataCleaner

logger = logging.getLogger(__name__)

# WKT regex with named groups, as required
WKT_POINT_PATTERN = re.compile(
    r"POINT\s*\(\s*(?P<lon>-?\d+\.?\d*)\s+(?P<lat>-?\d+\.?\d*)\s*\)",
    re.IGNORECASE,
)


def load_server_config(path: str) -> dict:
    p = Path(path)
    logger.info("Loading server config from %s", p)
    return json.loads(p.read_text(encoding="utf-8"))


def _parse_sensor_location_wkt(location: str) -> Optional[Tuple[float, float]]:
    """
    Parse WKT POINT(lon lat) using regex only.
    Returns (lat, lon) or None if invalid.
    """
    match = WKT_POINT_PATTERN.match(location)
    if not match:
        return None

    lon = float(match.group("lon"))
    lat = float(match.group("lat"))

    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        return None

    return lat, lon


def load_sensors(path: str) -> Dict[str, SensorInfo]:
    """
    Load sensor whitelist from JSON and build SensorInfo objects.
    Invalid WKT is logged and skipped (no crash).
    """
    p = Path(path)
    logger.info("Loading sensors from %s", p)
    items = json.loads(p.read_text(encoding="utf-8"))

    sensors: Dict[str, SensorInfo] = {}
    for entry in items:
        sensor_id = entry["id"]
        wkt = entry["location"]
        metadata = entry.get("metadata", {})

        coords = _parse_sensor_location_wkt(wkt)
        if coords is None:
            logger.warning("Invalid WKT for sensor %s: %s", sensor_id, wkt)
            continue

        lat, lon = coords
        sensors[sensor_id] = SensorInfo(
            sensor_id=sensor_id,
            location=wkt,
            latitude=lat,
            longitude=lon,
            metadata=metadata,
        )

    logger.info("Loaded %d valid sensors", len(sensors))
    return sensors


def load_historical_data(path: str) -> pd.DataFrame:
    p = Path(path)
    logger.info("Loading historical data from %s", p)
    df = pd.read_csv(p)
    cleaned_df, stats = DataCleaner.clean_historical(df)
    logger.info("Historical cleaning stats: %s", stats)
    return cleaned_df


def load_realtime_storage(path: str) -> List[dict]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Realtime storage file %s is corrupt, starting empty.", p)
        return []


def save_realtime_storage(path: str, readings: List[dict]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(readings, indent=2, default=str), encoding="utf-8")
