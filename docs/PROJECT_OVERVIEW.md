# 🎯 **Project Overview: LCW-Fetch**

**LCW-Fetch** is a professional-grade Python application that fetches cryptocurrency data from the Live Coin Watch API and stores it in InfluxDB (a time-series database) for analysis and monitoring.

## **📊 Key Statistics**
- **Total Lines of Code**: ~2,111 lines of Python (core application)
- **Repository**: `git@github.com:jrbgit/lcw-fetch.git`
- **Author**: jrbgit (joanas@gmail.com)
- **Python Version**: 3.8+ (tested on 3.10, 3.11, 3.12)
- **License**: MIT

---

## 🏗️ **Architecture & Structure**

### **Core Components**

1. **API Client** (`api/client.py` - 356 lines)
   - REST API client with circuit breaker pattern
   - Exponential backoff retry strategy
   - Rate limiting and caching support
   - Error handling (auth, rate limits, network issues)

2. **Data Fetcher** (`fetcher.py` - ~500+ lines)
   - Main orchestration logic
   - Paginated coin fetching (configurable pages)
   - Historical data retrieval (24-hour lookback)
   - Performance tracking integration

3. **Database Layer** (`database/influx_client.py` - 295 lines)
   - InfluxDB 2.x integration
   - Batch writing with configurable sizes
   - Connection pooling and health checks
   - Query API for data retrieval

4. **Scheduler** (`scheduler.py` - ~370 lines)
   - APScheduler-based automation
   - Multiple job types:
     - **Frequent fetch**: Every 1-2 minutes (configurable)
     - **Hourly exchange data**: Top exchanges
     - **Daily historical**: 7-day lookback
     - **Weekly full sync**: Top 200 coins
   - Graceful shutdown handling

5. **Data Models** (`models/` - 243 lines total)
   - **Coin**: Complete cryptocurrency data with delta tracking
   - **Exchange**: Exchange volume and visitor data
   - **Market**: Market overview and capitalization
   - Pydantic-based validation
   - InfluxDB point serialization

6. **Utilities** (`utils/` - 1,166 lines)
   - **Config**: Environment-based settings with validation
   - **Logger**: Loguru integration with rotation
   - **Cache**: LRU caching with TTL support
   - **Metrics**: Prometheus metrics export
   - **Performance Logger**: Operation timing and system resource tracking

### **Project Structure**
```
lcw-fetch/
├── src/lcw_fetcher/          # Main application package
│   ├── api/                  # API client & exceptions
│   ├── database/             # InfluxDB integration
│   ├── models/               # Data models (Coin, Exchange, Market)
│   ├── utils/                # Config, logging, caching, metrics
│   ├── fetcher.py            # Core fetching logic
│   ├── scheduler.py          # Job scheduling
│   └── main.py               # CLI interface
├── tests/                    # Comprehensive test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── performance/          # Performance benchmarks
├── config/                   # Configuration files & Grafana
├── docs/                     # Documentation & reports
├── docker-compose.yml        # Full stack deployment
├── Dockerfile                # Multi-stage container build
└── Makefile                  # Development automation
```

---

## 🚀 **Key Features**

### **1. Data Collection**
- ✅ Real-time cryptocurrency prices (1-2 minute intervals)
- ✅ Historical data (24-hour/7-day lookback)
- ✅ Exchange data (volumes, visitors)
- ✅ Market overview (total cap, BTC dominance)
- ✅ Paginated fetching (100 coins per page, configurable)
- ✅ Tracked coins: BTC, ETH, GLQ (configurable)

### **2. Reliability & Performance**
- ✅ Circuit breaker pattern for API failures
- ✅ Exponential backoff retry strategy
- ✅ Rate limiting (60 requests/min default)
- ✅ LRU caching with TTL
- ✅ Batch writing to InfluxDB
- ✅ Performance metrics tracking
- ✅ System resource monitoring

### **3. Observability**
- ✅ Prometheus metrics endpoint (port 9099)
- ✅ Grafana dashboards (included)
- ✅ Structured logging with Loguru
- ✅ Performance statistics tracking
- ✅ API credit monitoring
- ✅ Database statistics

### **4. DevOps**
- ✅ Docker & Docker Compose setup
- ✅ GitHub Actions CI/CD pipeline
- ✅ Multi-version Python testing (3.10-3.12)
- ✅ Non-root container user for security
- ✅ Health checks and graceful shutdown
- ✅ Comprehensive Makefile

---

## 🔧 **Configuration**

The application is configured via environment variables (`.env` file):

**Required:**
- `LCW_API_KEY` - Live Coin Watch API key
- `INFLUXDB_TOKEN` - InfluxDB authentication token
- `INFLUXDB_ORG` - InfluxDB organization name

**Optional:**
- `FETCH_INTERVAL_MINUTES` - Fetch frequency (default: 1)
- `TRACKED_COINS` - Comma-separated coin codes (default: BTC,ETH,GLQ)
- `COINS_LIST_PAGES` - Pages to fetch (default: 2)
- `COINS_PER_PAGE` - Coins per page (default: 100)
- `ENABLE_METRICS` - Enable Prometheus metrics (default: true)
- `LOG_LEVEL` - Logging level (default: INFO)

---

## 📦 **Technology Stack**

### **Core Dependencies**
- **requests** - HTTP client
- **influxdb-client** - InfluxDB 2.x integration
- **pydantic** - Data validation
- **APScheduler** - Job scheduling
- **loguru** - Modern logging
- **click** - CLI interface
- **prometheus_client** - Metrics export

### **Development Tools**
- **pytest** - Testing framework
- **black** & **isort** - Code formatting
- **flake8** - Linting
- **mypy** - Type checking

---

## 💡 **Recent Development Highlights**

Based on recent commits:
1. ✅ **Paginated fetching** - Implemented multi-page coin retrieval
2. ✅ **Docker permission fixes** - Resolved log file permission issues
3. ✅ **Performance optimization** - 4-phase optimization implementation
4. ✅ **Configurable intervals** - Fixed high CPU usage
5. ✅ **Grafana dashboards** - Added comprehensive GLQ dashboards
6. ✅ **CI/CD pipeline** - Upgraded to latest GitHub Actions

---

## 🎯 **CLI Commands**

```bash
# Check system status
python -m lcw_fetcher.main status

# Single fetch with 24h history
python -m lcw_fetcher.main run-once

# Start scheduler (automated)
python -m lcw_fetcher.main start

# Fetch specific coins
python -m lcw_fetcher.main fetch --coin BTC --coin ETH

# Show configuration
python -m lcw_fetcher.main config

# Performance stats
python -m lcw_fetcher.main perf-stats

# Cache statistics
python -m lcw_fetcher.main cache-stats

# Metrics server info
python -m lcw_fetcher.main metrics
```

---

## 🐳 **Docker Deployment**

The project includes a complete Docker Compose stack:
- **InfluxDB 2.7** - Time-series database
- **LCW-Fetch** - Main application
- **Grafana** - Data visualization (optional)

```bash
# Start the full stack
docker-compose up -d

# View logs
docker-compose logs -f lcw-fetch

# Stop services
docker-compose down
```

---

## 📈 **Data Schema (InfluxDB)**

### **Measurements:**

1. **cryptocurrency_data**
   - Tags: `code`, `name`, `currency`
   - Fields: `rate`, `volume`, `market_cap`, `rank`, `delta_1h`, `delta_24h`, etc.

2. **exchange_data**
   - Tags: `code`, `name`, `currency`
   - Fields: `volume`, `visitors`, `volume_per_visitor`, `rank`

3. **market_overview**
   - Tags: `currency`
   - Fields: `total_market_cap`, `total_volume`, `btc_dominance`

---

## 🧪 **Testing**

Comprehensive test suite with:
- Unit tests
- Integration tests (with InfluxDB)
- Performance benchmarks
- CI/CD integration

```bash
make test              # Run all tests
make test-coverage     # Coverage report
make test-unit         # Unit tests only
```

---

## 🎓 **Expert Assessment**

### **Strengths:**
1. ✅ **Professional architecture** - Well-structured, modular design
2. ✅ **Production-ready** - Error handling, logging, metrics
3. ✅ **Scalable** - Batch processing, pagination, caching
4. ✅ **Observable** - Comprehensive monitoring and metrics
5. ✅ **Well-documented** - Extensive README and inline docs
6. ✅ **Containerized** - Docker-first deployment
7. ✅ **CI/CD ready** - Automated testing and deployment

### **Code Quality:**
- Clean Python code following best practices
- Type hints with Pydantic models
- Proper error handling and logging
- Circuit breaker pattern for resilience
- Context managers for resource management

---

## 📊 **Component Statistics**

### **Source Code Breakdown:**
```
API Layer:           404 lines (client + exceptions)
Database Layer:      298 lines (InfluxDB integration)
Data Models:         243 lines (Coin, Exchange, Market)
Utilities:         1,166 lines (config, logging, cache, metrics)
Total Core Code:   ~2,111 lines
```

### **Module Distribution:**
- `utils/metrics.py` - 346 lines (Prometheus integration)
- `api/client.py` - 356 lines (API client with circuit breaker)
- `utils/performance_logger.py` - 308 lines (Performance tracking)
- `utils/cache.py` - 305 lines (LRU caching)
- `database/influx_client.py` - 295 lines (Time-series DB)

---

## 🔄 **Data Flow**

```
┌─────────────────┐
│  Live Coin      │
│  Watch API      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  API Client     │
│  (Circuit       │
│   Breaker)      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Cache Layer    │
│  (LRU + TTL)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Data Fetcher   │
│  (Orchestration)│
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  InfluxDB       │
│  (Time Series)  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Grafana        │
│  (Visualization)│
└─────────────────┘
```

---

## 🚦 **Scheduling Strategy**

1. **Frequent Updates** (Every 1-2 minutes)
   - Tracked coins (BTC, ETH, GLQ)
   - Paginated coin list (200 coins default)
   - Market overview

2. **Hourly Updates**
   - Top 50 exchanges
   - Exchange volume data

3. **Daily Updates** (2:00 AM UTC)
   - 7-day historical data for tracked coins
   - Deep historical backfill

4. **Weekly Full Sync** (Sunday 3:00 AM UTC)
   - Top 200 coins comprehensive data
   - Top 100 exchanges
   - Full market overview

---

## 📝 **Configuration Files**

### **Key Configuration:**
- `.env` - Environment variables (secrets)
- `.env.example` - Configuration template
- `docker-compose.yml` - Multi-container orchestration
- `Dockerfile` - Container image definition
- `Makefile` - Development automation
- `pyproject.toml` - Python tooling config
- `.github/workflows/` - CI/CD pipelines

---

## 🎯 **Use Cases**

1. **Real-time Monitoring** - Track cryptocurrency prices in real-time
2. **Historical Analysis** - Analyze price trends over time
3. **Market Research** - Study market capitalization and volumes
4. **Trading Insights** - Monitor exchange data and liquidity
5. **Data Science** - Export data for ML/AI analysis
6. **Portfolio Tracking** - Monitor specific coin performance

---

**Generated**: 2025-10-01  
**Project Status**: Active Development ✅  
**Maintainer**: jrbgit  

This is a **well-architected, production-grade cryptocurrency data fetching system** with excellent engineering practices! 🚀
