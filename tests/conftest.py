"""
Pytest configuration and fixtures for LCW API Fetcher tests.

This module provides common fixtures, test configurations, and utilities
used across all test modules.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

# Test environment setup
os.environ["LCW_API_KEY"] = "test_api_key"
os.environ["INFLUX_URL"] = "http://localhost:8086"
os.environ["INFLUX_TOKEN"] = "test_token"
os.environ["INFLUX_ORG"] = "test_org"
os.environ["INFLUX_BUCKET"] = "test_bucket"


@pytest.fixture
def mock_api_key():
    """Fixture for API key."""
    return "test_api_key_12345"


@pytest.fixture
def sample_coin_data():
    """Fixture providing sample coin data as returned by the LCW API."""
    return {
        "code": "BTC",
        "name": "Bitcoin",
        "symbol": "BTC",
        "rank": 1,
        "age": 5000,
        "color": "#f7931a",
        "png32": "https://lcw.nyc3.cdn.digitaloceanspaces.com/production/currencies/32/btc.png",
        "png64": "https://lcw.nyc3.cdn.digitaloceanspaces.com/production/currencies/64/btc.png",
        "webp32": "https://lcw.nyc3.cdn.digitaloceanspaces.com/production/currencies/32/btc.webp",
        "webp64": "https://lcw.nyc3.cdn.digitaloceanspaces.com/production/currencies/64/btc.webp",
        "exchanges": 420,
        "markets": 9821,
        "pairs": 3234,
        "rate": 45000.50,
        "volume": 28500000000.0,
        "cap": 850000000000.0,
        "liquidity": 125000000.0,
        "totalCap": 900000000000.0,
        "allTimeHighUSD": 69000.0,
        "circulatingSupply": 19000000.0,
        "totalSupply": 19500000.0,
        "maxSupply": 21000000.0,
        "categories": ["Currency", "Store of Value"],
        "delta": {
            "hour": 0.5,
            "day": 2.3,
            "week": -1.2,
            "month": 15.7,
            "quarter": 8.4,
            "year": 45.8
        },
        "currency": "USD",
        "fetched_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_exchange_data():
    """Fixture providing sample exchange data as returned by the LCW API."""
    return {
        "code": "binance",
        "name": "Binance",
        "png64": "https://lcw.nyc3.cdn.digitaloceanspaces.com/production/exchanges/64/binance.png",
        "webp64": "https://lcw.nyc3.cdn.digitaloceanspaces.com/production/exchanges/64/binance.webp",
        "centralized": True,
        "usCompliant": False,
        "volume": 15000000000.0,
        "bidTotal": 2500000.0,
        "askTotal": 2600000.0,
        "depth": 5100000.0,
        "visitors": 85000000,
        "volumePerVisitor": 176.47,
        "markets": 1534,
        "fiats": ["USD", "EUR", "GBP", "JPY"],
        "currency": "USD"
    }


@pytest.fixture
def sample_market_data():
    """Fixture providing sample market overview data."""
    return {
        "cap": 2500000000000.0,
        "volume": 95000000000.0,
        "liquidity": 8500000000.0,
        "btcDominance": 42.5,
        "currency": "USD"
    }


@pytest.fixture
def sample_coin_history_data():
    """Fixture providing sample historical coin data."""
    base_time = int(datetime.utcnow().timestamp() * 1000)
    return [
        {
            "date": base_time - 86400000,  # 1 day ago
            "rate": 44500.0,
            "volume": 27000000000.0,
            "cap": 840000000000.0
        },
        {
            "date": base_time - 43200000,  # 12 hours ago
            "rate": 44800.0,
            "volume": 28200000000.0,
            "cap": 845000000000.0
        },
        {
            "date": base_time,  # now
            "rate": 45000.0,
            "volume": 28500000000.0,
            "cap": 850000000000.0
        }
    ]


@pytest.fixture
def mock_requests_session():
    """Fixture providing a mock requests session."""
    session_mock = Mock()
    response_mock = Mock()
    response_mock.status_code = 200
    response_mock.json.return_value = {"status": "ok"}
    response_mock.raise_for_status = Mock()
    
    session_mock.post.return_value = response_mock
    session_mock.headers = {}
    session_mock.mount = Mock()
    
    return session_mock


@pytest.fixture
def mock_influxdb_client():
    """Fixture providing a mock InfluxDB client."""
    client_mock = Mock()
    
    # Mock write API
    write_api_mock = Mock()
    write_api_mock.write = Mock()
    client_mock.write_api.return_value = write_api_mock
    
    # Mock query API
    query_api_mock = Mock()
    client_mock.query_api.return_value = query_api_mock
    
    # Mock health check
    client_mock.health.return_value = {"status": "pass"}
    
    return client_mock


@pytest.fixture
def mock_influxdb_query_result():
    """Fixture providing mock InfluxDB query results."""
    class MockRecord:
        def __init__(self, time_val, code, field, value):
            self.values = {
                'code': code,
                '_field': field,
                '_value': value,
                '_time': time_val
            }
        
        def get_time(self):
            return self.values['_time']
        
        def get_field(self):
            return self.values['_field']
        
        def get_value(self):
            return self.values['_value']
    
    class MockTable:
        def __init__(self, records):
            self.records = records
    
    # Create mock records
    now = datetime.utcnow()
    records = [
        MockRecord(now, "BTC", "rate", 45000.0),
        MockRecord(now, "BTC", "volume", 28500000000.0),
        MockRecord(now, "ETH", "rate", 3200.0),
        MockRecord(now, "ETH", "volume", 15000000000.0),
    ]
    
    return [MockTable(records)]


@pytest.fixture
def temp_config_file(tmp_path):
    """Fixture providing a temporary configuration file."""
    config_content = """
LCW_API_KEY=test_key_123
INFLUX_URL=http://localhost:8086
INFLUX_TOKEN=test_token_456
INFLUX_ORG=test_org
INFLUX_BUCKET=test_bucket
LOG_LEVEL=DEBUG
FETCH_INTERVAL=300
"""
    config_file = tmp_path / ".env"
    config_file.write_text(config_content.strip())
    return str(config_file)


@pytest.fixture(scope="function", autouse=True)
def clean_environment():
    """Ensure clean environment for each test."""
    # Store original env vars
    original_env = os.environ.copy()
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


class MockDatetime:
    """Mock datetime class for testing time-dependent functionality."""
    
    def __init__(self, fixed_time=None):
        self.fixed_time = fixed_time or datetime(2024, 1, 15, 12, 0, 0)
    
    def utcnow(self):
        return self.fixed_time
    
    def now(self):
        return self.fixed_time


@pytest.fixture
def mock_datetime():
    """Fixture providing a mock datetime with fixed time."""
    return MockDatetime()


@pytest.fixture
def api_error_responses():
    """Fixture providing various API error responses for testing."""
    return {
        "rate_limit": {
            "status_code": 429,
            "response": {"error": {"code": 429, "description": "API rate limit exceeded"}}
        },
        "auth_error": {
            "status_code": 401,
            "response": {"error": {"code": 401, "description": "Invalid API key"}}
        },
        "server_error": {
            "status_code": 500,
            "response": {"error": {"code": 500, "description": "Internal server error"}}
        },
        "bad_request": {
            "status_code": 400,
            "response": {"error": {"code": 400, "description": "Bad request parameters"}}
        }
    }


# Custom assertions and utilities for tests
def assert_coin_data_valid(coin_data: Dict[str, Any]):
    """Custom assertion to validate coin data structure."""
    required_fields = ['rate', 'volume', 'cap']
    for field in required_fields:
        assert field in coin_data, f"Missing required field: {field}"
        if coin_data[field] is not None:
            assert isinstance(coin_data[field], (int, float)), f"Field {field} must be numeric"


def assert_influx_point_valid(point: Dict[str, Any]):
    """Custom assertion to validate InfluxDB point structure."""
    assert 'measurement' in point
    assert 'tags' in point
    assert 'fields' in point
    assert 'time' in point
    
    assert isinstance(point['tags'], dict)
    assert isinstance(point['fields'], dict)
    assert len(point['fields']) > 0, "Point must have at least one field"


# Test data generators
def generate_coins_list(count: int = 10) -> List[Dict[str, Any]]:
    """Generate a list of sample coin data for testing."""
    coins = []
    base_symbols = ["BTC", "ETH", "ADA", "DOT", "SOL", "AVAX", "MATIC", "ATOM", "LINK", "UNI"]
    
    for i in range(count):
        symbol = base_symbols[i % len(base_symbols)]
        coins.append({
            "code": symbol,
            "name": f"Test Coin {i+1}",
            "symbol": symbol,
            "rank": i + 1,
            "rate": 100.0 + (i * 50),
            "volume": 1000000000.0 + (i * 100000000),
            "cap": 10000000000.0 + (i * 1000000000),
            "currency": "USD"
        })
    
    return coins


def generate_exchanges_list(count: int = 5) -> List[Dict[str, Any]]:
    """Generate a list of sample exchange data for testing."""
    exchanges = []
    base_names = ["Binance", "Coinbase", "Kraken", "KuCoin", "Bitstamp"]
    
    for i in range(count):
        name = base_names[i % len(base_names)]
        exchanges.append({
            "code": name.lower(),
            "name": name,
            "centralized": True,
            "volume": 1000000000.0 + (i * 500000000),
            "visitors": 50000000 + (i * 10000000),
            "markets": 500 + (i * 100),
            "currency": "USD"
        })
    
    return exchanges


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (deselect with '-m \"not unit\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "api: marks tests that require API access"
    )
    config.addinivalue_line(
        "markers", "database: marks tests that require database access"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to all unit test files
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to integration test files
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.name.lower() for keyword in ["network", "api", "database"]):
            item.add_marker(pytest.mark.slow)
