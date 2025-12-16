# End-Term Assignment: Project Aether

## Overview & Goal

This project is an **enterprise-grade** distributed Air Quality Monitoring System (AQMS) backend for the Netherlands. You will build a robust Web API using FastAPI that acts as a central server for a smart city network of 15 IoT sensors across the Netherlands.

The application must validate and ingest data from IoT sensors, persist both real-time and historical readings, serve interactive geospatial dashboards, and provide comprehensive temporal analysis capabilities.

The system operates on a **Configuration-Driven Architecture** following **Clean Architecture** principles, **Domain-Driven Design**, and **Dependency Injection** patterns.

## Learning Objectives

By completing this project, you will demonstrate mastery of:

- **Web API Development**: RESTful endpoints using FastAPI and Pydantic
- **Data Engineering**: WKT parsing with Regular Expressions, pandas data processing
- **Clean Architecture**: Separation of DTOs from Domain Models, layered design
- **Dependency Injection**: Type-safe dependency management with FastAPI
- **Geospatial Visualization**: Interactive Plotly maps and temporal animations
- **Historical Data Analysis**: Processing and visualizing large datasets with pandas
- **Automated Testing**: Comprehensive test suite with FastAPI TestClient
- **Domain-Driven Design**: Framework-independent business logic

## Detailed Requirements

### 1. Configuration & Startup

**Requirement**: The server must be configuration-driven with no hard-coded values. It must initialize by reading configuration files and loading historical data.

#### Configuration Files

1. **System Config** (`config/server_config.json`):
   ```json
   {
     "storage_file": "data/readings.json",
     "historical_data_file": "data/historical_readings.csv",
     "host": "0.0.0.0",
     "port": 8000,
     "thresholds": {
       "pm25_safe": 25.0,
       "pm25_moderate": 50.0,
       "pm25_danger": 75.0,
       "pm10_safe": 50.0,
       "pm10_moderate": 100.0,
       "pm10_danger": 150.0
     },
     "map_config": {
       "default_zoom": 7,
       "map_style": "open-street-map"
     }
   }
   ```

2. **Sensor Whitelist** (`config/sensors.json`):
   - 15 authorized sensors across Netherlands
   - Each entry contains: `id`, `location` (WKT format), `metadata` (region, province, deployment_date, site_type)
   - Example:
     ```json
     {
       "id": "sensor_amsterdam_001",
       "location": "POINT(4.9041 52.3676)",
       "metadata": {
         "region": "Amsterdam",
         "province": "North Holland",
         "deployment_date": "2024-01-15",
         "site_type": "urban_center"
       }
     }
     ```

#### Startup Logic

1. **Parse Configuration**:
   - Load `sensors.json` and parse WKT using **Regular Expressions only** (no string splitting/slicing)
   - Extract latitude and longitude using named capture groups
   - Validate coordinate ranges (-180 to 180 for lon, -90 to 90 for lat)
   - Log and discard sensors with invalid WKT (don't crash)

2. **Load Historical Data**:
   - Read CSV file with one year of hourly sensor readings (historical_readings.csv)
   - Use **pandas vector operations** to clean data:
     - Drop rows with missing critical values (sensor_id, timestamp)
     - Remove rows with negative pollutant values
     - Filter extreme outliers (PM2.5 > 500)
     - Convert timestamp to datetime
   - Log statistics (rows loaded, rows dropped, percentage cleaned)

3. **Initialize Services**:
   - Set up dependency injection containers
   - Initialize service layer (business logic)
   - Prepare visualization components
   - Hydrate state from persistent storage

### 2. API Endpoints

The application must expose 7 HTTP endpoints:

#### A. POST /ingest - Data Ingestion

**Input**: JSON payload with `sensor_id` and `readings` dictionary

**Logic**:
- **Security**: Verify sensor_id against whitelist (403 Forbidden if unauthorized)
- **Validation**: Use pandas-based validation (DataCleaner)
- **Storage**: Create domain model (SensorReading) without validation, store raw data
- **Persistence**: Save to JSON file immediately
- **State Update**: Update sensor's last reading and timestamp

**Response**: `IngestResponse` DTO with status, message, sensor_id, timestamp

#### B. GET /map - Real-Time Dashboard

**Output**: HTML page with interactive Plotly map

**Logic**:
- Combine sensor locations with latest readings
- Use `px.scatter_map` for visualization
- Color-code markers by PM2.5 thresholds:
  - Green (Safe): ≤25 µg/m³
  - Yellow (Moderate): 25-50 µg/m³
  - Orange (Unhealthy): 50-75 µg/m³
  - Red (Dangerous): >75 µg/m³
  - Gray: No data
- Return HTML using `fig.to_html(include_plotlyjs='cdn', full_html=True)`

#### C. GET /status - System Health

**Output**: JSON with system statistics

**Data**:
- status: "healthy" or "degraded"
- uptime_seconds: Time since startup
- active_sensors: Count of sensors with readings
- total_readings: Total ingested readings
- last_update: Timestamp of most recent reading

#### D. GET /history/{sensor_id} - Time Series Chart

**Input**: sensor_id path parameter

**Output**: HTML page with time series plot

**Requirements**:
- Show PM2.5, PM10, NO2, O3 as separate traces
- Include **range slider** at bottom for zooming
- Display full year of hourly data (8,760 points per sensor)
- Interactive hover with exact values
- Return 404 if sensor doesn't exist or has no historical data

#### E. GET /distribution/{year}/{month} - Province Distribution

**Input**: year and month path parameters

**Output**: HTML page with 100% stacked bar chart

**Requirements**:
- Aggregate readings by province for specified month
- Categorize each reading by threshold (Safe/Moderate/Unhealthy/Dangerous)
- Create 100% stacked bar chart (one bar per province)
- Show percentage distribution in each category
- Validate month range (1-12), return 400 for invalid values
- Return 404 if no data exists for specified period

#### F. GET / - Welcome Page

**Output**: HTML page with navigation links to all endpoints

#### G. GET /docs - API Documentation

**Output**: Auto-generated Swagger UI documentation

### 3. Data Models & Architecture

#### Domain Models (`sensor.py`)

**SensorReading**:
- Plain Python class (not Pydantic)
- Stores readings in original form **without validation**
- Fields: sensor_id, readings (dict), timestamp
- Method: `to_dict()` for serialization

**SensorInfo**:
- Plain Python class
- Fields: id, location, latitude, longitude, metadata, last_reading, last_update

#### DTOs - Data Transfer Objects (`models.py`)

**API Models with Pydantic validation**:
- `IngestRequest`: API input validation
- `IngestResponse`: API output format
- `StatusResponse`: Status endpoint format
- `ErrorResponse`: Error formatting

**Key Principle**: Validation happens at API boundary (DTOs), not in domain models

#### Data Cleaning (`data_cleaning.py`)

**DataCleaner class** with static methods using pandas:
- `validate_readings()`: Check readings before ingestion (returns bool, errors list)
- `clean_readings_batch()`: Clean batch of readings with vector operations
- `aggregate_by_sensor()`: Group and aggregate by sensor
- `filter_by_threshold()`: Filter based on pollutant thresholds
- `calculate_statistics()`: Compute mean, median, min, max, std

**Philosophy**: Store raw data, validate only before presentation/calculation

### 4. Service Layer Architecture

#### Separation of Concerns

**Web Layer** (`main.py`):
- FastAPI routes only
- HTTP status codes
- Request/response handling
- Exception translation (service exceptions → HTTP exceptions)
- Uses dependency injection (`Depends()`)

**Service Layer** (`sensor_manager.py`):
- Business logic (authorization, ingestion, retrieval)
- State management (counters, timestamps)
- Data orchestration
- Domain-specific exceptions (`UnauthorizedSensorError`, `InvalidReadingError`)
- Presentation-independent (can be used outside FastAPI)

**Data Layer** (`persistence.py`):
- File I/O operations
- JSON/CSV serialization
- Reading storage and retrieval

#### Dependency Injection (`dependencies.py`)

**Requirements**:
- Implement singleton service providers
- `get_sensor_manager()`: Returns SensorManager instance
- `get_visualizer()`: Returns MapVisualizer instance
- `get_temporal_visualizer()`: Returns TemporalVisualizer instance
- Use in routes: `Annotated[SensorManager, Depends(get_sensor_manager)]`
- Initialize in lifespan handler (modern FastAPI pattern, not `on_event`)

### 6. Temporal Visualizations

#### Time Series with Range Slider (`temporal_visualization.py`)

**Method**: `create_time_series(df, sensor_id, title)`

**Requirements**:
- Multiple traces: PM2.5, PM10, NO2, O3
- Different colors per pollutant
- **Range slider** enabled: `xaxis={"rangeslider": {"visible": True}}`
- Unified hover mode
- 8,760 data points per sensor

#### Distribution Chart

**Method**: `create_distribution_chart(df, thresholds, year, month)`

**Requirements**:
- Categorize readings: Safe/Moderate/Unhealthy/Dangerous
- Group by province
- Calculate percentage in each category
- Create 100% stacked bar chart (`barmode="stack"`)
- Y-axis range: [0, 100]
- Show percentages inside bars
- Color-code by category (same colors as maps)

### 7. Data Persistence

**Requirements**: Multi-tier storage with automatic cleaning

#### Real-Time Storage
- JSON file for current ingested readings
- Immediate persistence on ingestion
- State hydration on restart
- Path: `config["storage_file"]`

#### Historical Storage
- CSV file with 131,400 hourly readings
- Loaded at startup
- Cleaned using pandas vector operations
- No validation at ingestion (store raw)
- Path: `config["historical_data_file"]`


## Technical Implementation Guidelines

### 1. WKT Parsing with Regex

**Requirement**: Use Regular Expressions with named capture groups

```python
WKT_POINT_PATTERN = re.compile(
    r"POINT\s*\(\s*(?P<lon>-?\d+\.?\d*)\s+(?P<lat>-?\d+\.?\d*)\s*\)",
    re.IGNORECASE,
)
```

**Must**:
- Use named groups (`?P<lon>`, `?P<lat>`)
- Handle whitespace variations
- Be case-insensitive
- Validate coordinate ranges

**Must Not**:
- Use `.split()` or `.replace()`
- Use string slicing
- Hard-code coordinate extraction

### 2. Domain Models vs DTOs

**Domain Models** (`sensor.py`):
- Plain Python classes
- **No validation** (no Pydantic)
- Store data in original form
- Framework-independent

**DTOs** (`models.py`):
- Pydantic BaseModel classes
- Validation at API boundary
- Request/response models only

**Example**:
```python
# Domain Model - No validation
class SensorReading:
    def __init__(self, sensor_id, readings, timestamp):
        self.readings = readings  # Store as-is, even if invalid

# DTO - Pydantic validation
class IngestRequest(BaseModel):
    sensor_id: str = Field(..., min_length=1)
    readings: dict[str, float]
```

### 3. Pandas Data Cleaning

**Requirement**: Validate using pandas vector operations, not at ingestion

**When to Validate**:
- Before presentation (visualization)
- Before calculation (statistics)
- At startup (historical data cleaning)

**Not When**:
- At ingestion (store raw) - for this assignment, we will store raw data at ingestion
- In domain models (keep pure) - for this assignment, we will keep the data in the domain model as is

**Example**:
```python
# Batch validation with pandas
df = df[df["pm25"] >= 0]  # Vector operation
df = df.dropna(subset=["sensor_id"])  # Vector operation
```

### 4. Dependency Injection

**Requirement**: Use FastAPI Depends() pattern

**Implementation**:
```python
# Provider
def get_sensor_manager() -> SensorManager:
    if _sensor_manager is None:
        raise RuntimeError("Not initialized")
    return _sensor_manager

# Route with injection
@app.post("/ingest")
def ingest_data(
    request: IngestRequest,
    sensor_manager: Annotated[SensorManager, Depends(get_sensor_manager)],
) -> IngestResponse:
    # sensor_manager is auto-injected
    reading = sensor_manager.ingest_reading(...)
```

**Benefits**:
- Type-safe
- Testable (easy mocking)
- No manual state management
- Clear dependencies

### 5. Testing with TestClient

**Requirement**: Use FastAPI's TestClient for all API tests

**Setup**:
```python
from fastapi.testclient import TestClient

@pytest.fixture
def test_app(server_config_file, sensors_config_file):
    from aether.main import create_app
    
    reset_services()
    app = create_app(server_config_file, sensors_config_file)
    initialize_services(server_config_file, sensors_config_file)
    
    with TestClient(app) as client:
        yield client
    
    reset_services()

def test_endpoint(test_app: TestClient):
    response = test_app.get("/status")
    assert response.status_code == 200
```

**Note**: All routes and tests are **synchronous** - no async/await needed. This simplifies the code and is perfectly adequate for this application's scale.

### 6. FastAPI Patterns

**Startup Event**:
```python
@app.on_event("startup")
def startup_event():
    initialize_services(config_path, sensors_path)
```

**Synchronous Routes**:
```python
@app.post("/ingest")
def ingest_data(
    request: IngestRequest,
    sensor_manager: Annotated[SensorManager, Depends(get_sensor_manager)],
) -> IngestResponse:
    # No async, no await - simpler for students
    reading = sensor_manager.ingest_reading(...)
    return IngestResponse(...)
```

## Sample Usage Scenarios

### Scenario 1: Real-Time Monitoring

1. **Start**: Server loads config, parses WKT for all 15 sensors, loads 131K historical readings
2. **Cleaning**: Pandas removes 81 incorrect rows (0.06%)
3. **Request**: `POST /ingest` with `{"sensor_id": "sensor_amsterdam_001", "readings": {"pm25": 55.0}}`
4. **Result**: Server accepts (200 OK), saves to JSON, updates sensor state
5. **Request**: `GET /map`
6. **Result**: Map shows Amsterdam with red dot (55.0 > 50.0 threshold)

### Scenario 2: Historical Analysis

1. **Request**: `GET /history/sensor_rotterdam_001`
2. **Result**: Time series chart showing Rotterdam's pollution over year
   - Higher in winter months
   - Peak during rush hours
   - Lower on weekends
   - Range slider allows zooming to specific periods

### Scenario 3: Province Comparison

1. **Request**: `GET /distribution/2024/1` (January - winter)
2. **Result**: Stacked bar shows:
   - South Holland (Rotterdam): 40% Unhealthy, 30% Moderate
   - Groningen: 80% Safe, 15% Moderate
   
3. **Request**: `GET /distribution/2024/6` (June - summer)
4. **Result**: Same provinces improved:
   - South Holland: 60% Safe, 30% Moderate
   - Groningen: 95% Safe, 5% Moderate

### Scenario 4: Unauthorized Access

1. **Request**: `POST /ingest` with `{"sensor_id": "sensor_unauthorized", ...}`
2. **Result**: 403 Forbidden with clear error message
3. **Log**: Warning logged but server continues running

## Scoring System (100 Points Total)

| Category | Task Description | Points |
|----------|-----------------|--------|
| Architecture & Config | Loads JSON files, implements whitelist, dependency injection | 15 |
| Data Engineering | Regex WKT parsing, pandas data cleaning/analysis | 15 |
| API Implementation | 7 endpoints correctly implemented | 20 |
| Visualization | Real-time map + 2 temporal visualizations | 15 |
| Robustness | Error handling, graceful degradation | 5 |
| Clean Architecture | DTOs vs Domain separation, service layer | 5 |
| Code Quality | Type hints, documentation, professional patterns | 5 |
| Testing | Tests with FastAPI TestClient and others | 20 |
| **TOTAL** | | **100** |

## Required Technologies

### Core Dependencies
- **Python**: 3.11 or higher
- **FastAPI**: 0.115.0+ (web framework)
- **Uvicorn**: 0.32.0+ (ASGI server)
- **Pydantic**: 2.10.0+ (DTO validation)
- **Pandas**: 2.2.0+ (data processing)
- **Plotly**: 5.24.0+ (visualizations)

## Submission Requirements

### What to Submit

1. **Complete source code** in `src/aether/` directory
2. **Configuration files** in `config/` directory
3. **Test suite** in `tests/` directory
4. **README.md** with:
   - Installation instructions
   - Usage examples
   - API documentation
   - Architecture description
5. **requirements.txt** or **pyproject.toml**
6. **Startup script** (run.sh or equivalent)

### Verification Checklist

Before submission, verify:
- ✅ `./run.sh` starts server without errors
- ✅ All 8 endpoints accessible
- ✅ `pytest tests/` shows passing tests
- ✅ Map centers on Netherlands (all 15 sensors visible)
- ✅ Temporal animation plays smoothly
- ✅ Range slider works on time series
- ✅ Distribution chart shows all provinces
- ✅ No hard-coded paths or sensor IDs
- ✅ Type hints throughout (`mypy src/` passes)

## Best Practices & Tips

### 1. Start with Architecture

Begin by setting up the layer structure:
1. Create domain models (sensor.py)
2. Create DTOs (models.py)
3. Implement service layer (sensor_manager.py)
4. Add dependency injection (dependencies.py)
5. Create web layer (main.py)

### 2. Use Pandas Effectively

Don't reinvent the wheel:
- `df.dropna()` for missing values
- `df[df["pm25"] >= 0]` for negative filtering
- `df.groupby()` for aggregation
- Vector operations are fast and clean

### 3. Test As You Build

Write tests alongside code:
- Test domain models (easy, no dependencies)
- Test service layer (business logic)
- Test web layer last (uses all layers)

### 4. Use Type Hints Everywhere

FastAPI leverages type hints for:
- Auto-validation
- Auto-documentation
- IDE autocomplete
- Error detection

## Common Pitfalls to Avoid

❌ **Don't validate in domain models** - Use DTOs and pandas instead  
❌ **Don't use string splitting for WKT** - Must use regex  
❌ **Don't mix DTOs and domain models** - Separate files  
❌ **Don't add async/await** - Keep routes synchronous for simplicity  
❌ **Don't hard-code thresholds** - Load from config  
❌ **Don't skip type hints** - Required for full credit  

## Success Criteria Summary

✅ **Configuration-Driven**: All behavior from JSON files  
✅ **WKT Regex**: Named groups, no splitting  
✅ **7 Endpoints**: Real-time + temporal  
✅ **Pandas Cleaning**: Vector operations  
✅ **Clean Architecture**: DTOs ≠ Domain  
✅ **Dependency Injection**: FastAPI Depends()  
✅ **Testing**: FastAPI TestClient with proper fixtures  
✅ **Type Hints**: 100% coverage  
✅ **Single README**: Complete documentation  

