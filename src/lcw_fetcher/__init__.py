"""
Live Coin Watch API Data Fetcher

A Python application to fetch cryptocurrency data from Live Coin Watch API
and store it in a time series database (InfluxDB).
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .api import LCWClient
from .database import InfluxDBClient
from .models import Coin, Exchange, Market
from .utils import Config, setup_logging

__all__ = [
    "LCWClient",
    "InfluxDBClient",
    "Coin",
    "Exchange",
    "Market",
    "Config",
    "setup_logging",
]
