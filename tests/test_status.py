# tests/test_status.py

import os
import pytest
from fastapi.testclient import TestClient

os.environ["PYTHONPATH"] = "src"

from aether.main import app
from aether import dependencies
from aether.sensor_manager import SensorManager
from aether.persistance import load_server_config, load_sensors, load_historical_data
from aether.visualization import MapVisualizer
from aether.temporal_visualization import TemporalVisualizer


@pytest.fixture(scope="module")
def test_client():
    """Initialize services and return test client."""
    config_path = "config/server_config.json"
    sensors_path = "config/sensors.json"
    
    # Load configuration
    config = load_server_config(config_path)
    sensors = load_sensors(sensors_path)
    historical_df = load_historical_data(config["historical_data_file"])
    
    # Initialize services
    manager = SensorManager(
        config=config,
        sensors=sensors,
        historical_df=historical_df,
        realtime_storage_path=config["storage_file"],
    )
    map_visualizer = MapVisualizer(
        map_config=config.get("map_config", {}),
        thresholds=config["thresholds"],
    )
    temporal_visualizer = TemporalVisualizer()
    
    dependencies.set_services(manager, map_visualizer, temporal_visualizer)
    
    return TestClient(app)


def test_status_endpoint(test_client):
    """Test /status endpoint returns 200 with required fields."""
    resp = test_client.get("/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "uptime_seconds" in data
    assert "active_sensors" in data
    assert "total_readings" in data
    assert data["status"] in ["healthy", "degraded"]


def test_status_returns_valid_uptime(test_client):
    """Test that uptime is a non-negative number."""
    resp = test_client.get("/status")
    data = resp.json()
    assert isinstance(data["uptime_seconds"], (int, float))
    assert data["uptime_seconds"] >= 0
