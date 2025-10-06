"""Utility functions and classes for the lcw_fetcher package"""

from .config import Config
from .logger import setup_logging
from .performance_logger import (
    get_system_stats,
    log_system_resources,
    monitor_resource_usage,
    track_performance,
    PerformanceContext,
)

try:
    from .cache import api_cache, redis_cache
except ImportError:
    # Cache might not be available in all environments
    api_cache = None
    redis_cache = None

# For backward compatibility
def get_performance_stats():
    """Backward compatibility function"""
    return get_system_stats()

def performance_monitor(operation_name: str):
    """Backward compatibility function"""  
    return monitor_resource_usage(operation_name)

__all__ = [
    'Config',
    'setup_logging',
    'get_system_stats',
    'get_performance_stats',
    'log_system_resources',
    'monitor_resource_usage',
    'performance_monitor',
    'track_performance',
    'PerformanceContext',
    'api_cache',
    'redis_cache',
]
