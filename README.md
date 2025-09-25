# LCW-Fetch: Live Coin Watch Data Fetcher

A Python application to fetch cryptocurrency data from the [Live Coin Watch API](https://www.livecoinwatch.com/) and store it in a time series database (InfluxDB) for analysis and monitoring.

## Features

- 🚀 **Automated Data Fetching**: Scheduled collection of cryptocurrency data
- 📊 **Time Series Storage**: Store data in InfluxDB for efficient time-based queries
- 🔧 **Configurable**: Flexible configuration via environment variables
- 📈 **Multiple Data Types**: Fetch coins, exchanges, and market overview data
- ⚡ **Rate Limiting**: Built-in API rate limiting to respect API quotas
- 🗓️ **Flexible Scheduling**: Multiple scheduling options (regular, hourly, daily, weekly)
- 📱 **CLI Interface**: Easy-to-use command-line interface
- 🔍 **Monitoring**: Built-in status checking and logging

## Quick Start

### Prerequisites

- Python 3.8 or higher
- InfluxDB 2.x instance
- Live Coin Watch API key (free tier available)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd lcw-fetch
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Configure your environment:**
   ```bash
   # Required
   LCW_API_KEY=your_live_coin_watch_api_key
   INFLUXDB_TOKEN=your_influxdb_token
   INFLUXDB_ORG=your_organization_name
   
   # Optional (with defaults)
   INFLUXDB_URL=http://localhost:8086
   INFLUXDB_BUCKET=cryptocurrency_data
   FETCH_INTERVAL_MINUTES=5
   ```

### Quick Test

```bash
# Check system status
python -m lcw_fetcher.main status

# Run a single fetch cycle
python -m lcw_fetcher.main run-once

# Start the scheduler
python -m lcw_fetcher.main start
```

## Installation Guide

### 1. Get API Keys

#### Live Coin Watch API Key
1. Visit [Live Coin Watch](https://www.livecoinwatch.com/)
2. Create an account and navigate to your profile
3. Generate an API key (free tier provides 10,000 requests/day)

#### InfluxDB Setup
You can use InfluxDB Cloud or self-hosted:

**InfluxDB Cloud:**
1. Sign up at [InfluxDB Cloud](https://www.influxdata.com/products/influxdb-cloud/)
2. Create a bucket named `cryptocurrency_data`
3. Generate an API token with read/write permissions

**Self-hosted InfluxDB:**
```bash
# Using Docker
docker run -d -p 8086:8086 \
  -v influxdb-storage:/var/lib/influxdb2 \
  influxdb:2.7

# Access the web UI at http://localhost:8086
```

### 2. Virtual Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create `.env` file from the template:

```bash
# Live Coin Watch API Configuration
LCW_API_KEY=your_api_key_here
LCW_BASE_URL=https://api.livecoinwatch.com

# InfluxDB Configuration
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_influxdb_token_here
INFLUXDB_ORG=your_organization_name
INFLUXDB_BUCKET=cryptocurrency_data

# Application Configuration
LOG_LEVEL=INFO
FETCH_INTERVAL_MINUTES=1
MAX_COINS_PER_FETCH=100
TRACKED_COINS=BTC,ETH,GLQ

# Scheduling Configuration
ENABLE_SCHEDULER=true
SCHEDULER_TIMEZONE=UTC
REQUESTS_PER_MINUTE=60
```

## Usage

### Command Line Interface

The application provides a comprehensive CLI:

```bash
python -m lcw_fetcher.main --help
```

#### Available Commands

**Check Status:**
```bash
# Check API and database connectivity
python -m lcw_fetcher.main status
```

**One-time Fetch:**
```bash
# Run a single data collection cycle
python -m lcw_fetcher.main run-once
```

**Start Scheduler:**
```bash
# Start automated data collection
python -m lcw_fetcher.main start
```

**Custom Fetch:**
```bash
# Fetch specific coins
python -m lcw_fetcher.main fetch --coin BTC --coin ETH

# Fetch top 50 coins
python -m lcw_fetcher.main fetch --limit 50
```

**View Configuration:**
```bash
# Display current configuration
python -m lcw_fetcher.main config
```

### Programmatic Usage

```python
from lcw_fetcher import Config, DataFetcher

# Load configuration
config = Config()

# Create fetcher instance
fetcher = DataFetcher(config)

# Fetch specific coins
coins = fetcher.fetch_specific_coins(['BTC', 'ETH'])

# Store in database
fetcher.store_coins(coins)
```

## Data Schema

### InfluxDB Measurements

#### `cryptocurrency_data`
- **Tags**: `code`, `name`, `currency`
- **Fields**: `rate`, `volume`, `market_cap`, `liquidity`, `rank`, `circulating_supply`, `delta_1h`, `delta_24h`, `delta_7d`, `delta_30d`
- **Timestamp**: Data fetch time

#### `exchange_data`
- **Tags**: `code`, `name`, `currency`
- **Fields**: `volume`, `visitors`, `volume_per_visitor`, `rank`
- **Timestamp**: Data fetch time

#### `market_overview`
- **Tags**: `currency`
- **Fields**: `total_market_cap`, `total_volume`, `total_liquidity`, `btc_dominance`
- **Timestamp**: Data fetch time

### Example Queries

```sql
-- Get latest Bitcoin price
SELECT last(rate) FROM cryptocurrency_data 
WHERE code = 'BTC' AND time >= now() - 1d

-- Get 24h price change for top 10 coins by market cap
SELECT mean(delta_24h) FROM cryptocurrency_data 
WHERE time >= now() - 1h 
GROUP BY code 
ORDER BY mean(market_cap) DESC 
LIMIT 10

-- Market cap trend over time
SELECT mean(total_market_cap) FROM market_overview 
WHERE time >= now() - 7d 
GROUP BY time(1h)
```

## Scheduling

The application supports multiple scheduling patterns:

### Default Schedule
- **Frequent Fetch**: Every 1 minute (real-time data collection)
- **Exchange Data**: Every hour
- **Historical Data**: Daily at 2:00 AM
- **Full Sync**: Weekly on Sunday at 3:00 AM

### Custom Scheduling
Modify scheduling in your configuration:

```python
# In your code
from lcw_fetcher.scheduler import DataScheduler

scheduler = DataScheduler(config)

# Add custom job
scheduler.scheduler.add_job(
    func=custom_function,
    trigger='cron',
    hour=6,
    minute=0,
    id='custom_job'
)
```

## Monitoring and Logging

### Log Files
- `logs/lcw_fetcher.log`: General application logs
- `logs/errors.log`: Error messages only
- `logs/api_calls.log`: Detailed API call logs

### Log Levels
Configure via `LOG_LEVEL` environment variable:
- `DEBUG`: Detailed debugging information
- `INFO`: General operational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages only
- `CRITICAL`: Critical errors only

### Monitoring API Usage
```bash
# Check API credits
python -m lcw_fetcher.main status

# Monitor logs in real-time
tail -f logs/lcw_fetcher.log
```

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LCW_API_KEY` | *required* | Live Coin Watch API key |
| `LCW_BASE_URL` | `https://api.livecoinwatch.com` | API base URL |
| `INFLUXDB_URL` | `http://localhost:8086` | InfluxDB server URL |
| `INFLUXDB_TOKEN` | *required* | InfluxDB authentication token |
| `INFLUXDB_ORG` | *required* | InfluxDB organization name |
| `INFLUXDB_BUCKET` | `cryptocurrency_data` | InfluxDB bucket name |
| `LOG_LEVEL` | `INFO` | Logging level |
| `FETCH_INTERVAL_MINUTES` | `5` | Legacy fetch interval (now uses 1-minute intervals) |
| `MAX_COINS_PER_FETCH` | `100` | Maximum coins per request |
| `TRACKED_COINS` | `BTC,ETH,GLQ` | Specific coins to track |
| `ENABLE_SCHEDULER` | `true` | Enable/disable scheduler |
| `SCHEDULER_TIMEZONE` | `UTC` | Scheduler timezone |
| `JOB_MISFIRE_GRACE_TIME` | `60` | Grace time in seconds for late job execution |
| `REQUESTS_PER_MINUTE` | `60` | API rate limit |

## Development

### Project Structure
```
lcw-fetch/
├── src/lcw_fetcher/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── fetcher.py           # Main data fetching logic
│   ├── scheduler.py         # Job scheduling
│   ├── api/
│   │   ├── client.py        # API client
│   │   └── exceptions.py    # API exceptions
│   ├── database/
│   │   └── influx_client.py # InfluxDB client
│   ├── models/
│   │   ├── coin.py          # Coin data models
│   │   ├── exchange.py      # Exchange models
│   │   └── market.py        # Market models
│   └── utils/
│       ├── config.py        # Configuration
│       └── logger.py        # Logging setup
├── config/                  # Configuration files
├── logs/                    # Log files
├── tests/                   # Unit tests
├── requirements.txt         # Python dependencies
├── setup.py                # Package setup
├── .env.example            # Environment template
└── README.md              # This file
```

### Running Tests
```bash
python -m pytest tests/
```

### Adding New Data Sources
1. Create model in `models/`
2. Add API methods to `api/client.py`
3. Update fetcher logic in `fetcher.py`
4. Add storage methods to `database/influx_client.py`

## Troubleshooting

### Common Issues

**API Rate Limiting:**
```
Error: API rate limit exceeded
```
- Solution: Reduce `REQUESTS_PER_MINUTE` or `FETCH_INTERVAL_MINUTES`

**Database Connection:**
```
Error: Failed to connect to InfluxDB
```
- Check `INFLUXDB_URL`, `INFLUXDB_TOKEN`, and `INFLUXDB_ORG`
- Ensure InfluxDB is running and accessible

**API Authentication:**
```
Error: Invalid API key
```
- Verify your `LCW_API_KEY` is correct
- Check API key permissions and quota

**Job Scheduling Misfire:**
```
Run time of job "JobName" was missed by X:XX:XX
```
- Increase `JOB_MISFIRE_GRACE_TIME` to allow more late execution time
- Check system load - jobs may be delayed due to high CPU usage
- Consider reducing fetch frequency if jobs consistently run late

### Debug Mode
```bash
python -m lcw_fetcher.main --log-level DEBUG status
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational and research purposes. Always respect API rate limits and terms of service. Cryptocurrency data can be volatile and should not be used as the sole basis for financial decisions.

## Support

- 📧 Email: [your.email@example.com]
- 🐛 Issues: [GitHub Issues]
- 📖 Documentation: [Project Wiki]

## Changelog

### v1.0.0
- Initial release
- Basic data fetching and storage
- Scheduling system
- CLI interface
- Comprehensive logging
