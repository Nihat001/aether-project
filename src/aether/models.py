# src/aether/models.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    sensor_id: str = Field(..., min_length=1)
    readings: Dict[str, float]


class IngestResponse(BaseModel):
    status: str
    message: str
    sensor_id: str
    timestamp: datetime


class StatusResponse(BaseModel):
    status: str
    uptime_seconds: float
    active_sensors: int
    total_readings: int
    last_update: Optional[datetime] = None


class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
