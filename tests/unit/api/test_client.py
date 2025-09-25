"""
Unit tests for the LCW API client.

Tests cover API client functionality, request handling, error handling,
retry logic, and response processing.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout

from src.lcw_fetcher.api.client import LCWClient
from src.lcw_fetcher.api.exceptions import (
    LCWAPIError,
    LCWAuthError,
    LCWNetworkError,
    LCWRateLimitError,
)
from src.lcw_fetcher.models import Coin, Exchange, Market


class TestLCWClientInit:
    """Tests for LCWClient initialization."""

    def test_client_init_default_params(self, mock_api_key):
        """Test client initialization with default parameters."""
        client = LCWClient(api_key=mock_api_key)

        assert client.api_key == mock_api_key
        assert client.base_url == "https://api.livecoinwatch.com"
        assert client.timeout == 30
        assert isinstance(client.session, requests.Session)

    def test_client_init_custom_params(self, mock_api_key):
        """Test client initialization with custom parameters."""
        custom_url = "https://custom-api.example.com"
        custom_timeout = 60
        max_retries = 5

        client = LCWClient(
            api_key=mock_api_key,
            base_url=custom_url,
            timeout=custom_timeout,
            max_retries=max_retries,
        )

        assert client.api_key == mock_api_key
        assert client.base_url == custom_url
        assert client.timeout == custom_timeout

    def test_client_base_url_trailing_slash_removed(self, mock_api_key):
        """Test that trailing slash is removed from base URL."""
        client = LCWClient(
            api_key=mock_api_key, base_url="https://api.livecoinwatch.com/"
        )

        assert client.base_url == "https://api.livecoinwatch.com"

    def test_client_session_headers(self, mock_api_key):
        """Test that session headers are set correctly."""
        client = LCWClient(api_key=mock_api_key)

        assert client.session.headers["Content-Type"] == "application/json"
        assert client.session.headers["x-api-key"] == mock_api_key


class TestLCWClientMakeRequest:
    """Tests for the _make_request method."""

    @patch("requests.Session.post")
    def test_make_request_success(self, mock_post, mock_api_key):
        """Test successful API request."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        client = LCWClient(api_key=mock_api_key)
        result = client._make_request("test-endpoint", {"test": "payload"})

        assert result == {"status": "success"}
        mock_post.assert_called_once()

        # Check the call arguments
        args, kwargs = mock_post.call_args
        assert "test-endpoint" in args[0]
        assert kwargs["json"] == {"test": "payload"}
        assert kwargs["timeout"] == 30

    @patch("requests.Session.post")
    def test_make_request_no_payload(self, mock_post, mock_api_key):
        """Test API request without payload."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        client = LCWClient(api_key=mock_api_key)
        result = client._make_request("test-endpoint")

        # Should use empty dict as payload
        args, kwargs = mock_post.call_args
        assert kwargs["json"] == {}

    @patch("requests.Session.post")
    def test_make_request_endpoint_leading_slash(self, mock_post, mock_api_key):
        """Test that leading slash is stripped from endpoint."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        client = LCWClient(api_key=mock_api_key)
        client._make_request("/test-endpoint")

        # Check that URL was constructed correctly
        args, kwargs = mock_post.call_args
        expected_url = "https://api.livecoinwatch.com/test-endpoint"
        assert args[0] == expected_url

    @patch("requests.Session.post")
    def test_make_request_auth_error(self, mock_post, mock_api_key):
        """Test handling of authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        client = LCWClient(api_key=mock_api_key)

        with pytest.raises(LCWAuthError) as exc_info:
            client._make_request("test-endpoint")

        assert "Invalid API key" in str(exc_info.value)
        assert exc_info.value.status_code == 401

    @patch("requests.Session.post")
    def test_make_request_rate_limit_error(self, mock_post, mock_api_key):
        """Test handling of rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        client = LCWClient(api_key=mock_api_key)

        with pytest.raises(LCWRateLimitError) as exc_info:
            client._make_request("test-endpoint")

        assert "API rate limit exceeded" in str(exc_info.value)
        assert exc_info.value.status_code == 429

    @patch("requests.Session.post")
    def test_make_request_api_error_with_json(self, mock_post, mock_api_key):
        """Test handling of API error with JSON error response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {"description": "Invalid parameters"}
        }
        mock_post.return_value = mock_response

        client = LCWClient(api_key=mock_api_key)

        with pytest.raises(LCWAPIError) as exc_info:
            client._make_request("test-endpoint")

        assert "Invalid parameters" in str(exc_info.value)
        assert exc_info.value.status_code == 400

    @patch("requests.Session.post")
    def test_make_request_api_error_without_json(self, mock_post, mock_api_key):
        """Test handling of API error without JSON error response."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("No JSON")
        mock_post.return_value = mock_response

        client = LCWClient(api_key=mock_api_key)

        with pytest.raises(LCWAPIError) as exc_info:
            client._make_request("test-endpoint")

        assert "HTTP 500" in str(exc_info.value)
        assert exc_info.value.status_code == 500

    @patch("requests.Session.post")
    def test_make_request_timeout_error(self, mock_post, mock_api_key):
        """Test handling of timeout error."""
        mock_post.side_effect = Timeout("Request timeout")

        client = LCWClient(api_key=mock_api_key)

        with pytest.raises(LCWNetworkError) as exc_info:
            client._make_request("test-endpoint")

        assert "Request timeout" in str(exc_info.value)

    @patch("requests.Session.post")
    def test_make_request_connection_error(self, mock_post, mock_api_key):
        """Test handling of connection error."""
        mock_post.side_effect = ConnectionError("Connection failed")

        client = LCWClient(api_key=mock_api_key)

        with pytest.raises(LCWNetworkError) as exc_info:
            client._make_request("test-endpoint")

        assert "Connection error" in str(exc_info.value)

    @patch("requests.Session.post")
    def test_make_request_generic_request_error(self, mock_post, mock_api_key):
        """Test handling of generic request error."""
        mock_post.side_effect = requests.exceptions.RequestException("Generic error")

        client = LCWClient(api_key=mock_api_key)

        with pytest.raises(LCWNetworkError) as exc_info:
            client._make_request("test-endpoint")

        assert "Request failed: Generic error" in str(exc_info.value)


class TestLCWClientStatusMethods:
    """Tests for status and credits methods."""

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_check_status(self, mock_make_request, mock_api_key):
        """Test check_status method."""
        expected_response = {"status": "ok", "timestamp": 1642204800}
        mock_make_request.return_value = expected_response

        client = LCWClient(api_key=mock_api_key)
        result = client.check_status()

        assert result == expected_response
        mock_make_request.assert_called_once_with("status")

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_get_credits(self, mock_make_request, mock_api_key):
        """Test get_credits method."""
        expected_response = {"credits": 9500, "remaining": 500}
        mock_make_request.return_value = expected_response

        client = LCWClient(api_key=mock_api_key)
        result = client.get_credits()

        assert result == expected_response
        mock_make_request.assert_called_once_with("credits")


class TestLCWClientCoinMethods:
    """Tests for coin-related methods."""

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_get_coin_single(self, mock_make_request, mock_api_key, sample_coin_data):
        """Test get_coin_single method."""
        # Remove fields that are added by the client
        api_response = sample_coin_data.copy()
        api_response.pop("currency", None)
        api_response.pop("code", None)

        mock_make_request.return_value = api_response

        client = LCWClient(api_key=mock_api_key)
        result = client.get_coin_single("BTC", currency="USD", meta=True)

        assert isinstance(result, Coin)
        assert result.code == "BTC"
        assert result.currency == "USD"

        # Check the API call
        expected_payload = {"currency": "USD", "code": "BTC", "meta": True}
        mock_make_request.assert_called_once_with("coins/single", expected_payload)

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_get_coin_single_default_params(
        self, mock_make_request, mock_api_key, sample_coin_data
    ):
        """Test get_coin_single method with default parameters."""
        api_response = sample_coin_data.copy()
        api_response.pop("currency", None)
        api_response.pop("code", None)

        mock_make_request.return_value = api_response

        client = LCWClient(api_key=mock_api_key)
        result = client.get_coin_single("btc")  # Lowercase should be converted

        assert isinstance(result, Coin)
        assert result.code == "BTC"
        assert result.currency == "USD"

        # Check the API call with defaults
        expected_payload = {"currency": "USD", "code": "BTC", "meta": True}
        mock_make_request.assert_called_once_with("coins/single", expected_payload)

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_get_coin_history_with_datetime(
        self, mock_make_request, mock_api_key, sample_coin_data
    ):
        """Test get_coin_history method with datetime objects."""
        api_response = sample_coin_data.copy()
        api_response.pop("currency", None)

        mock_make_request.return_value = api_response

        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 2, 0, 0, 0)

        client = LCWClient(api_key=mock_api_key)
        result = client.get_coin_history("BTC", start_time, end_time)

        assert isinstance(result, Coin)
        assert result.currency == "USD"

        # Check the API call - timestamps should be converted to milliseconds
        expected_payload = {
            "currency": "USD",
            "code": "BTC",
            "start": int(start_time.timestamp() * 1000),
            "end": int(end_time.timestamp() * 1000),
            "meta": True,
        }
        mock_make_request.assert_called_once_with(
            "coins/single/history", expected_payload
        )

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_get_coin_history_with_timestamps(
        self, mock_make_request, mock_api_key, sample_coin_data
    ):
        """Test get_coin_history method with timestamp integers."""
        api_response = sample_coin_data.copy()
        api_response.pop("currency", None)

        mock_make_request.return_value = api_response

        start_timestamp = 1640995200000  # 2022-01-01 in milliseconds
        end_timestamp = 1641081600000  # 2022-01-02 in milliseconds

        client = LCWClient(api_key=mock_api_key)
        result = client.get_coin_history(
            "BTC", start_timestamp, end_timestamp, currency="EUR"
        )

        assert isinstance(result, Coin)
        assert result.currency == "EUR"

        expected_payload = {
            "currency": "EUR",
            "code": "BTC",
            "start": start_timestamp,
            "end": end_timestamp,
            "meta": True,
        }
        mock_make_request.assert_called_once_with(
            "coins/single/history", expected_payload
        )

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_get_coins_list(self, mock_make_request, mock_api_key, sample_coin_data):
        """Test get_coins_list method."""
        # Create list of coin data
        coin_list = [sample_coin_data.copy() for _ in range(3)]
        for i, coin in enumerate(coin_list):
            coin["code"] = f"COIN{i+1}"
            coin.pop("currency", None)  # Remove currency as it's added by client

        mock_make_request.return_value = coin_list

        client = LCWClient(api_key=mock_api_key)
        result = client.get_coins_list(
            currency="EUR",
            sort="volume",
            order="descending",
            offset=10,
            limit=50,
            meta=True,
        )

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(coin, Coin) for coin in result)
        assert all(coin.currency == "EUR" for coin in result)

        expected_payload = {
            "currency": "EUR",
            "sort": "volume",
            "order": "descending",
            "offset": 10,
            "limit": 50,
            "meta": True,
        }
        mock_make_request.assert_called_once_with("coins/list", expected_payload)

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_get_coins_list_default_params(
        self, mock_make_request, mock_api_key, sample_coin_data
    ):
        """Test get_coins_list method with default parameters."""
        coin_list = [sample_coin_data.copy()]
        coin_list[0].pop("currency", None)

        mock_make_request.return_value = coin_list

        client = LCWClient(api_key=mock_api_key)
        result = client.get_coins_list()

        assert len(result) == 1

        expected_payload = {
            "currency": "USD",
            "sort": "rank",
            "order": "ascending",
            "offset": 0,
            "limit": 100,
            "meta": False,
        }
        mock_make_request.assert_called_once_with("coins/list", expected_payload)


class TestLCWClientExchangeMethods:
    """Tests for exchange-related methods."""

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_get_exchanges_list(
        self, mock_make_request, mock_api_key, sample_exchange_data
    ):
        """Test get_exchanges_list method."""
        exchange_list = [sample_exchange_data.copy() for _ in range(2)]
        for i, exchange in enumerate(exchange_list):
            exchange["code"] = f"exchange{i+1}"
            exchange.pop("currency", None)

        mock_make_request.return_value = exchange_list

        client = LCWClient(api_key=mock_api_key)
        result = client.get_exchanges_list(
            currency="EUR",
            sort="volume",
            order="ascending",
            offset=5,
            limit=25,
            meta=True,
        )

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(exchange, Exchange) for exchange in result)
        assert all(exchange.currency == "EUR" for exchange in result)

        expected_payload = {
            "currency": "EUR",
            "sort": "volume",
            "order": "ascending",
            "offset": 5,
            "limit": 25,
            "meta": True,
        }
        mock_make_request.assert_called_once_with("exchanges/list", expected_payload)

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_get_exchanges_list_default_params(
        self, mock_make_request, mock_api_key, sample_exchange_data
    ):
        """Test get_exchanges_list method with default parameters."""
        exchange_list = [sample_exchange_data.copy()]
        exchange_list[0].pop("currency", None)

        mock_make_request.return_value = exchange_list

        client = LCWClient(api_key=mock_api_key)
        result = client.get_exchanges_list()

        assert len(result) == 1

        expected_payload = {
            "currency": "USD",
            "sort": "visitors",
            "order": "descending",
            "offset": 0,
            "limit": 50,
            "meta": False,
        }
        mock_make_request.assert_called_once_with("exchanges/list", expected_payload)


class TestLCWClientMarketMethods:
    """Tests for market overview methods."""

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_get_overview_dict_response(
        self, mock_make_request, mock_api_key, sample_market_data
    ):
        """Test get_overview method when API returns dict."""
        api_response = sample_market_data.copy()
        api_response.pop("currency", None)

        mock_make_request.return_value = api_response

        client = LCWClient(api_key=mock_api_key)
        result = client.get_overview(currency="EUR")

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Market)
        assert result[0].currency == "EUR"

        expected_payload = {"currency": "EUR"}
        mock_make_request.assert_called_once_with("overview", expected_payload)

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_get_overview_list_response(
        self, mock_make_request, mock_api_key, sample_market_data
    ):
        """Test get_overview method when API returns list."""
        api_response = [sample_market_data.copy() for _ in range(2)]
        for market in api_response:
            market.pop("currency", None)

        mock_make_request.return_value = api_response

        client = LCWClient(api_key=mock_api_key)
        result = client.get_overview()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(market, Market) for market in result)
        assert all(market.currency == "USD" for market in result)

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_get_overview_default_currency(
        self, mock_make_request, mock_api_key, sample_market_data
    ):
        """Test get_overview method with default currency."""
        api_response = sample_market_data.copy()
        api_response.pop("currency", None)

        mock_make_request.return_value = api_response

        client = LCWClient(api_key=mock_api_key)
        result = client.get_overview()

        assert result[0].currency == "USD"

        expected_payload = {"currency": "USD"}
        mock_make_request.assert_called_once_with("overview", expected_payload)


class TestLCWClientEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_client_with_empty_api_key(self):
        """Test client initialization with empty API key."""
        client = LCWClient(api_key="")
        assert client.api_key == ""
        assert client.session.headers["x-api-key"] == ""

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_coin_methods_with_empty_response(self, mock_make_request, mock_api_key):
        """Test coin methods with empty API response."""
        mock_make_request.return_value = []

        client = LCWClient(api_key=mock_api_key)
        result = client.get_coins_list()

        assert result == []

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_exchange_methods_with_empty_response(
        self, mock_make_request, mock_api_key
    ):
        """Test exchange methods with empty API response."""
        mock_make_request.return_value = []

        client = LCWClient(api_key=mock_api_key)
        result = client.get_exchanges_list()

        assert result == []

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_coin_single_with_missing_fields(self, mock_make_request, mock_api_key):
        """Test get_coin_single with minimal API response."""
        # Minimal response with only required fields for Coin model
        minimal_response = {"name": "Bitcoin", "rate": 45000.0}
        mock_make_request.return_value = minimal_response

        client = LCWClient(api_key=mock_api_key)
        result = client.get_coin_single("BTC")

        assert isinstance(result, Coin)
        assert result.code == "BTC"
        assert result.name == "Bitcoin"
        assert result.rate == 45000.0

    def test_client_str_representation(self, mock_api_key):
        """Test string representation of client doesn't expose API key."""
        client = LCWClient(api_key=mock_api_key)
        client_str = str(client)

        # API key should not be in string representation for security
        assert mock_api_key not in client_str
        assert "LCWClient" in client_str

    @patch("src.lcw_fetcher.api.client.LCWClient._make_request")
    def test_special_characters_in_coin_code(
        self, mock_make_request, mock_api_key, sample_coin_data
    ):
        """Test handling of special characters in coin codes."""
        api_response = sample_coin_data.copy()
        api_response.pop("currency", None)
        api_response.pop("code", None)

        mock_make_request.return_value = api_response

        client = LCWClient(api_key=mock_api_key)
        result = client.get_coin_single("BTC-USD")  # Hypothetical pair code

        assert result.code == "BTC-USD"
