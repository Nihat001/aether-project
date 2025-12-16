# src/aether/dependencies.py

from __future__ import annotations

from typing import Optional

from .sensor_manager import SensorManager
from .visualization import MapVisualizer
from .temporal_visualization import TemporalVisualizer

_sensor_manager: Optional[SensorManager] = None
_map_visualizer: Optional[MapVisualizer] = None
_temporal_visualizer: Optional[TemporalVisualizer] = None


def set_services(
    manager: SensorManager,
    map_visualizer: MapVisualizer,
    temporal_visualizer: TemporalVisualizer,
) -> None:
    global _sensor_manager, _map_visualizer, _temporal_visualizer
    _sensor_manager = manager
    _map_visualizer = map_visualizer
    _temporal_visualizer = temporal_visualizer


def get_sensor_manager() -> SensorManager:
    if _sensor_manager is None:
        raise RuntimeError("SensorManager not initialized")
    return _sensor_manager


def get_map_visualizer() -> MapVisualizer:
    if _map_visualizer is None:
        raise RuntimeError("MapVisualizer not initialized")
    return _map_visualizer


def get_temporal_visualizer() -> TemporalVisualizer:
    if _temporal_visualizer is None:
        raise RuntimeError("TemporalVisualizer not initialized")
    return _temporal_visualizer
