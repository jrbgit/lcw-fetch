import json
import time
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models import Coin, Exchange, Market, CoinHistory
from .exceptions import LCWAPIError, LCWRateLimitError, LCWAuthError, LCWNetworkError


class LCWClient:
    """Live Coin Watch API client"""
    
    def __init__(
        self, 
        api_key: str, 
        base_url: str = "https://api.livecoinwatch.com",
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]  # LCW API uses POST for everything
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'x-api-key': self.api_key
        })
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to the LCW API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.post(
                url, 
                json=payload or {}, 
                timeout=self.timeout
            )
            
            # Handle different error cases
            if response.status_code == 401:
                raise LCWAuthError("Invalid API key", response.status_code)
            elif response.status_code == 429:
                raise LCWRateLimitError("API rate limit exceeded", response.status_code)
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('description', f"HTTP {response.status_code}")
                except:
                    error_msg = f"HTTP {response.status_code}"
                raise LCWAPIError(error_msg, response.status_code)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise LCWNetworkError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise LCWNetworkError("Connection error")
        except requests.exceptions.RequestException as e:
            raise LCWNetworkError(f"Request failed: {str(e)}")
    
    def check_status(self) -> Dict[str, Any]:
        """Check API status"""
        return self._make_request('status')
    
    def get_credits(self) -> Dict[str, Any]:
        """Get remaining API credits"""
        return self._make_request('credits')
    
    def get_coin_single(self, code: str, currency: str = "USD", meta: bool = True) -> Coin:
        """Get single coin data"""
        payload = {
            "currency": currency,
            "code": code.upper(),
            "meta": meta
        }
        
        data = self._make_request('coins/single', payload)
        data['currency'] = currency
        data['code'] = code.upper()  # Add the code field since API doesn't return it
        return Coin(**data)
    
    def get_coin_history(
        self, 
        code: str, 
        start: Union[int, datetime], 
        end: Union[int, datetime], 
        currency: str = "USD",
        meta: bool = True
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
            "meta": meta
        }
        
        data = self._make_request('coins/single/history', payload)
        data['currency'] = currency
        return Coin(**data)
    
    def get_coins_list(
        self,
        currency: str = "USD",
        sort: str = "rank",
        order: str = "ascending",
        offset: int = 0,
        limit: int = 100,
        meta: bool = False
    ) -> List[Coin]:
        """Get list of coins"""
        payload = {
            "currency": currency,
            "sort": sort,
            "order": order,
            "offset": offset,
            "limit": limit,
            "meta": meta
        }
        
        data = self._make_request('coins/list', payload)
        coins = []
        
        for coin_data in data:
            coin_data['currency'] = currency
            coins.append(Coin(**coin_data))
        
        return coins
    
    def get_exchanges_list(
        self,
        currency: str = "USD",
        sort: str = "visitors",
        order: str = "descending",
        offset: int = 0,
        limit: int = 50,
        meta: bool = False
    ) -> List[Exchange]:
        """Get list of exchanges"""
        payload = {
            "currency": currency,
            "sort": sort,
            "order": order,
            "offset": offset,
            "limit": limit,
            "meta": meta
        }
        
        data = self._make_request('exchanges/list', payload)
        exchanges = []
        
        for exchange_data in data:
            exchange_data['currency'] = currency
            exchanges.append(Exchange(**exchange_data))
        
        return exchanges
    
    def get_overview(
        self,
        currency: str = "USD"
    ) -> List[Market]:
        """Get market overview data"""
        payload = {
            "currency": currency
        }
        
        data = self._make_request('overview', payload)
        
        # The overview endpoint returns a single dict, not a list
        if isinstance(data, dict):
            data['currency'] = currency
            return [Market(**data)]
        else:
            # Handle case where it might return a list
            markets = []
            for market_data in data:
                market_data['currency'] = currency
                markets.append(Market(**market_data))
            return markets
    
    def get_overview_history(
        self,
        start: Union[int, datetime],
        end: Union[int, datetime],
        currency: str = "USD"
    ) -> List[Market]:
        """Get historical market overview data"""
        # Convert datetime to timestamp if needed
        if isinstance(start, datetime):
            start = int(start.timestamp() * 1000)
        if isinstance(end, datetime):
            end = int(end.timestamp() * 1000)
        
        payload = {
            "currency": currency,
            "start": start,
            "end": end
        }
        
        data = self._make_request('overview/history', payload)
        markets = []
        
        for market_data in data:
            market_data['currency'] = currency
            markets.append(Market(**market_data))
        
        return markets
    
    def get_fiats_all(self) -> List[Dict[str, Any]]:
        """Get all available fiat currencies"""
        return self._make_request('fiats/all')
    
    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
