import os
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration"""
    
    # Live Coin Watch API settings
    lcw_api_key: str = Field(..., env="LCW_API_KEY")
    lcw_base_url: str = Field("https://api.livecoinwatch.com", env="LCW_BASE_URL")
    
    # InfluxDB settings
    influxdb_url: str = Field("http://localhost:8086", env="INFLUXDB_URL")
    influxdb_token: str = Field(..., env="INFLUXDB_TOKEN")
    influxdb_org: str = Field(..., env="INFLUXDB_ORG")
    influxdb_bucket: str = Field("cryptocurrency_data", env="INFLUXDB_BUCKET")
    
    # Application settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    fetch_interval_minutes: int = Field(5, env="FETCH_INTERVAL_MINUTES")  # Configurable fetch interval in minutes
    max_coins_per_fetch: int = Field(100, env="MAX_COINS_PER_FETCH")
    
    # Database settings
    database_name: str = Field("crypto_timeseries", env="DATABASE_NAME")
    
    # Coins to track (comma-separated)
    tracked_coins: str = Field("BTC,ETH,GLQ", env="TRACKED_COINS")
    
    # Scheduling settings
    enable_scheduler: bool = Field(True, env="ENABLE_SCHEDULER")
    scheduler_timezone: str = Field("UTC", env="SCHEDULER_TIMEZONE")
    job_misfire_grace_time: int = Field(60, env="JOB_MISFIRE_GRACE_TIME")
    
    # API rate limiting
    requests_per_minute: int = Field(60, env="REQUESTS_PER_MINUTE")

    # Metrics / Observability
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    metrics_port: int = Field(9099, env="METRICS_PORT")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    @field_validator('fetch_interval_minutes')
    @classmethod
    def validate_fetch_interval(cls, v):
        if v < 1:
            raise ValueError('Fetch interval must be at least 1 minute')
        return v
    
    @field_validator('max_coins_per_fetch')
    @classmethod
    def validate_max_coins(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('Max coins per fetch must be between 1 and 1000')
        return v
    
    @field_validator('job_misfire_grace_time')
    @classmethod
    def validate_grace_time(cls, v):
        if v < 0 or v > 3600:
            raise ValueError('Job misfire grace time must be between 0 and 3600 seconds')
        return v
    
    def get_tracked_coins(self) -> List[str]:
        """Get list of tracked coin codes"""
        return [coin.strip().upper() for coin in self.tracked_coins.split(',') if coin.strip()]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


# Global config instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def set_config(config: Config) -> None:
    """Set the global config instance."""
    global _config_instance
    _config_instance = config
