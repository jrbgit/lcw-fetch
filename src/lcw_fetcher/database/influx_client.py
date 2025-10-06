import logging
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from influxdb_client import InfluxDBClient as BaseInfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions
from influxdb_client.domain.write_precision import WritePrecision
from loguru import logger

from ..models import Coin, Exchange, Market
from ..utils.performance_logger import track_performance, PerformanceContext

logger = logging.getLogger(__name__)


class InfluxDBClient:
    """InfluxDB client for storing cryptocurrency time series data"""

    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        bucket: str,
        timeout: int = 30000,  # Increased timeout for better reliability
        batch_size: int = 1000,
        flush_interval: int = 1000,
    ):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.timeout = timeout
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        self._client = None
        self._write_api = None
        self._query_api = None
        self._connection_pool_initialized = False

    def connect(self) -> None:
        """Establish connection to InfluxDB with optimized settings"""
        with PerformanceContext("influxdb_connect"):
            try:
                self._client = BaseInfluxDBClient(
                    url=self.url,
                    token=self.token,
                    org=self.org,
                    timeout=self.timeout,
                    enable_gzip=True,  # Enable compression
                )

                # Configure write options for better performance
                write_options = WriteOptions(
                    batch_size=self.batch_size,
                    flush_interval=self.flush_interval,
                    jitter_interval=100,
                    retry_interval=5000,
                    max_retries=3,
                    max_retry_delay=30000,
                    exponential_base=2,
                )

                self._write_api = self._client.write_api(write_options=write_options)
                self._query_api = self._client.query_api()

                # Test connection
                health_check = self._client.health()
                logger.info(
                    f"Connected to InfluxDB successfully - Status: {health_check.status}"
                )
                self._connection_pool_initialized = True

            except Exception as e:
                logger.error(f"Failed to connect to InfluxDB: {e}")
                raise

    def disconnect(self) -> None:
        """Close connection to InfluxDB with proper thread cleanup"""
        # CRITICAL FIX: Close WriteAPI first to stop background threads
        if self._write_api:
            try:
                logger.info("Closing InfluxDB WriteAPI to stop background threads...")
                self._write_api.close()  # This stops background threads
                logger.info("WriteAPI closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WriteAPI: {e}")
            finally:
                self._write_api = None
        
        # Close query API
        if self._query_api:
            try:
                # Query API doesn't have explicit close, but clear reference
                self._query_api = None
            except Exception as e:
                logger.warning(f"Error clearing query API: {e}")
        
        # Then close the main client
        if self._client:
            try:
                logger.info("Closing InfluxDB client connection...")
                self._client.close()
                logger.info("InfluxDB client closed successfully")
            except Exception as e:
                logger.warning(f"Error closing InfluxDB client: {e}")
            finally:
                self._client = None
                
        self._connection_pool_initialized = False
        logger.info("Disconnected from InfluxDB with thread cleanup")

    def write_coins(self, coins: List[Coin]) -> None:
        """Write coin data to InfluxDB with performance tracking"""
        if not self._write_api:
            raise RuntimeError("InfluxDB client not connected")

        with PerformanceContext("influxdb_write_coins", {"coin_count": len(coins)}):
            try:
                points = [coin.to_influx_point() for coin in coins]

                # Write in batches if we have many points
                if len(points) > self.batch_size:
                    for i in range(0, len(points), self.batch_size):
                        batch = points[i : i + self.batch_size]
                        self._write_api.write(
                            bucket=self.bucket,
                            org=self.org,
                            record=batch,
                            write_precision=WritePrecision.MS,
                        )
                else:
                    self._write_api.write(
                        bucket=self.bucket,
                        org=self.org,
                        record=points,
                        write_precision=WritePrecision.MS,
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
                write_precision=WritePrecision.MS,
            )
            logger.info(
                f"Successfully wrote {len(exchanges)} exchange records to InfluxDB"
            )

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
                write_precision=WritePrecision.MS,
            )
            logger.info(f"Successfully wrote {len(markets)} market records to InfluxDB")

        except Exception as e:
            logger.error(f"Failed to write market data to InfluxDB: {e}")
            raise

    def query_latest_coins(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Query latest coin data with performance tracking"""
        if not self._query_api:
            raise RuntimeError("InfluxDB client not connected")

        with PerformanceContext("influxdb_query_latest_coins", {"limit": limit}):
            flux_query = f"""
                from(bucket: "{self.bucket}")
                |> range(start: -1d)
                |> filter(fn: (r) => r._measurement == "cryptocurrency_data")
                |> last()
                |> limit(n: {limit})
            """

            try:
                result = self._query_api.query(query=flux_query, org=self.org)
                records = []

                for table in result:
                    for record in table.records:
                        records.append(
                            {
                                "time": record.get_time(),
                                "code": record.values.get("code"),
                                "field": record.get_field(),
                                "value": record.get_value(),
                            }
                        )

                logger.info(
                    f"Retrieved {len(records)} latest coin records from InfluxDB"
                )
                return records

            except Exception as e:
                logger.error(f"Failed to query coin data from InfluxDB: {e}")
                raise

    def query_coin_history(
        self, code: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Query historical data for a specific coin"""
        if not self._query_api:
            raise RuntimeError("InfluxDB client not connected")

        flux_query = f"""
            from(bucket: "{self.bucket}")
            |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
            |> filter(fn: (r) => r._measurement == "cryptocurrency_data")
            |> filter(fn: (r) => r.code == "{code.upper()}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        """

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
            crypto_query = f"""
                from(bucket: "{self.bucket}")
                |> range(start: -30d)
                |> filter(fn: (r) => r._measurement == "cryptocurrency_data")
                |> count()
            """

            result = self._query_api.query(query=crypto_query, org=self.org)
            for table in result:
                for record in table.records:
                    stats["crypto_records_30d"] = record.get_value()
                    break
                break

            # Count of exchange records
            exchange_query = f"""
                from(bucket: "{self.bucket}")
                |> range(start: -30d)
                |> filter(fn: (r) => r._measurement == "exchange_data")
                |> count()
            """

            result = self._query_api.query(query=exchange_query, org=self.org)
            for table in result:
                for record in table.records:
                    stats["exchange_records_30d"] = record.get_value()
                    break
                break

            # Count of market records
            market_query = f"""
                from(bucket: "{self.bucket}")
                |> range(start: -30d)
                |> filter(fn: (r) => r._measurement == "market_overview")
                |> count()
            """

            result = self._query_api.query(query=market_query, org=self.org)
            for table in result:
                for record in table.records:
                    stats["market_records_30d"] = record.get_value()
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
