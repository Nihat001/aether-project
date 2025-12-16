# src/aether/main.py

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.responses import HTMLResponse

from .models import IngestRequest, IngestResponse, StatusResponse
from .sensor_manager import (
    SensorManager,
    UnauthorizedSensorError,
    InvalidReadingError,
)
from . import dependencies
from . import persistance
from .visualization import MapVisualizer
from .temporal_visualization import TemporalVisualizer


CONFIG_PATH = "config/server_config.json"
SENSORS_PATH = "config/sensors.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Modern FastAPI lifespan for initialization and teardown.
    """
    # Startup
    config = persistance.load_server_config(CONFIG_PATH)
    sensors = persistance.load_sensors(SENSORS_PATH)
    historical_df = persistance.load_historical_data(
        config["historical_data_file"]
    )

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

    yield

    # Teardown (nothing special here, but could flush things if needed)


app = FastAPI(
    title="Project Aether AQMS",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------- Routes ----------


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return """
    <html>
      <head><title>Project Aether</title></head>
      <body>
        <h1>Project Aether - Air Quality Monitoring System</h1>
        <ul>
          <li><a href="/docs">Swagger API Docs</a></li>
          <li><a href="/status">System Status</a></li>
          <li><a href="/map">Real-Time Map</a></li>
          <li><a href="/history/sensor_amsterdam_001">Example History</a></li>
          <li><a href="/distribution/2024/1">Example Distribution (2024-01)</a></li>
        </ul>
      </body>
    </html>
    """


@app.post("/ingest", response_model=IngestResponse)
def ingest(
    request: IngestRequest,
    manager: Annotated[SensorManager, Depends(dependencies.get_sensor_manager)],
) -> IngestResponse:
    try:
        reading = manager.ingest(request.sensor_id, request.readings)
    except UnauthorizedSensorError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized sensor",
        )
    except InvalidReadingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": e.errors},
        )

    return IngestResponse(
        status="ok",
        message="Reading ingested",
        sensor_id=reading.sensor_id,
        timestamp=reading.timestamp.astimezone(timezone.utc),
    )


@app.get("/status", response_model=StatusResponse)
def status_endpoint(
    manager: Annotated[SensorManager, Depends(dependencies.get_sensor_manager)],
) -> StatusResponse:
    data = manager.get_status()
    return StatusResponse(**data)


@app.get("/map", response_class=HTMLResponse)
def map_endpoint(
    manager: Annotated[SensorManager, Depends(dependencies.get_sensor_manager)],
    viz: Annotated[
        MapVisualizer, Depends(dependencies.get_map_visualizer)
    ],
) -> str:
    df = manager.get_map_dataframe()
    html = viz.create_map_html(df, title="Real-Time Air Quality Map")
    return HTMLResponse(content=html)


@app.get("/history/{sensor_id}", response_class=HTMLResponse)
def history_endpoint(
    sensor_id: str,
    manager: Annotated[SensorManager, Depends(dependencies.get_sensor_manager)],
    temporal_viz: Annotated[
        TemporalVisualizer, Depends(dependencies.get_temporal_visualizer)
    ],
) -> str:
    try:
        df = manager.get_sensor_history(sensor_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found or has no historical data",
        )

    html = temporal_viz.create_time_series(
        df, sensor_id=sensor_id, title=f"Historical Readings - {sensor_id}"
    )
    return HTMLResponse(content=html)


@app.get(
    "/distribution/{year}/{month}",
    response_class=HTMLResponse,
)
def distribution_endpoint(
    manager: Annotated[SensorManager, Depends(dependencies.get_sensor_manager)],
    temporal_viz: Annotated[
        TemporalVisualizer, Depends(dependencies.get_temporal_visualizer)
    ],
    year: int = Path(..., ge=2000, le=2100),
    month: int = Path(..., ge=1, le=12),
) -> str:
    try:
        df = manager.get_distribution_dataframe(year, month)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12",
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data for given year/month",
        )

    thresholds = manager.config["thresholds"]
    html = temporal_viz.create_distribution_chart(
        df,
        year=year,
        month=month,
        thresholds=thresholds,
        title=f"Province Distribution {year}-{month:02d}",
    )
    return HTMLResponse(content=html)
