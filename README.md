# Project Aether 🌍

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0%2B-green.svg)](https://fastapi.tiangolo.com/)

An **enterprise-grade distributed Air Quality Monitoring System (AQMS)** backend for the Netherlands. This FastAPI-based Web API serves as a central server for a smart city network of 15 IoT sensors across the Netherlands, providing real-time data ingestion, historical analysis, and interactive geospatial visualizations.


⚠️ This project was developed as part of a university course.
It is published for portfolio and demonstration purposes only.
Reusing or submitting this code as coursework may violate academic integrity rules.

## 🎯 Features

### Core Capabilities
- **Real-Time Data Ingestion**: Secure endpoint for IoT sensor data with whitelist-based authorization
- **Interactive Geospatial Dashboard**: Live map visualization with color-coded air quality indicators
- **Historical Analysis**: Time series charts with range slider for detailed temporal analysis
- **Province Distribution**: Comparative analysis of air quality across Dutch provinces
- **System Health Monitoring**: Real-time status and metrics endpoint
- **Auto-Generated API Documentation**: Swagger UI for API exploration

### Technical Highlights
- **Configuration-Driven Architecture**: No hard-coded values, fully configurable via JSON
- **Clean Architecture**: Separation of concerns with DTOs, domain models, and service layers
- **Dependency Injection**: Type-safe dependency management using FastAPI patterns
- **Data Engineering**: Pandas-based batch processing with vector operations
- **Geospatial Processing**: WKT (Well-Known Text) parsing using Regular Expressions
- **Comprehensive Testing**: Full test suite using FastAPI TestClient

## 🏗️ Architecture

Project Aether follows **Clean Architecture** principles with **Domain-Driven Design**:

```
┌─────────────────────────────────────────────────────────┐
│                     Web Layer (main.py)                  │
│              FastAPI Routes & HTTP Handling              │
├─────────────────────────────────────────────────────────┤
│                Service Layer (sensor_manager.py)         │
│         Business Logic & Domain Orchestration            │
├─────────────────────────────────────────────────────────┤
│              Data Layer (persistance.py)                 │
│              File I/O & Serialization                    │
├─────────────────────────────────────────────────────────┤
│         Domain Models (sensor.py) - Framework-Free       │
│         DTOs (models.py) - Pydantic Validation          │
└─────────────────────────────────────────────────────────┘
```

### Key Design Patterns
- **Dependency Injection**: Services injected via `Depends()` for testability
- **DTO Pattern**: API validation separated from domain logic
- **Repository Pattern**: Abstracted data persistence layer
- **Strategy Pattern**: Pluggable visualization components

## 📋 Prerequisites

- **Python**: 3.11 or higher
- **pip**: Latest version recommended
- **Operating System**: Windows, macOS, or Linux

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/aether_project.git
cd aether_project
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Configuration Files
Ensure the following files exist:
- `config/server_config.json` - System configuration
- `config/sensors.json` - Sensor whitelist (15 authorized sensors)
- `data/historical_readings.csv` - Historical air quality data

## 🎮 Usage

### Start the Server

#### Using Shell Script (macOS/Linux)
```bash
chmod +x run.sh
./run.sh
```

#### Using Batch File (Windows)
```bash
run.bat
```

#### Manual Start
```bash
uvicorn src.aether.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`

### Startup Process
1. **Configuration Loading**: Parses `server_config.json` and `sensors.json`
2. **WKT Parsing**: Extracts coordinates from POINT geometries using regex
3. **Historical Data Loading**: Loads and cleans 131,400+ hourly readings
4. **Data Cleaning**: Removes invalid entries using pandas vector operations
5. **Service Initialization**: Sets up dependency injection containers

## 📡 API Endpoints

### Overview
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Welcome page with navigation links |
| `/ingest` | POST | Ingest sensor data (requires authorization) |
| `/map` | GET | Interactive real-time air quality map |
| `/status` | GET | System health and statistics |
| `/history/{sensor_id}` | GET | Time series chart for specific sensor |
| `/distribution/{year}/{month}` | GET | Province distribution for given month |
| `/docs` | GET | Auto-generated API documentation |

### Detailed Endpoint Documentation

#### POST /ingest
Ingest real-time sensor data with security validation.

**Request Body:**
```json
{
  "sensor_id": "sensor_amsterdam_001",
  "readings": {
    "pm25": 35.5,
    "pm10": 48.2,
    "no2": 22.1,
    "o3": 65.3
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Data ingested successfully",
  "sensor_id": "sensor_amsterdam_001",
  "timestamp": "2024-01-15T14:23:45Z"
}
```

**Security:**
- Returns 403 Forbidden if sensor_id not in whitelist
- Validates data structure using Pydantic
- Persists immediately to JSON storage

#### GET /map
Returns interactive HTML map with color-coded markers.

**Color Scheme:**
- 🟢 **Green (Safe)**: PM2.5 ≤ 25 µg/m³
- 🟡 **Yellow (Moderate)**: 25 < PM2.5 ≤ 50 µg/m³
- 🟠 **Orange (Unhealthy)**: 50 < PM2.5 ≤ 75 µg/m³
- 🔴 **Red (Dangerous)**: PM2.5 > 75 µg/m³
- ⚫ **Gray**: No data available

#### GET /status
Returns system health metrics.

**Response:**
```json
{
  "status": "healthy",
  "uptime_seconds": 3654.2,
  "active_sensors": 15,
  "total_readings": 1247,
  "last_update": "2024-01-15T14:23:45Z"
}
```

#### GET /history/{sensor_id}
Interactive time series chart with range slider.

**Parameters:**
- `sensor_id` (path): Sensor identifier (e.g., "sensor_amsterdam_001")

**Features:**
- Multiple traces: PM2.5, PM10, NO2, O3
- Range slider for temporal zooming
- Hover tooltips with exact values
- Full year of hourly data (8,760 points)

#### GET /distribution/{year}/{month}
100% stacked bar chart showing province distribution.

**Parameters:**
- `year` (path): Year (e.g., 2024)
- `month` (path): Month (1-12)

**Response:** HTML page with stacked bar chart showing percentage distribution across air quality categories for each province.

#### GET /docs
Auto-generated Swagger UI documentation with interactive API testing.

## 🧪 Testing

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_ingest.py -v
pytest tests/test_status.py -v
```

### Run with Coverage
```bash
pytest --cov=src/aether --cov-report=html
```

### Test Structure
- `tests/test_ingest.py`: Data ingestion and validation tests
- `tests/test_status.py`: System health and monitoring tests
- Uses **FastAPI TestClient** for integration testing
- Fixtures for test data and configuration

## ⚙️ Configuration

### Server Configuration (`config/server_config.json`)
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

### Sensor Configuration (`config/sensors.json`)
Each sensor entry contains:
- `id`: Unique sensor identifier
- `location`: WKT POINT geometry (e.g., "POINT(4.9041 52.3676)")
- `metadata`: Region, province, deployment date, site type

**Example:**
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

## 📁 Project Structure

```
aether_project/
├── config/
│   ├── sensors.json              # Sensor whitelist (15 sensors)
│   └── server_config.json        # System configuration
├── data/
│   ├── historical_readings.csv   # Historical air quality data
│   └── readings.json             # Real-time storage
├── src/
│   └── aether/
│       ├── __init__.py
│       ├── main.py               # FastAPI application & routes
│       ├── models.py             # Pydantic DTOs
│       ├── sensor.py             # Domain models
│       ├── sensor_manager.py     # Business logic service
│       ├── persistance.py        # Data persistence layer
│       ├── data_cleaning.py      # Pandas data processing
│       ├── visualization.py      # Map visualizations
│       ├── temporal_visualization.py  # Time series charts
│       └── dependencies.py       # Dependency injection
├── tests/
│   ├── test_ingest.py           # Ingestion tests
│   └── test_status.py           # Status endpoint tests
├── requirements.txt             # Python dependencies
├── run.sh                       # Unix startup script
├── run.bat                      # Windows startup script
└── README.md                    # This file
```

## 🔧 Technology Stack

### Core Framework
- **FastAPI** (0.115.0+): Modern, fast web framework with automatic API documentation
- **Uvicorn** (0.32.0+): Lightning-fast ASGI server
- **Pydantic** (2.10.0+): Data validation using Python type annotations

### Data Processing
- **Pandas** (2.2.0+): High-performance data manipulation and analysis
- **NumPy**: Numerical computing (pandas dependency)

### Visualization
- **Plotly** (5.24.0+): Interactive charts and maps

### Testing
- **Pytest** (9.0.0+): Testing framework
- **HTTPX** (0.27.0+): HTTP client for TestClient

## 🎓 Learning Objectives

This project demonstrates mastery of:
- ✅ RESTful API design with FastAPI
- ✅ Clean Architecture and Domain-Driven Design
- ✅ Dependency Injection patterns
- ✅ Data engineering with pandas
- ✅ Geospatial data processing (WKT parsing)
- ✅ Interactive data visualization
- ✅ Comprehensive testing strategies
- ✅ Type-safe Python development

## 🐛 Troubleshooting

### Server Won't Start
- Verify Python version: `python --version` (must be 3.11+)
- Check if port 8000 is available: `netstat -an | grep 8000`
- Ensure all config files exist in `config/` directory

### Import Errors
```bash
# Ensure you're in virtual environment
pip install -r requirements.txt --upgrade
```

### Data Loading Failures
- Verify `data/historical_readings.csv` exists and is readable
- Check CSV format matches expected schema
- Review startup logs for specific error messages

### WKT Parsing Errors
- Ensure sensor locations follow format: `POINT(lon lat)`
- Validate coordinate ranges: longitude [-180, 180], latitude [-90, 90]
- Check for proper whitespace in WKT strings

## 📊 Data Statistics

### Historical Dataset
- **Total Records**: 131,400+ hourly readings
- **Time Span**: One full year of data
- **Sensors**: 15 sensors across Netherlands
- **Pollutants**: PM2.5, PM10, NO2, O3
- **Data Quality**: ~99.94% clean after processing

### Real-Time Operations
- **Storage Format**: JSON for immediate persistence
- **Validation**: Whitelist-based authorization
- **State Management**: In-memory with disk synchronization

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🔮 Future Improvements
- Replace JSON storage with PostgreSQL
- Introduce async background ingestion workers
- Add authentication via OAuth2 / JWT
- Containerize with Docker and add CI pipeline

### Code Standards
- Follow PEP 8 style guide
- Add type hints to all functions
- Write docstrings for public APIs
- Include tests for new features
- Update documentation as needed

## 🙏 Acknowledgments

- **OpenStreetMap**: Map tile provider
- **Plotly**: Interactive visualization library
- **FastAPI**: Modern web framework
- **Netherlands Environmental Assessment Agency**: Air quality data standards

## 📞 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ for smart cities and clean air monitoring**
