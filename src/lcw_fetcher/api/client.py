import json
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models import Coin, CoinHistory, Exchange, Market
from ..utils.cache import api_cache
from .exceptions import LCWAPIError, LCWAuthError, LCWNetworkError, LCWRateLimitError


class CircuitBreakerState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Simple circuit breaker implementation"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED

    def can_execute(self) -> bool:
        """Check if request can be executed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self):
        """Record successful request"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


class LCWClient:
    """Live Coin Watch API client with enhanced error handling"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.livecoinwatch.com",
        connect_timeout: int = 10,
        read_timeout: int = 30,
        max_retries: int = 3,
        enable_caching: bool = True,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.timeout = (connect_timeout, read_timeout)  # (connect, read)
        self.enable_caching = enable_caching

        # Circuit breaker for API health
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

        # Setup session with enhanced retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=2,  # Exponential backoff: 2, 4, 8 seconds
            status_forcelist=[429, 500, 502, 503, 504, 520, 521, 522, 523, 524],
            allowed_methods=["POST"],  # LCW API uses POST for everything
            raise_on_status=False,  # Handle status codes manually
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=2, pool_maxsize=5
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Default headers
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "User-Agent": "LCW-DataFetcher/1.0",
            }
        )

    def _make_request(
        self, endpoint: str, payload: Dict[str, Any] = None, use_cache: bool = True
    ) -> Dict[str, Any]:
        """Make a request to the LCW API with circuit breaker, caching, and enhanced error handling"""
        # Try cache first if enabled
        if self.enable_caching and use_cache:
            cached_response = api_cache.get_cached_response(endpoint, payload or {})
            if cached_response is not None:
                logger.debug(f"Using cached response for endpoint: {endpoint}")
                return cached_response

        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            raise LCWAPIError(
                "Circuit breaker is open - API temporarily unavailable", 503
            )

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_start_time = time.time()

        try:
            logger.debug(f"Making API request to: {endpoint}")

            response = self.session.post(url, json=payload or {}, timeout=self.timeout)

            request_duration = time.time() - request_start_time
            logger.debug(f"API request completed in {request_duration:.2f}s")

            # Handle different error cases
            if response.status_code == 401:
                self.circuit_breaker.record_failure()
                raise LCWAuthError("Invalid API key", response.status_code)
            elif response.status_code == 429:
                # Don't count rate limits as circuit breaker failures
                logger.warning(f"Rate limit hit for endpoint: {endpoint}")
                raise LCWRateLimitError("API rate limit exceeded", response.status_code)
            elif response.status_code >= 500:
                # Server errors count as failures
                self.circuit_breaker.record_failure()
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get(
                        "description", f"HTTP {response.status_code}"
                    )
                except:
                    error_msg = f"Server error: HTTP {response.status_code}"
                raise LCWAPIError(error_msg, response.status_code)
            elif response.status_code >= 400:
                # Client errors don't count as circuit breaker failures
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get(
                        "description", f"HTTP {response.status_code}"
                    )
                except:
                    error_msg = f"Client error: HTTP {response.status_code}"
                raise LCWAPIError(error_msg, response.status_code)

            response.raise_for_status()

            # Success - reset circuit breaker
            self.circuit_breaker.record_success()

            response_data = response.json()

            # Cache the response if caching is enabled
            if self.enable_caching and use_cache and response_data:
                api_cache.cache_response(endpoint, payload or {}, response_data)

            return response_data

        except requests.exceptions.Timeout as e:
            self.circuit_breaker.record_failure()
            request_duration = time.time() - request_start_time
            logger.error(
                f"Request timeout after {request_duration:.2f}s for endpoint: {endpoint}"
            )
            raise LCWNetworkError(
                f"Request timeout ({request_duration:.1f}s) - check network connection"
            )
        except requests.exceptions.ConnectionError as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Connection error for endpoint: {endpoint} - {str(e)}")
            raise LCWNetworkError(f"Connection error - check network connectivity")
        except requests.exceptions.RequestException as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Request failed for endpoint: {endpoint} - {str(e)}")
            raise LCWNetworkError(f"Request failed: {str(e)}")

    def check_status(self) -> Dict[str, Any]:
        """Check API status (cached for 2 minutes)"""
        return self._make_request("status")

    def get_credits(self) -> Dict[str, Any]:
        """Get remaining API credits (cached for 5 minutes)"""
        return self._make_request("credits")

    def get_coin_single(
        self, code: str, currency: str = "USD", meta: bool = True
    ) -> Coin:
        """Get single coin data"""
        payload = {"currency": currency, "code": code.upper(), "meta": meta}

        data = self._make_request("coins/single", payload)
        data["currency"] = currency
        data["code"] = code.upper()  # Add the code field since API doesn't return it
        return Coin(**data)

    def get_coin_history(
        self,
        code: str,
        start: Union[int, datetime],
        end: Union[int, datetime],
        currency: str = "USD",
        meta: bool = True,
    ) -> Coin:
        """Get historical data for a coin"""
        # Convert datetime to timestamp if needed
        if isinstance(start, datetime):
            start = int(start.timestamp() * 1000)
        if isinstance(end, datetime):
            end = int(end.timestamp() * 1000)

        payload = {
            "currency": currency,
            "code": code.upper(),
            "start": start,
            "end": end,
            "meta": meta,
        }

        data = self._make_request("coins/single/history", payload)
        data["currency"] = currency
        return Coin(**data)

    def get_coins_list(
        self,
        currency: str = "USD",
        sort: str = "rank",
        order: str = "ascending",
        offset: int = 0,
        limit: int = 100,
        meta: bool = False,
    ) -> List[Coin]:
        """Get list of coins"""
        payload = {
            "currency": currency,
            "sort": sort,
            "order": order,
            "offset": offset,
            "limit": limit,
            "meta": meta,
        }

        data = self._make_request("coins/list", payload)
        coins = []

        for coin_data in data:
            coin_data["currency"] = currency
            coins.append(Coin(**coin_data))

        return coins

    def get_exchanges_list(
        self,
        currency: str = "USD",
        sort: str = "visitors",
        order: str = "descending",
        offset: int = 0,
        limit: int = 50,
        meta: bool = False,
    ) -> List[Exchange]:
        """Get list of exchanges"""
        payload = {
            "currency": currency,
            "sort": sort,
            "order": order,
            "offset": offset,
            "limit": limit,
            "meta": meta,
        }

        data = self._make_request("exchanges/list", payload)
        exchanges = []

        for exchange_data in data:
            exchange_data["currency"] = currency
            exchanges.append(Exchange(**exchange_data))

        return exchanges

    def get_overview(self, currency: str = "USD") -> List[Market]:
        """Get market overview data"""
        payload = {"currency": currency}

        data = self._make_request("overview", payload)

        # The overview endpoint returns a single dict, not a list
        if isinstance(data, dict):
            data["currency"] = currency
            return [Market(**data)]
        else:
            # Handle case where it might return a list
            markets = []
            for market_data in data:
                market_data["currency"] = currency
                markets.append(Market(**market_data))
            return markets

    def get_overview_history(
        self,
        start: Union[int, datetime],
        end: Union[int, datetime],
        currency: str = "USD",
    ) -> List[Market]:
        """Get historical market overview data"""
        # Convert datetime to timestamp if needed
        if isinstance(start, datetime):
            start = int(start.timestamp() * 1000)
        if isinstance(end, datetime):
            end = int(end.timestamp() * 1000)

        payload = {"currency": currency, "start": start, "end": end}

        data = self._make_request("overview/history", payload)
        markets = []

        for market_data in data:
            market_data["currency"] = currency
            markets.append(Market(**market_data))

        return markets

    def get_fiats_all(self) -> List[Dict[str, Any]]:
        """Get all available fiat currencies"""
        return self._make_request("fiats/all")

    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
