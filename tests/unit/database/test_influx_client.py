"""
Unit tests for the InfluxDB client.

Tests cover database connection, write operations, queries, error handling,
and data management functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from influxdb_client import InfluxDBClient as BaseInfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.domain.write_precision import WritePrecision

from src.lcw_fetcher.database.influx_client import InfluxDBClient
from src.lcw_fetcher.models import Coin, Exchange, Market
from tests.conftest import generate_coins_list, generate_exchanges_list


class TestInfluxDBClientInit:
    """Tests for InfluxDBClient initialization."""

    def test_client_init_with_required_params(self):
        """Test client initialization with required parameters."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        assert client.url == "http://localhost:8086"
        assert client.token == "test-token"
        assert client.org == "test-org"
        assert client.bucket == "test-bucket"
        assert client.timeout == 10000  # Default timeout

        # Client should not be connected initially
        assert client._client is None
        assert client._write_api is None
        assert client._query_api is None

    def test_client_init_with_custom_timeout(self):
        """Test client initialization with custom timeout."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
            timeout=5000,
        )

        assert client.timeout == 5000


class TestInfluxDBClientConnection:
    """Tests for database connection management."""

    @patch("src.lcw_fetcher.database.influx_client.BaseInfluxDBClient")
    def test_connect_success(self, mock_base_client):
        """Test successful database connection."""
        # Setup mock client
        mock_client_instance = Mock()
        mock_write_api = Mock()
        mock_query_api = Mock()

        mock_client_instance.write_api.return_value = mock_write_api
        mock_client_instance.query_api.return_value = mock_query_api
        mock_client_instance.health.return_value = {"status": "pass"}

        mock_base_client.return_value = mock_client_instance

        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        client.connect()

        # Verify connection was established
        assert client._client is mock_client_instance
        assert client._write_api is mock_write_api
        assert client._query_api is mock_query_api

        # Verify BaseInfluxDBClient was called with correct params
        mock_base_client.assert_called_once_with(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            timeout=10000,
        )

        # Verify health check was called
        mock_client_instance.health.assert_called_once()

    @patch("src.lcw_fetcher.database.influx_client.BaseInfluxDBClient")
    def test_connect_failure(self, mock_base_client):
        """Test database connection failure."""
        mock_base_client.side_effect = InfluxDBError(message="Connection failed")

        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        with pytest.raises(InfluxDBError):
            client.connect()

        # Client should remain unconnected
        assert client._client is None
        assert client._write_api is None
        assert client._query_api is None

    @patch("src.lcw_fetcher.database.influx_client.BaseInfluxDBClient")
    def test_connect_health_check_failure(self, mock_base_client):
        """Test connection failure during health check."""
        mock_client_instance = Mock()
        mock_client_instance.health.side_effect = Exception("Health check failed")
        mock_base_client.return_value = mock_client_instance

        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        with pytest.raises(Exception) as exc_info:
            client.connect()

        assert "Health check failed" in str(exc_info.value)

    def test_disconnect(self):
        """Test database disconnection."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        # Set up as if connected
        mock_client = Mock()
        client._client = mock_client
        client._write_api = Mock()
        client._query_api = Mock()

        client.disconnect()

        # Verify client was closed and references cleared
        mock_client.close.assert_called_once()
        assert client._client is None
        assert client._write_api is None
        assert client._query_api is None

    def test_disconnect_when_not_connected(self):
        """Test disconnecting when not connected."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        # Should not raise exception
        client.disconnect()

        assert client._client is None


class TestInfluxDBClientWriteOperations:
    """Tests for database write operations."""

    def setup_connected_client(self):
        """Helper to set up a connected client."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        # Mock connected state
        client._client = Mock()
        client._write_api = Mock()
        client._query_api = Mock()

        return client

    def test_write_coins_success(self, sample_coin_data):
        """Test successful coin data writing."""
        client = self.setup_connected_client()

        coins = [Coin(**sample_coin_data)]
        client.write_coins(coins)

        # Verify write API was called
        client._write_api.write.assert_called_once()

        call_args = client._write_api.write.call_args
        assert call_args[1]["bucket"] == "test-bucket"
        assert call_args[1]["org"] == "test-org"
        assert call_args[1]["write_precision"] == WritePrecision.MS

        # Verify the points were converted properly
        points = call_args[1]["record"]
        assert len(points) == 1
        assert points[0]["measurement"] == "cryptocurrency_data"

    def test_write_coins_multiple(self):
        """Test writing multiple coin records."""
        client = self.setup_connected_client()

        coin_data_list = generate_coins_list(5)
        coins = [Coin(**coin_data) for coin_data in coin_data_list]

        client.write_coins(coins)

        call_args = client._write_api.write.call_args
        points = call_args[1]["record"]
        assert len(points) == 5

    def test_write_coins_not_connected(self):
        """Test writing coins when not connected."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        coins = [Coin(code="BTC", rate=45000.0)]

        with pytest.raises(RuntimeError) as exc_info:
            client.write_coins(coins)

        assert "InfluxDB client not connected" in str(exc_info.value)

    def test_write_coins_database_error(self, sample_coin_data):
        """Test handling database error during coin write."""
        client = self.setup_connected_client()
        client._write_api.write.side_effect = InfluxDBError(message="Write failed")

        coins = [Coin(**sample_coin_data)]

        with pytest.raises(InfluxDBError):
            client.write_coins(coins)

    def test_write_exchanges_success(self, sample_exchange_data):
        """Test successful exchange data writing."""
        client = self.setup_connected_client()

        exchanges = [Exchange(**sample_exchange_data)]
        client.write_exchanges(exchanges)

        client._write_api.write.assert_called_once()

        call_args = client._write_api.write.call_args
        points = call_args[1]["record"]
        assert len(points) == 1
        assert points[0]["measurement"] == "exchange_data"

    def test_write_exchanges_multiple(self):
        """Test writing multiple exchange records."""
        client = self.setup_connected_client()

        exchange_data_list = generate_exchanges_list(3)
        exchanges = [Exchange(**exchange_data) for exchange_data in exchange_data_list]

        client.write_exchanges(exchanges)

        call_args = client._write_api.write.call_args
        points = call_args[1]["record"]
        assert len(points) == 3

    def test_write_markets_success(self, sample_market_data):
        """Test successful market data writing."""
        client = self.setup_connected_client()

        markets = [Market(**sample_market_data)]
        client.write_markets(markets)

        client._write_api.write.assert_called_once()

        call_args = client._write_api.write.call_args
        points = call_args[1]["record"]
        assert len(points) == 1
        assert points[0]["measurement"] == "market_overview"

    def test_write_empty_lists(self):
        """Test writing empty lists."""
        client = self.setup_connected_client()

        # Should still call write with empty list
        client.write_coins([])
        client._write_api.write.assert_called_once_with(
            bucket="test-bucket",
            org="test-org",
            record=[],
            write_precision=WritePrecision.MS,
        )


class TestInfluxDBClientQueryOperations:
    """Tests for database query operations."""

    def setup_connected_client(self):
        """Helper to set up a connected client."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        client._client = Mock()
        client._write_api = Mock()
        client._query_api = Mock()

        return client

    def test_query_latest_coins_success(self, mock_influxdb_query_result):
        """Test successful query of latest coin data."""
        client = self.setup_connected_client()
        client._query_api.query.return_value = mock_influxdb_query_result

        result = client.query_latest_coins(limit=50)

        assert isinstance(result, list)
        assert len(result) == 4  # Based on mock data

        # Verify query was called with correct parameters
        client._query_api.query.assert_called_once()
        call_args = client._query_api.query.call_args

        assert "test-bucket" in call_args[1]["query"]
        assert "cryptocurrency_data" in call_args[1]["query"]
        assert "limit(n: 50)" in call_args[1]["query"]
        assert call_args[1]["org"] == "test-org"

    def test_query_latest_coins_default_limit(self, mock_influxdb_query_result):
        """Test query with default limit."""
        client = self.setup_connected_client()
        client._query_api.query.return_value = mock_influxdb_query_result

        client.query_latest_coins()

        call_args = client._query_api.query.call_args
        assert "limit(n: 100)" in call_args[1]["query"]

    def test_query_latest_coins_not_connected(self):
        """Test querying when not connected."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        with pytest.raises(RuntimeError) as exc_info:
            client.query_latest_coins()

        assert "InfluxDB client not connected" in str(exc_info.value)

    def test_query_latest_coins_database_error(self):
        """Test handling database error during query."""
        client = self.setup_connected_client()
        client._query_api.query.side_effect = InfluxDBError(message="Query failed")

        with pytest.raises(InfluxDBError):
            client.query_latest_coins()

    def test_query_coin_history_success(self, mock_influxdb_query_result):
        """Test successful coin history query."""
        client = self.setup_connected_client()
        client._query_api.query.return_value = mock_influxdb_query_result

        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 2)

        result = client.query_coin_history("BTC", start_time, end_time)

        assert isinstance(result, list)

        # Verify query construction
        call_args = client._query_api.query.call_args
        query_str = call_args[1]["query"]

        assert "test-bucket" in query_str
        assert "cryptocurrency_data" in query_str
        assert "BTC" in query_str
        assert "2024-01-01T00:00:00Z" in query_str
        assert "2024-01-02T00:00:00Z" in query_str
        assert "pivot" in query_str

    def test_query_coin_history_lowercase_code(self, mock_influxdb_query_result):
        """Test coin history query with lowercase coin code."""
        client = self.setup_connected_client()
        client._query_api.query.return_value = mock_influxdb_query_result

        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 2)

        client.query_coin_history("btc", start_time, end_time)

        call_args = client._query_api.query.call_args
        query_str = call_args[1]["query"]

        # Code should be converted to uppercase
        assert "BTC" in query_str
        assert "btc" not in query_str

    def test_get_database_stats_success(self):
        """Test getting database statistics."""
        client = self.setup_connected_client()

        # Mock query results for stats
        mock_result = []
        client._query_api.query.return_value = mock_result

        result = client.get_database_stats()

        assert isinstance(result, dict)

        # Should have called query API multiple times for different stats
        assert client._query_api.query.call_count >= 1


class TestInfluxDBClientErrorHandling:
    """Tests for error handling in various scenarios."""

    def test_write_with_invalid_data(self):
        """Test writing with invalid data objects."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        client._client = Mock()
        client._write_api = Mock()
        client._query_api = Mock()

        # Create coin with invalid to_influx_point method
        invalid_coin = Mock()
        invalid_coin.to_influx_point.side_effect = Exception("Conversion error")

        with pytest.raises(Exception) as exc_info:
            client.write_coins([invalid_coin])

        assert "Conversion error" in str(exc_info.value)

    def test_connection_lost_during_operation(self):
        """Test handling connection loss during operation."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        # Set up as connected but with failing write API
        client._client = Mock()
        client._write_api = Mock()
        client._write_api.write.side_effect = ConnectionError("Connection lost")
        client._query_api = Mock()

        coin = Coin(code="BTC", rate=45000.0)

        with pytest.raises(ConnectionError):
            client.write_coins([coin])

    def test_query_with_malformed_results(self):
        """Test handling malformed query results."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        client._client = Mock()
        client._write_api = Mock()
        client._query_api = Mock()

        # Mock malformed result
        malformed_result = [Mock()]
        malformed_result[0].records = [Mock()]
        malformed_result[0].records[0].get_time.side_effect = AttributeError("No time")

        client._query_api.query.return_value = malformed_result

        with pytest.raises(AttributeError):
            client.query_latest_coins()


class TestInfluxDBClientEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_large_batch_write(self):
        """Test writing very large batches of data."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        client._client = Mock()
        client._write_api = Mock()
        client._query_api = Mock()

        # Create a large number of coins
        large_coin_list = generate_coins_list(1000)
        coins = [Coin(**coin_data) for coin_data in large_coin_list]

        client.write_coins(coins)

        call_args = client._write_api.write.call_args
        points = call_args[1]["record"]
        assert len(points) == 1000

    def test_empty_query_results(self):
        """Test handling empty query results."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        client._client = Mock()
        client._write_api = Mock()
        client._query_api = Mock()
        client._query_api.query.return_value = []  # Empty result

        result = client.query_latest_coins()

        assert result == []

    def test_special_characters_in_coin_code(self):
        """Test handling special characters in coin codes."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        client._client = Mock()
        client._write_api = Mock()
        client._query_api = Mock()
        client._query_api.query.return_value = []

        # Test with special characters
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 2)

        # Should not raise exception
        client.query_coin_history("BTC-USD", start_time, end_time)

        call_args = client._query_api.query.call_args
        query_str = call_args[1]["query"]
        assert "BTC-USD" in query_str

    def test_unicode_in_data(self):
        """Test handling Unicode characters in data."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        client._client = Mock()
        client._write_api = Mock()
        client._query_api = Mock()

        # Create coin with Unicode name
        coin = Coin(code="测试", name="测试币", rate=1000.0)  # Chinese characters

        # Should not raise exception
        client.write_coins([coin])

        call_args = client._write_api.write.call_args
        points = call_args[1]["record"]
        assert points[0]["tags"]["code"] == "测试"
        assert points[0]["tags"]["name"] == "测试币"

    def test_very_long_time_range_query(self):
        """Test querying with very long time ranges."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        client._client = Mock()
        client._write_api = Mock()
        client._query_api = Mock()
        client._query_api.query.return_value = []

        # Very long time range (1 year)
        start_time = datetime(2023, 1, 1)
        end_time = datetime(2024, 1, 1)

        client.query_coin_history("BTC", start_time, end_time)

        # Should construct query without issues
        client._query_api.query.assert_called_once()

    def test_concurrent_operations_mock(self):
        """Test that client can handle concurrent operations (mocked)."""
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
        )

        client._client = Mock()
        client._write_api = Mock()
        client._query_api = Mock()
        client._query_api.query.return_value = []

        # Simulate concurrent writes and reads
        coin = Coin(code="BTC", rate=45000.0)

        client.write_coins([coin])
        client.query_latest_coins()
        client.write_coins([coin])

        assert client._write_api.write.call_count == 2
        assert client._query_api.query.call_count == 1
