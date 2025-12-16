# tests/test_ingest.py

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Setup test environment
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


def test_ingest_unauthorized(test_client):
    """Test that unauthorized sensor is rejected with 403."""
    payload = {
        "sensor_id": "sensor_unauthorized",
        "readings": {"pm25": 10.0},
    }
    resp = test_client.post("/ingest", json=payload)
    assert resp.status_code == 403


def test_ingest_authorized(test_client):
    """Test that authorized sensor accepts valid reading."""
    payload = {
        "sensor_id": "sensor_amsterdam_001",
        "readings": {"pm25": 20.0, "pm10": 30.0, "no2": 15.0, "o3": 50.0},
    }
    resp = test_client.post("/ingest", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["sensor_id"] == "sensor_amsterdam_001"


def test_ingest_invalid_readings(test_client):
    """Test that invalid readings are rejected with 400."""
    payload = {
        "sensor_id": "sensor_amsterdam_001",
        "readings": {"pm25": -10.0},  # Negative value
    }
    resp = test_client.post("/ingest", json=payload)
    assert resp.status_code == 400
