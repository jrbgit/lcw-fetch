# Testing Guide

This document provides comprehensive information about testing the LCW API Fetcher application.

## Table of Contents

- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Writing Tests](#writing-tests)
- [Test Configuration](#test-configuration)
- [Continuous Integration](#continuous-integration)
- [Coverage Reports](#coverage-reports)
- [Troubleshooting](#troubleshooting)

## Test Structure

The test suite is organized into the following structure:

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── api/                    # API client tests
│   │   ├── __init__.py
│   │   ├── test_client.py      # LCW API client tests
│   │   └── test_exceptions.py  # API exception tests
│   ├── database/               # Database client tests
│   │   ├── __init__.py
│   │   └── test_influx_client.py
│   └── models/                 # Data model tests
│       ├── __init__.py
│       ├── test_coin.py        # Coin model tests
│       ├── test_exchange.py    # Exchange model tests
│       └── test_market.py      # Market model tests
└── integration/                # Integration tests
    ├── __init__.py
    └── test_data_flow.py       # End-to-end data flow tests
```

## Running Tests

### Prerequisites

1. Install test dependencies:
   ```bash
   pip install -r requirements-test.txt
   ```

2. Set up environment variables:
   ```bash
   export LCW_API_KEY="your_test_api_key"
   export INFLUX_URL="http://localhost:8086"
   export INFLUX_TOKEN="your_test_token"
   export INFLUX_ORG="test_org"
   export INFLUX_BUCKET="test_bucket"
   ```

### Basic Test Execution

Run all tests:
```bash
pytest
```

Run only unit tests:
```bash
pytest tests/unit/
```

Run only integration tests:
```bash
pytest tests/integration/
```

Run tests with verbose output:
```bash
pytest -v
```

Run tests with coverage:
```bash
pytest --cov=src --cov-report=html --cov-report=term
```

### Advanced Test Options

Run tests in parallel:
```bash
pytest -n auto  # Uses all available CPU cores
pytest -n 4     # Uses 4 processes
```

Run specific test categories:
```bash
pytest -m unit           # Run only unit tests
pytest -m integration    # Run only integration tests  
pytest -m "not slow"     # Skip slow tests
pytest -m api            # Run only API-related tests
pytest -m database       # Run only database tests
```

Run tests with specific output formats:
```bash
pytest --tb=short        # Short traceback format
pytest --tb=line         # One line per failure
pytest --tb=no           # No traceback
pytest --html=report.html # Generate HTML report
```

Filter tests by name:
```bash
pytest -k "test_coin"    # Run tests with "test_coin" in name
pytest -k "not slow"     # Skip tests with "slow" in name
```

## Test Categories

Tests are organized using pytest markers:

### Available Markers

- `@pytest.mark.unit` - Unit tests that test individual components in isolation
- `@pytest.mark.integration` - Integration tests that test component interactions
- `@pytest.mark.slow` - Tests that may take longer to run
- `@pytest.mark.api` - Tests that require API access
- `@pytest.mark.database` - Tests that require database access

### Example Usage

```python
import pytest

@pytest.mark.unit
def test_coin_model_validation():
    """Unit test for coin model validation."""
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_complete_data_pipeline():
    """Integration test for complete data pipeline."""
    pass
```

## Writing Tests

### Test File Naming

- Test files must start with `test_` or end with `_test.py`
- Test functions must start with `test_`
- Test classes must start with `Test`

### Using Fixtures

Common fixtures are available in `conftest.py`:

```python
def test_api_client(mock_api_key):
    """Test using the mock API key fixture."""
    client = LCWClient(api_key=mock_api_key)
    assert client.api_key == mock_api_key

def test_coin_model(sample_coin_data):
    """Test using sample coin data fixture."""
    coin = Coin(**sample_coin_data)
    assert coin.code == "BTC"
```

### Mocking External Dependencies

Use `unittest.mock` or `pytest-mock` for mocking:

```python
from unittest.mock import Mock, patch
import pytest

@patch('requests.Session.post')
def test_api_call(mock_post):
    """Test API call with mocked HTTP request."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success"}
    mock_post.return_value = mock_response
    
    # Your test code here
```

### Testing Exceptions

```python
def test_invalid_api_key():
    """Test that invalid API key raises appropriate exception."""
    with pytest.raises(LCWAuthError):
        client = LCWClient(api_key="invalid")
        client.check_status()
```

### Parameterized Tests

```python
@pytest.mark.parametrize("coin_code,expected", [
    ("btc", "BTC"),
    ("eth", "ETH"),
    ("ada", "ADA")
])
def test_coin_code_normalization(coin_code, expected):
    """Test coin code normalization with multiple inputs."""
    result = normalize_coin_code(coin_code)
    assert result == expected
```

## Test Configuration

### Pytest Configuration

Configuration is in `pytest.ini`:

```ini
[tool:pytest]
minversion = 6.0
addopts = -ra -q --strict-markers --strict-config
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    api: Tests requiring API access
    database: Tests requiring database access
```

### Coverage Configuration

Coverage settings are in `.coveragerc`:

```ini
[run]
source = src/
omit = */tests/*

[report]
fail_under = 80
show_missing = True
```

## Continuous Integration

### GitHub Actions

The CI pipeline runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

### CI Pipeline Steps

1. **Environment Setup**
   - Set up Python matrix (3.10, 3.11, 3.12)
   - Start InfluxDB service
   - Install dependencies

2. **Code Quality**
   - Linting with flake8
   - Code formatting check with black
   - Import sorting check with isort
   - Type checking with mypy

3. **Testing**
   - Run unit tests with coverage
   - Run integration tests
   - Generate coverage reports

4. **Security**
   - Security analysis with bandit
   - Dependency vulnerability check with safety

5. **Build & Deploy**
   - Build Python package
   - Build Docker image
   - Deploy to production (on main branch)

### Environment Variables for CI

Set these secrets in your GitHub repository:

```
LCW_API_KEY          # Live Coin Watch API key
DOCKERHUB_USERNAME   # Docker Hub username  
DOCKERHUB_TOKEN      # Docker Hub access token
```

## Coverage Reports

### Generating Reports

Generate HTML coverage report:
```bash
pytest --cov=src --cov-report=html
```

Generate XML coverage report (for CI):
```bash
pytest --cov=src --cov-report=xml
```

Generate terminal coverage report:
```bash
pytest --cov=src --cov-report=term-missing
```

### Coverage Goals

- **Minimum Coverage**: 80%
- **Target Coverage**: 90%+
- **Critical Components**: 95%+ (API client, database client, data models)

### Viewing Reports

HTML reports are generated in `htmlcov/index.html`:
```bash
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Install package in development mode
pip install -e .
```

#### 2. Database Connection Issues
```bash
# Start InfluxDB container
docker run -d -p 8086:8086 influxdb:2.7

# Wait for database to be ready
curl -f http://localhost:8086/ping
```

#### 3. Missing Environment Variables
```bash
# Set required environment variables
export LCW_API_KEY="your_api_key"
export INFLUX_URL="http://localhost:8086"
# ... other variables
```

#### 4. Test Isolation Issues
```bash
# Run tests with fresh imports
pytest --forked

# Run tests in random order
pytest --random-order
```

#### 5. Slow Tests
```bash
# Skip slow tests during development
pytest -m "not slow"

# Run tests in parallel
pytest -n auto
```

### Debugging Tests

Enable detailed output:
```bash
pytest -vv --tb=long --capture=no
```

Use pytest debugger:
```python
def test_something():
    import pytest; pytest.set_trace()
    # Your test code here
```

Use standard debugger:
```bash
pytest --pdb  # Drop to debugger on first failure
pytest --pdbcls=IPython.terminal.debugger:Pdb  # Use IPython debugger
```

### Performance Testing

Run performance benchmarks:
```bash
pytest --benchmark-only
```

Profile test execution:
```bash
pytest --profile
```

## Best Practices

### Test Design

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **One Assertion Per Test**: Keep tests focused
3. **Descriptive Names**: Use clear, descriptive test names
4. **Independent Tests**: Tests should not depend on each other
5. **Fast Tests**: Keep unit tests fast, use integration tests for complex scenarios

### Mock Usage

1. **Mock External Dependencies**: Always mock API calls, database connections
2. **Use Fixtures**: Reuse common mock setups via fixtures
3. **Verify Interactions**: Assert that mocks were called correctly
4. **Realistic Mocks**: Make mocks behave like real dependencies

### Test Data

1. **Use Factories**: Create test data with factory_boy or similar
2. **Minimal Data**: Use minimal data that satisfies test requirements
3. **Edge Cases**: Test boundary conditions and edge cases
4. **Invalid Data**: Test error handling with invalid inputs

### Maintenance

1. **Keep Tests Updated**: Update tests when code changes
2. **Remove Dead Tests**: Delete tests for removed functionality
3. **Refactor Tests**: Refactor tests when they become hard to maintain
4. **Monitor Coverage**: Regularly check and improve test coverage

For more specific testing questions or issues, please refer to the project documentation or create an issue in the repository.
