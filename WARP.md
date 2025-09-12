# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a cryptocurrency data fetcher application that connects to the Live Coin Watch API to collect real-time market data and stores it in InfluxDB for time-series analysis. The application uses Python with scheduled data collection, comprehensive error handling, and a CLI interface.

## Common Development Commands

### Build & Setup Commands
```powershell
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (includes test tools)
make install-dev
# OR manually:
pip install -r requirements.txt
pip install -r requirements-test.txt
pip install -e .

# Setup development environment with pre-commit hooks
make setup-dev
```

### Testing Commands
```powershell
# Run all tests
pytest
# OR use Makefile:
make test

# Run only unit tests
pytest tests/unit/
# OR:
make test-unit

# Run only integration tests
pytest tests/integration/
# OR:
make test-integration

# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing
# OR:
make test-coverage

# Run tests in parallel (faster)
pytest -n auto
# OR:
make test-parallel

# Run tests excluding slow ones
pytest -m "not slow"
# OR:
make test-fast

# Run specific test categories
pytest -m unit           # Only unit tests
pytest -m integration    # Only integration tests
pytest -m api            # API-related tests
pytest -m database       # Database tests
```

### Application Commands
```powershell
# Check system status (API and database connectivity)
python -m lcw_fetcher.main status

# Run a single data fetch cycle
python -m lcw_fetcher.main run-once

# Start the scheduled data fetcher
python -m lcw_fetcher.main start

# View current configuration
python -m lcw_fetcher.main config

# Fetch specific coins
python -m lcw_fetcher.main fetch --coin BTC --coin ETH

# Fetch top N coins
python -m lcw_fetcher.main fetch --limit 50
```

### Docker Commands
```powershell
# Build Docker image
make docker
# OR:
docker build -t lcw-api-fetcher .

# Start full stack (app + InfluxDB + Grafana)
docker-compose up -d

# Start only InfluxDB for development
make db-up

# Stop and clean up
docker-compose down
make db-down
```

### Code Quality Commands
```powershell
# Format code (Black + isort)
make format

# Check formatting without changing files
make format-check

# Lint code
make lint

# Type checking
make type-check

# Security checks
make security

# Run all quality checks (CI simulation)
make ci-local
```

## Architecture Overview

### Core Components

**Data Flow Architecture:**
1. **Scheduler** (`scheduler.py`) - Orchestrates timed data collection using APScheduler
2. **Data Fetcher** (`fetcher.py`) - Coordinates API calls and database operations
3. **API Client** (`api/client.py`) - Handles Live Coin Watch API communication with retry logic
4. **Database Client** (`database/influx_client.py`) - Manages InfluxDB time-series data storage
5. **CLI Interface** (`main.py`) - Provides command-line interaction using Click

**Data Models** (Pydantic-based):
- `Coin` - Cryptocurrency data with price, volume, market cap, and historical data
- `Exchange` - Trading platform data with volume and visitor metrics
- `Market` - Overall market overview data with BTC dominance

### Key Design Patterns

**Configuration Management:**
- Uses Pydantic Settings for type-safe configuration from environment variables
- Centralized in `utils/config.py` with validation and defaults
- Supports `.env` file loading for development

**Error Handling Strategy:**
- Custom exception hierarchy for API errors (`LCWAPIError`, `LCWRateLimitError`, etc.)
- Graceful degradation - continues operation on partial failures
- Comprehensive logging with structured messages

**Rate Limiting:**
- Built-in rate limiting respects API quotas
- Configurable requests per minute
- Automatic backoff on rate limit exceeded

**Scheduling System:**
- Multiple job types: frequent fetch (1min), hourly exchanges, daily historical, weekly full sync
- Non-overlapping job execution with max_instances=1
- Graceful shutdown handling for all scheduled jobs

**Database Design:**
- Time-series optimized for InfluxDB 2.x
- Measurements: `cryptocurrency_data`, `exchange_data`, `market_overview`
- Tags for filtering (code, name, currency), fields for metrics (rate, volume, cap)

### Testing Architecture

**Test Organization:**
- `tests/unit/` - Isolated component tests with mocking
- `tests/integration/` - End-to-end data flow tests
- `conftest.py` - Comprehensive fixture library with sample data

**Test Categories (Pytest Markers):**
- `@pytest.mark.unit` - Fast isolated tests
- `@pytest.mark.integration` - Slower cross-component tests
- `@pytest.mark.slow` - Tests requiring external services
- `@pytest.mark.api` - Tests requiring Live Coin Watch API
- `@pytest.mark.database` - Tests requiring InfluxDB

**Mock Strategy:**
- Extensive use of `unittest.mock` for external dependencies
- Fixtures for sample API responses and database query results
- Time-based testing with `freezegun` for consistent datetime handling

## Development Guidelines

### Environment Setup Requirements
```powershell
# Required environment variables
$env:LCW_API_KEY="your_live_coin_watch_api_key"
$env:INFLUXDB_TOKEN="your_influxdb_token"
$env:INFLUXDB_ORG="your_organization_name"

# Optional with defaults
$env:INFLUXDB_URL="http://localhost:8086"
$env:INFLUXDB_BUCKET="cryptocurrency_data"
$env:LOG_LEVEL="INFO"
$env:FETCH_INTERVAL_MINUTES="5"
```

### Adding New Data Sources
1. Create model in `src/lcw_fetcher/models/`
2. Add API methods to `src/lcw_fetcher/api/client.py`
3. Update fetcher logic in `src/lcw_fetcher/fetcher.py`
4. Add storage methods to `src/lcw_fetcher/database/influx_client.py`
5. Write tests in both `tests/unit/` and `tests/integration/`

### Database Schema Considerations
- InfluxDB measurements use tags for dimensions, fields for metrics
- Time precision is nanosecond (default InfluxDB)
- Use `to_influx_point()` method on models for consistent data transformation
- Tags should be strings, fields should be numeric when possible

### Deployment Considerations
- Application supports both standalone and Docker deployments
- Uses non-root user in Docker for security
- Health checks implemented for both application and InfluxDB
- Logs directory needs write permissions in production

### Configuration Validation
- All config uses Pydantic with field validators
- API keys and tokens are required fields
- Numeric ranges are validated (fetch intervals, coin limits)
- Timezone and log level validation with specific allowed values

This codebase emphasizes reliability, observability, and maintainability for long-running cryptocurrency data collection with comprehensive error handling and monitoring capabilities.
