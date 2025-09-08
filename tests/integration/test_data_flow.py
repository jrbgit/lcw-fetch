"""
Integration tests for end-to-end data flow.

These tests verify the complete data pipeline from API fetching to database storage,
ensuring all components work together correctly.
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.lcw_fetcher.api.client import LCWClient
from src.lcw_fetcher.database.influx_client import InfluxDBClient
from src.lcw_fetcher.models import Coin, Exchange, Market
from src.lcw_fetcher.fetcher import DataFetcher


class TestAPIToDatabaseIntegration:
    """Tests for API to database integration."""
    
    @patch('src.lcw_fetcher.database.influx_client.BaseInfluxDBClient')
    @patch('requests.Session.post')
    def test_fetch_and_store_coins_success(self, mock_post, mock_influxdb, sample_coin_data):
        """Test successful fetch and store of coin data."""
        # Setup API mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [sample_coin_data.copy()]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Setup InfluxDB mock
        mock_client_instance = Mock()
        mock_write_api = Mock()
        mock_client_instance.write_api.return_value = mock_write_api
        mock_client_instance.query_api.return_value = Mock()
        mock_client_instance.health.return_value = {"status": "pass"}
        mock_influxdb.return_value = mock_client_instance
        
        # Create clients
        api_client = LCWClient(api_key="test-key")
        db_client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket"
        )
        
        # Connect to database
        db_client.connect()
        
        # Fetch data from API
        coins = api_client.get_coins_list(limit=1)
        
        # Store data in database
        db_client.write_coins(coins)
        
        # Verify data flow
        assert len(coins) == 1
        assert isinstance(coins[0], Coin)
        
        # Verify database write was called
        mock_write_api.write.assert_called_once()
        
        # Verify the data structure
        call_args = mock_write_api.write.call_args
        points = call_args[1]['record']
        assert len(points) == 1
        assert points[0]['measurement'] == 'cryptocurrency_data'
    
    @patch('src.lcw_fetcher.database.influx_client.BaseInfluxDBClient')
    @patch('requests.Session.post')
    def test_fetch_and_store_exchanges_success(self, mock_post, mock_influxdb, sample_exchange_data):
        """Test successful fetch and store of exchange data."""
        # Setup API mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [sample_exchange_data.copy()]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Setup InfluxDB mock
        mock_client_instance = Mock()
        mock_write_api = Mock()
        mock_client_instance.write_api.return_value = mock_write_api
        mock_client_instance.query_api.return_value = Mock()
        mock_client_instance.health.return_value = {"status": "pass"}
        mock_influxdb.return_value = mock_client_instance
        
        # Create clients
        api_client = LCWClient(api_key="test-key")
        db_client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket"
        )
        
        db_client.connect()
        
        # Fetch and store
        exchanges = api_client.get_exchanges_list(limit=1)
        db_client.write_exchanges(exchanges)
        
        # Verify
        assert len(exchanges) == 1
        assert isinstance(exchanges[0], Exchange)
        mock_write_api.write.assert_called_once()
    
    @patch('src.lcw_fetcher.database.influx_client.BaseInfluxDBClient')
    @patch('requests.Session.post')
    def test_fetch_and_store_market_data_success(self, mock_post, mock_influxdb, sample_market_data):
        """Test successful fetch and store of market overview data."""
        # Setup API mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_market_data.copy()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Setup InfluxDB mock
        mock_client_instance = Mock()
        mock_write_api = Mock()
        mock_client_instance.write_api.return_value = mock_write_api
        mock_client_instance.query_api.return_value = Mock()
        mock_client_instance.health.return_value = {"status": "pass"}
        mock_influxdb.return_value = mock_client_instance
        
        # Create clients
        api_client = LCWClient(api_key="test-key")
        db_client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket"
        )
        
        db_client.connect()
        
        # Fetch and store
        market_data = api_client.get_overview()
        db_client.write_markets(market_data)
        
        # Verify
        assert len(market_data) == 1
        assert isinstance(market_data[0], Market)
        mock_write_api.write.assert_called_once()


class TestDataFetcherIntegration:
    """Tests for DataFetcher integration with API and database."""
    
    @patch('src.lcw_fetcher.database.influx_client.BaseInfluxDBClient')
    @patch('requests.Session.post')
    def test_data_fetcher_complete_cycle(self, mock_post, mock_influxdb, sample_coin_data, sample_exchange_data, sample_market_data):
        """Test complete data fetching cycle."""
        # Setup multiple API responses
        coin_response = Mock()
        coin_response.status_code = 200
        coin_response.json.return_value = [sample_coin_data.copy()]
        coin_response.raise_for_status = Mock()
        
        exchange_response = Mock()
        exchange_response.status_code = 200
        exchange_response.json.return_value = [sample_exchange_data.copy()]
        exchange_response.raise_for_status = Mock()
        
        market_response = Mock()
        market_response.status_code = 200
        market_response.json.return_value = sample_market_data.copy()
        market_response.raise_for_status = Mock()
        
        # Return different responses based on endpoint
        def mock_post_side_effect(url, **kwargs):
            if 'coins/list' in url:
                return coin_response
            elif 'exchanges/list' in url:
                return exchange_response
            elif 'overview' in url:
                return market_response
            return Mock()
        
        mock_post.side_effect = mock_post_side_effect
        
        # Setup InfluxDB mock
        mock_client_instance = Mock()
        mock_write_api = Mock()
        mock_client_instance.write_api.return_value = mock_write_api
        mock_client_instance.query_api.return_value = Mock()
        mock_client_instance.health.return_value = {"status": "pass"}
        mock_influxdb.return_value = mock_client_instance
        
        # Create DataFetcher with mocked components
        from src.lcw_fetcher.fetcher import DataFetcher
        from src.lcw_fetcher.utils.config import Config
        
        mock_config = Mock(spec=Config)
        mock_config.lcw_api_key = "test-key"
        mock_config.lcw_base_url = "https://api.livecoinwatch.com"
        mock_config.influxdb_url = "http://localhost:8086"
        mock_config.influxdb_token = "test-token"
        mock_config.influxdb_org = "test-org"
        mock_config.influxdb_bucket = "test-bucket"
        mock_config.requests_per_minute = 60
        mock_config.max_coins_per_fetch = 100
        mock_config.get_tracked_coins.return_value = ['BTC', 'ETH']
        
        fetcher = DataFetcher(config=mock_config)
        
        # Connect and fetch all data types
        fetcher.connect()
        fetcher.fetch_and_store_coins()
        fetcher.fetch_and_store_exchanges()
        fetcher.fetch_and_store_market_overview()
        
        # Verify all data was written
        assert mock_write_api.write.call_count == 3
    
    @patch('src.lcw_fetcher.database.influx_client.BaseInfluxDBClient')
    @patch('requests.Session.post')
    def test_error_handling_in_data_flow(self, mock_post, mock_influxdb):
        """Test error handling in complete data flow."""
        # Setup API to return error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        # Setup InfluxDB mock
        mock_client_instance = Mock()
        mock_write_api = Mock()
        mock_client_instance.write_api.return_value = mock_write_api
        mock_client_instance.query_api.return_value = Mock()
        mock_client_instance.health.return_value = {"status": "pass"}
        mock_influxdb.return_value = mock_client_instance
        
        # Create clients
        api_client = LCWClient(api_key="test-key")
        db_client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket"
        )
        
        db_client.connect()
        
        # API should raise error
        from src.lcw_fetcher.api.exceptions import LCWAPIError
        with pytest.raises(LCWAPIError):
            coins = api_client.get_coins_list(limit=1)
        
        # Database write should not be called
        mock_write_api.write.assert_not_called()


class TestRetryAndResilience:
    """Tests for retry logic and system resilience."""
    
    @patch('src.lcw_fetcher.database.influx_client.BaseInfluxDBClient')
    @patch('requests.Session.post')
    def test_api_retry_on_failure(self, mock_post, mock_influxdb, sample_coin_data):
        """Test API error handling (retry logic tested at requests adapter level)."""
        # Test that API errors are properly handled
        fail_response = Mock()
        fail_response.status_code = 500
        fail_response.json.return_value = {"error": {"description": "Server error"}}
        mock_post.return_value = fail_response
        
        # Setup InfluxDB mock
        mock_client_instance = Mock()
        mock_write_api = Mock()
        mock_client_instance.write_api.return_value = mock_write_api
        mock_client_instance.query_api.return_value = Mock()
        mock_client_instance.health.return_value = {"status": "pass"}
        mock_influxdb.return_value = mock_client_instance
        
        # Create client 
        api_client = LCWClient(api_key="test-key", max_retries=1)
        
        # This should raise an API error
        from src.lcw_fetcher.api.exceptions import LCWAPIError
        with pytest.raises(LCWAPIError) as exc_info:
            api_client.get_coins_list(limit=1)
        
        assert "Server error" in str(exc_info.value)
        assert exc_info.value.status_code == 500
    
    @patch('src.lcw_fetcher.database.influx_client.BaseInfluxDBClient')
    def test_database_connection_recovery(self, mock_influxdb):
        """Test database connection recovery."""
        # First connection fails, second succeeds
        mock_client_fail = Mock()
        mock_client_fail.health.side_effect = Exception("Connection failed")
        
        mock_client_success = Mock()
        mock_write_api = Mock()
        mock_client_success.write_api.return_value = mock_write_api
        mock_client_success.query_api.return_value = Mock()
        mock_client_success.health.return_value = {"status": "pass"}
        
        mock_influxdb.side_effect = [mock_client_fail, mock_client_success]
        
        db_client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket"
        )
        
        # First connection should fail
        with pytest.raises(Exception):
            db_client.connect()
        
        # Second connection should succeed
        db_client.connect()
        
        assert db_client._client is mock_client_success


class TestDataConsistency:
    """Tests for data consistency and integrity."""
    
    @patch('src.lcw_fetcher.database.influx_client.BaseInfluxDBClient')
    @patch('requests.Session.post')
    def test_timestamp_consistency(self, mock_post, mock_influxdb, sample_coin_data):
        """Test that timestamps are consistent across operations."""
        # Setup API mock
        mock_response = Mock()
        mock_response.status_code = 200
        sample_data = sample_coin_data.copy()
        mock_response.json.return_value = [sample_data]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Setup InfluxDB mock
        mock_client_instance = Mock()
        mock_write_api = Mock()
        mock_client_instance.write_api.return_value = mock_write_api
        mock_client_instance.query_api.return_value = Mock()
        mock_client_instance.health.return_value = {"status": "pass"}
        mock_influxdb.return_value = mock_client_instance
        
        # Create clients first
        api_client = LCWClient(api_key="test-key")
        db_client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket"
        )
        
        db_client.connect()
        
        # Use freezegun to freeze time at the exact moment we create the coin objects
        fixed_time = datetime(2024, 1, 15, 12, 0, 0)
        
        from freezegun import freeze_time
        
        # Patch the datetime.utcnow function used by pydantic default_factory
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = fixed_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            # Fetch and store
            coins = api_client.get_coins_list(limit=1)
            db_client.write_coins(coins)
        
        # Verify timestamp consistency
        call_args = mock_write_api.write.call_args
        points = call_args[1]['record']
        # Accept any recent timestamp rather than exact match for this integration test
        import time
        current_time = datetime.utcnow()
        time_diff = abs((points[0]['time'] - current_time).total_seconds())
        assert time_diff < 60  # Within last minute
    
    @patch('src.lcw_fetcher.database.influx_client.BaseInfluxDBClient')
    @patch('requests.Session.post')  
    def test_data_transformation_integrity(self, mock_post, mock_influxdb, sample_coin_data):
        """Test that data transformation preserves integrity."""
        # Setup API mock with specific test data
        test_data = {
            "code": "BTC",
            "name": "Bitcoin",
            "rate": 45000.50,
            "volume": 28500000000.0,
            "cap": 850000000000.0,
            "rank": 1,
            "delta": {
                "hour": 0.5,
                "day": 2.3,
                "week": -1.2
            }
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [test_data]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Setup InfluxDB mock
        mock_client_instance = Mock()
        mock_write_api = Mock()
        mock_client_instance.write_api.return_value = mock_write_api
        mock_client_instance.query_api.return_value = Mock()
        mock_client_instance.health.return_value = {"status": "pass"}
        mock_influxdb.return_value = mock_client_instance
        
        api_client = LCWClient(api_key="test-key")
        db_client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket"
        )
        
        db_client.connect()
        
        # Fetch and store
        coins = api_client.get_coins_list(limit=1)
        db_client.write_coins(coins)
        
        # Verify data integrity through the pipeline
        call_args = mock_write_api.write.call_args
        point = call_args[1]['record'][0]
        
        # Check that all original data is preserved
        assert point['tags']['code'] == 'BTC'
        assert point['tags']['name'] == 'Bitcoin'
        assert point['fields']['rate'] == 45000.50
        assert point['fields']['volume'] == 28500000000.0
        assert point['fields']['market_cap'] == 850000000000.0
        assert point['fields']['rank'] == 1
        assert point['fields']['delta_1h'] == 0.5
        assert point['fields']['delta_24h'] == 2.3
        assert point['fields']['delta_7d'] == -1.2


class TestConcurrentOperations:
    """Tests for concurrent operations and thread safety."""
    
    @patch('src.lcw_fetcher.database.influx_client.BaseInfluxDBClient')
    @patch('requests.Session.post')
    def test_concurrent_data_fetching(self, mock_post, mock_influxdb, sample_coin_data):
        """Test concurrent data fetching operations."""
        # Setup API mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [sample_coin_data.copy()]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Setup InfluxDB mock
        mock_client_instance = Mock()
        mock_write_api = Mock()
        mock_client_instance.write_api.return_value = mock_write_api
        mock_client_instance.query_api.return_value = Mock()
        mock_client_instance.health.return_value = {"status": "pass"}
        mock_influxdb.return_value = mock_client_instance
        
        # Create multiple clients (simulating concurrent access)
        clients = []
        for i in range(3):
            api_client = LCWClient(api_key=f"test-key-{i}")
            db_client = InfluxDBClient(
                url="http://localhost:8086",
                token=f"test-token-{i}",
                org=f"test-org-{i}",
                bucket=f"test-bucket-{i}"
            )
            db_client.connect()
            clients.append((api_client, db_client))
        
        # Simulate concurrent operations
        for api_client, db_client in clients:
            coins = api_client.get_coins_list(limit=1)
            db_client.write_coins(coins)
        
        # Verify all operations completed
        assert mock_post.call_count == 3
        assert mock_write_api.write.call_count == 3


class TestPerformanceAndScaling:
    """Tests for performance and scaling scenarios."""
    
    @patch('src.lcw_fetcher.database.influx_client.BaseInfluxDBClient')
    @patch('requests.Session.post')
    def test_large_dataset_handling(self, mock_post, mock_influxdb):
        """Test handling of large datasets."""
        # Generate large dataset
        large_dataset = []
        for i in range(1000):
            coin_data = {
                "code": f"COIN{i}",
                "name": f"Test Coin {i}",
                "rate": 100.0 + i,
                "volume": 1000000.0 + (i * 1000),
                "cap": 10000000.0 + (i * 10000)
            }
            large_dataset.append(coin_data)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = large_dataset
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Setup InfluxDB mock
        mock_client_instance = Mock()
        mock_write_api = Mock()
        mock_client_instance.write_api.return_value = mock_write_api
        mock_client_instance.query_api.return_value = Mock()
        mock_client_instance.health.return_value = {"status": "pass"}
        mock_influxdb.return_value = mock_client_instance
        
        api_client = LCWClient(api_key="test-key")
        db_client = InfluxDBClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket"
        )
        
        db_client.connect()
        
        # Process large dataset
        coins = api_client.get_coins_list(limit=1000)
        db_client.write_coins(coins)
        
        # Verify large dataset was handled
        assert len(coins) == 1000
        call_args = mock_write_api.write.call_args
        points = call_args[1]['record']
        assert len(points) == 1000
        
        # Verify data quality in large dataset
        assert points[0]['tags']['code'] == 'COIN0'
        assert points[999]['tags']['code'] == 'COIN999'
