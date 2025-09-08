import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from influxdb_client import InfluxDBClient as BaseInfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.domain.write_precision import WritePrecision

from ..models import Coin, Exchange, Market


logger = logging.getLogger(__name__)


class InfluxDBClient:
    """InfluxDB client for storing cryptocurrency time series data"""
    
    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        bucket: str,
        timeout: int = 10000
    ):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.timeout = timeout
        
        self._client = None
        self._write_api = None
        self._query_api = None
    
    def connect(self) -> None:
        """Establish connection to InfluxDB"""
        try:
            self._client = BaseInfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org,
                timeout=self.timeout
            )
            self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
            self._query_api = self._client.query_api()
            
            # Test connection
            self._client.health()
            logger.info("Connected to InfluxDB successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close connection to InfluxDB"""
        if self._client:
            self._client.close()
            self._client = None
            self._write_api = None
            self._query_api = None
            logger.info("Disconnected from InfluxDB")
    
    def write_coins(self, coins: List[Coin]) -> None:
        """Write coin data to InfluxDB"""
        if not self._write_api:
            raise RuntimeError("InfluxDB client not connected")
        
        try:
            points = [coin.to_influx_point() for coin in coins]
            self._write_api.write(
                bucket=self.bucket,
                org=self.org,
                record=points,
                write_precision=WritePrecision.MS
            )
            logger.info(f"Successfully wrote {len(coins)} coin records to InfluxDB")
            
        except Exception as e:
            logger.error(f"Failed to write coin data to InfluxDB: {e}")
            raise
    
    def write_exchanges(self, exchanges: List[Exchange]) -> None:
        """Write exchange data to InfluxDB"""
        if not self._write_api:
            raise RuntimeError("InfluxDB client not connected")
        
        try:
            points = [exchange.to_influx_point() for exchange in exchanges]
            self._write_api.write(
                bucket=self.bucket,
                org=self.org,
                record=points,
                write_precision=WritePrecision.MS
            )
            logger.info(f"Successfully wrote {len(exchanges)} exchange records to InfluxDB")
            
        except Exception as e:
            logger.error(f"Failed to write exchange data to InfluxDB: {e}")
            raise
    
    def write_markets(self, markets: List[Market]) -> None:
        """Write market overview data to InfluxDB"""
        if not self._write_api:
            raise RuntimeError("InfluxDB client not connected")
        
        try:
            points = [market.to_influx_point() for market in markets]
            self._write_api.write(
                bucket=self.bucket,
                org=self.org,
                record=points,
                write_precision=WritePrecision.MS
            )
            logger.info(f"Successfully wrote {len(markets)} market records to InfluxDB")
            
        except Exception as e:
            logger.error(f"Failed to write market data to InfluxDB: {e}")
            raise
    
    def query_latest_coins(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Query latest coin data"""
        if not self._query_api:
            raise RuntimeError("InfluxDB client not connected")
        
        flux_query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: -1d)
            |> filter(fn: (r) => r._measurement == "cryptocurrency_data")
            |> last()
            |> limit(n: {limit})
        '''
        
        try:
            result = self._query_api.query(query=flux_query, org=self.org)
            records = []
            
            for table in result:
                for record in table.records:
                    records.append({
                        'time': record.get_time(),
                        'code': record.values.get('code'),
                        'field': record.get_field(),
                        'value': record.get_value()
                    })
            
            logger.info(f"Retrieved {len(records)} latest coin records from InfluxDB")
            return records
            
        except Exception as e:
            logger.error(f"Failed to query coin data from InfluxDB: {e}")
            raise
    
    def query_coin_history(
        self, 
        code: str, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Query historical data for a specific coin"""
        if not self._query_api:
            raise RuntimeError("InfluxDB client not connected")
        
        flux_query = f'''
            from(bucket: "{self.bucket}")
            |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
            |> filter(fn: (r) => r._measurement == "cryptocurrency_data")
            |> filter(fn: (r) => r.code == "{code.upper()}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        
        try:
            result = self._query_api.query(query=flux_query, org=self.org)
            records = []
            
            for table in result:
                for record in table.records:
                    records.append(record.values)
            
            logger.info(f"Retrieved {len(records)} historical records for {code}")
            return records
            
        except Exception as e:
            logger.error(f"Failed to query historical data for {code}: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self._query_api:
            raise RuntimeError("InfluxDB client not connected")
        
        stats = {}
        
        try:
            # Count of cryptocurrency records
            crypto_query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -30d)
                |> filter(fn: (r) => r._measurement == "cryptocurrency_data")
                |> count()
            '''
            
            result = self._query_api.query(query=crypto_query, org=self.org)
            for table in result:
                for record in table.records:
                    stats['crypto_records_30d'] = record.get_value()
                    break
                break
            
            # Count of exchange records
            exchange_query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -30d)
                |> filter(fn: (r) => r._measurement == "exchange_data")
                |> count()
            '''
            
            result = self._query_api.query(query=exchange_query, org=self.org)
            for table in result:
                for record in table.records:
                    stats['exchange_records_30d'] = record.get_value()
                    break
                break
            
            # Count of market records
            market_query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -30d)
                |> filter(fn: (r) => r._measurement == "market_overview")
                |> count()
            '''
            
            result = self._query_api.query(query=market_query, org=self.org)
            for table in result:
                for record in table.records:
                    stats['market_records_30d'] = record.get_value()
                    break
                break
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
