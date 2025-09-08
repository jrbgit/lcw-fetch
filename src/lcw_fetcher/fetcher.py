import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from loguru import logger

from .api import LCWClient, LCWAPIError, LCWRateLimitError
from .database import InfluxDBClient
from .models import Coin, Exchange, Market
from .utils import Config


class DataFetcher:
    """Main service for fetching and storing cryptocurrency data"""
    
    def __init__(self, config: Config):
        self.config = config
        self.lcw_client = LCWClient(
            api_key=config.lcw_api_key,
            base_url=config.lcw_base_url
        )
        self.db_client = InfluxDBClient(
            url=config.influxdb_url,
            token=config.influxdb_token,
            org=config.influxdb_org,
            bucket=config.influxdb_bucket
        )
        
        # Rate limiting
        self._last_request_time = 0
        self._request_interval = 60.0 / config.requests_per_minute
        
    def _rate_limit(self) -> None:
        """Implement rate limiting between API requests"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._request_interval:
            sleep_time = self._request_interval - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self._last_request_time = time.time()
    
    def check_api_status(self) -> bool:
        """Check if the LCW API is accessible"""
        try:
            self._rate_limit()
            status = self.lcw_client.check_status()
            logger.info("API status check successful")
            return True
        except Exception as e:
            logger.error(f"API status check failed: {e}")
            return False
    
    def get_api_credits(self) -> Optional[Dict[str, Any]]:
        """Get remaining API credits"""
        try:
            self._rate_limit()
            credits = self.lcw_client.get_credits()
            logger.info(f"API credits remaining: {credits.get('dailyCreditsRemaining', 'unknown')}")
            return credits
        except Exception as e:
            logger.error(f"Failed to get API credits: {e}")
            return None
    
    def fetch_coins_list(self, limit: Optional[int] = None) -> List[Coin]:
        """Fetch list of coins from the API"""
        if limit is None:
            limit = self.config.max_coins_per_fetch
        
        coins = []
        try:
            self._rate_limit()
            coins = self.lcw_client.get_coins_list(
                limit=limit,
                meta=True
            )
            logger.info(f"Fetched {len(coins)} coins from API")
            return coins
            
        except LCWRateLimitError:
            logger.warning("Rate limit exceeded, backing off")
            time.sleep(60)  # Wait 1 minute
            return []
        except LCWAPIError as e:
            logger.error(f"API error while fetching coins: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while fetching coins: {e}")
            return []
    
    def fetch_specific_coins(self, coin_codes: List[str]) -> List[Coin]:
        """Fetch specific coins by their codes"""
        coins = []
        
        for code in coin_codes:
            try:
                self._rate_limit()
                coin = self.lcw_client.get_coin_single(code=code, meta=True)
                coins.append(coin)
                logger.debug(f"Fetched data for {code}")
                
            except LCWRateLimitError:
                logger.warning("Rate limit exceeded, backing off")
                time.sleep(60)
                continue
            except LCWAPIError as e:
                logger.error(f"API error while fetching {code}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error while fetching {code}: {e}")
                continue
        
        logger.info(f"Fetched data for {len(coins)} specific coins")
        return coins
    
    def fetch_exchanges_list(self, limit: int = 50) -> List[Exchange]:
        """Fetch list of exchanges from the API"""
        try:
            self._rate_limit()
            exchanges = self.lcw_client.get_exchanges_list(limit=limit)
            logger.info(f"Fetched {len(exchanges)} exchanges from API")
            return exchanges
            
        except LCWRateLimitError:
            logger.warning("Rate limit exceeded while fetching exchanges")
            time.sleep(60)
            return []
        except LCWAPIError as e:
            logger.error(f"API error while fetching exchanges: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while fetching exchanges: {e}")
            return []
    
    def fetch_market_overview(self) -> List[Market]:
        """Fetch market overview data"""
        try:
            self._rate_limit()
            markets = self.lcw_client.get_overview()
            logger.info(f"Fetched {len(markets)} market overview records")
            return markets
            
        except LCWRateLimitError:
            logger.warning("Rate limit exceeded while fetching market overview")
            time.sleep(60)
            return []
        except LCWAPIError as e:
            logger.error(f"API error while fetching market overview: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while fetching market overview: {e}")
            return []
    
    def fetch_coin_history(
        self, 
        code: str, 
        hours_back: int = 24
    ) -> Optional[Coin]:
        """Fetch historical data for a specific coin"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        try:
            self._rate_limit()
            coin_with_history = self.lcw_client.get_coin_history(
                code=code,
                start=start_time,
                end=end_time,
                meta=True
            )
            logger.info(f"Fetched {len(coin_with_history.history)} historical records for {code}")
            return coin_with_history
            
        except LCWRateLimitError:
            logger.warning(f"Rate limit exceeded while fetching history for {code}")
            time.sleep(60)
            return None
        except LCWAPIError as e:
            logger.error(f"API error while fetching history for {code}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while fetching history for {code}: {e}")
            return None
    
    def store_coins(self, coins: List[Coin]) -> bool:
        """Store coin data in the database"""
        if not coins:
            return True
        
        try:
            with self.db_client as db:
                db.write_coins(coins)
            logger.info(f"Stored {len(coins)} coins in database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store coins in database: {e}")
            return False
    
    def store_exchanges(self, exchanges: List[Exchange]) -> bool:
        """Store exchange data in the database"""
        if not exchanges:
            return True
        
        try:
            with self.db_client as db:
                db.write_exchanges(exchanges)
            logger.info(f"Stored {len(exchanges)} exchanges in database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store exchanges in database: {e}")
            return False
    
    def store_markets(self, markets: List[Market]) -> bool:
        """Store market data in the database"""
        if not markets:
            return True
        
        try:
            with self.db_client as db:
                db.write_markets(markets)
            logger.info(f"Stored {len(markets)} market records in database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store market data in database: {e}")
            return False
    
    def run_full_fetch(self) -> Dict[str, int]:
        """Run a complete data fetch cycle"""
        logger.info("Starting full fetch cycle")
        start_time = datetime.utcnow()
        
        stats = {
            'coins_fetched': 0,
            'coins_stored': 0,
            'exchanges_fetched': 0,
            'exchanges_stored': 0,
            'markets_fetched': 0,
            'markets_stored': 0,
            'errors': 0
        }
        
        # Check API status first
        if not self.check_api_status():
            logger.error("API is not available, skipping fetch cycle")
            stats['errors'] += 1
            return stats
        
        # Get API credits
        credits = self.get_api_credits()
        if credits and credits.get('dailyCreditsRemaining', 0) < 10:
            logger.warning("Low API credits remaining, consider reducing fetch frequency")
        
        # Fetch tracked coins specifically
        tracked_coins = self.config.get_tracked_coins()
        if tracked_coins:
            coins = self.fetch_specific_coins(tracked_coins)
            stats['coins_fetched'] = len(coins)
            
            if self.store_coins(coins):
                stats['coins_stored'] = len(coins)
            else:
                stats['errors'] += 1
        
        # Fetch top coins list
        top_coins = self.fetch_coins_list(limit=20)  # Just top 20 for regular updates
        if top_coins:
            stats['coins_fetched'] += len(top_coins)
            
            if self.store_coins(top_coins):
                stats['coins_stored'] += len(top_coins)
            else:
                stats['errors'] += 1
        
        # Fetch exchanges (less frequently)
        exchanges = self.fetch_exchanges_list(limit=20)
        if exchanges:
            stats['exchanges_fetched'] = len(exchanges)
            
            if self.store_exchanges(exchanges):
                stats['exchanges_stored'] = len(exchanges)
            else:
                stats['errors'] += 1
        
        # Fetch market overview
        markets = self.fetch_market_overview()
        if markets:
            stats['markets_fetched'] = len(markets)
            
            if self.store_markets(markets):
                stats['markets_stored'] = len(markets)
            else:
                stats['errors'] += 1
        
        elapsed = datetime.utcnow() - start_time
        logger.info(f"Full fetch cycle completed in {elapsed.total_seconds():.2f} seconds")
        logger.info(f"Stats: {stats}")
        
        return stats
    
    def connect(self) -> None:
        """Connect to database"""
        try:
            self.db_client.connect()
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def fetch_and_store_coins(self) -> bool:
        """Fetch and store coin data"""
        coins = self.fetch_coins_list()
        if coins:
            return self.store_coins(coins)
        return True
    
    def fetch_and_store_exchanges(self) -> bool:
        """Fetch and store exchange data"""
        exchanges = self.fetch_exchanges_list()
        if exchanges:
            return self.store_exchanges(exchanges)
        return True
    
    def fetch_and_store_market_overview(self) -> bool:
        """Fetch and store market overview data"""
        markets = self.fetch_market_overview()
        if markets:
            return self.store_markets(markets)
        return True
    
    def close(self) -> None:
        """Close all connections"""
        if self.lcw_client:
            self.lcw_client.close()
        if hasattr(self.db_client, 'close'):
            self.db_client.disconnect()
        # db_client closes automatically when used as context manager
