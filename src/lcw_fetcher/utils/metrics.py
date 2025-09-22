"""
Prometheus metrics for LCW Data Fetcher observability.

This module provides Prometheus-compatible metrics for monitoring
the LCW data fetcher performance and operations.
"""
import time
import threading
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
    from prometheus_client.core import CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create mock objects for when prometheus_client is not available
    class MockMetric:
        def inc(self, amount: float = 1) -> None: pass
        def observe(self, amount: float) -> None: pass
        def set(self, value: float) -> None: pass
        def info(self, data: Dict[str, str]) -> None: pass
    
    Counter = Histogram = Gauge = Info = MockMetric

from loguru import logger


class MetricsCollector:
    """Collects and exports Prometheus metrics for LCW data fetcher"""
    
    def __init__(self, enable_metrics: bool = True, port: int = 9099):
        self.enable_metrics = enable_metrics and PROMETHEUS_AVAILABLE
        self.port = port
        self.registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None
        self._metrics_server_started = False
        
        if self.enable_metrics:
            self._init_metrics()
        else:
            self._init_mock_metrics()
    
    def _init_metrics(self):
        """Initialize Prometheus metrics"""
        # Operation duration histogram
        self.operation_duration = Histogram(
            'lcw_operation_duration_seconds',
            'Time spent on different operations',
            ['operation', 'status'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 60.0, float('inf')],
            registry=self.registry
        )
        
        # Operation counters
        self.operations_total = Counter(
            'lcw_operations_total',
            'Total number of operations performed',
            ['operation', 'status'],
            registry=self.registry
        )
        
        # API call metrics
        self.api_calls_total = Counter(
            'lcw_api_calls_total',
            'Total number of API calls made',
            ['endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.api_response_duration = Histogram(
            'lcw_api_response_duration_seconds',
            'API response time',
            ['endpoint'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float('inf')],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_operations_total = Counter(
            'lcw_cache_operations_total',
            'Total cache operations',
            ['operation'],  # hit, miss, eviction
            registry=self.registry
        )
        
        self.cache_size = Gauge(
            'lcw_cache_size_entries',
            'Current number of entries in cache',
            registry=self.registry
        )
        
        # Database metrics
        self.database_operations_total = Counter(
            'lcw_database_operations_total',
            'Total database operations',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.database_response_duration = Histogram(
            'lcw_database_response_duration_seconds',
            'Database operation response time',
            ['operation'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, float('inf')],
            registry=self.registry
        )
        
        # System metrics
        self.system_resources = Gauge(
            'lcw_system_resources',
            'System resource usage',
            ['resource'],  # cpu, memory, disk
            registry=self.registry
        )
        
        # Fetch cycle metrics
        self.fetch_cycles_total = Counter(
            'lcw_fetch_cycles_total',
            'Total number of fetch cycles',
            ['status'],
            registry=self.registry
        )
        
        self.fetch_cycle_duration = Histogram(
            'lcw_fetch_cycle_duration_seconds',
            'Full fetch cycle duration',
            buckets=[1.0, 5.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0, 120.0, float('inf')],
            registry=self.registry
        )
        
        # Data quality metrics
        self.data_points_stored = Counter(
            'lcw_data_points_stored_total',
            'Total data points stored',
            ['data_type'],  # coins, exchanges, markets
            registry=self.registry
        )
        
        # Application info
        self.app_info = Info(
            'lcw_app_info',
            'Application information',
            registry=self.registry
        )
        
        # Set application info
        self.app_info.info({
            'version': '1.0.0',
            'component': 'lcw-data-fetcher',
            'optimization_phase': 'phase-4-metrics'
        })
        
        logger.info("Prometheus metrics initialized")
    
    def _init_mock_metrics(self):
        """Initialize mock metrics when Prometheus is not available"""
        self.operation_duration = MockMetric()
        self.operations_total = MockMetric()
        self.api_calls_total = MockMetric()
        self.api_response_duration = MockMetric()
        self.cache_operations_total = MockMetric()
        self.cache_size = MockMetric()
        self.database_operations_total = MockMetric()
        self.database_response_duration = MockMetric()
        self.system_resources = MockMetric()
        self.fetch_cycles_total = MockMetric()
        self.fetch_cycle_duration = MockMetric()
        self.data_points_stored = MockMetric()
        self.app_info = MockMetric()
        
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available - metrics will be disabled")
    
    def start_metrics_server(self):
        """Start the Prometheus metrics HTTP server"""
        if not self.enable_metrics or self._metrics_server_started:
            return
        
        try:
            start_http_server(self.port, registry=self.registry)
            self._metrics_server_started = True
            logger.info(f"Metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
    
    def record_operation(self, operation: str, duration: float, success: bool = True):
        """Record an operation's duration and status"""
        status = 'success' if success else 'error'
        self.operation_duration.labels(operation=operation, status=status).observe(duration)
        self.operations_total.labels(operation=operation, status=status).inc()
    
    def record_api_call(self, endpoint: str, duration: float, status_code: int):
        """Record an API call"""
        self.api_calls_total.labels(endpoint=endpoint, status_code=str(status_code)).inc()
        self.api_response_duration.labels(endpoint=endpoint).observe(duration)
    
    def record_cache_operation(self, operation: str):
        """Record a cache operation (hit, miss, eviction)"""
        self.cache_operations_total.labels(operation=operation).inc()
    
    def update_cache_size(self, size: int):
        """Update current cache size"""
        self.cache_size.set(size)
    
    def record_database_operation(self, operation: str, duration: float, success: bool = True):
        """Record a database operation"""
        status = 'success' if success else 'error'
        self.database_operations_total.labels(operation=operation, status=status).inc()
        self.database_response_duration.labels(operation=operation).observe(duration)
    
    def update_system_resource(self, resource: str, value: float):
        """Update system resource gauge"""
        self.system_resources.labels(resource=resource).set(value)
    
    def record_fetch_cycle(self, duration: float, success: bool = True):
        """Record a complete fetch cycle"""
        status = 'success' if success else 'error'
        self.fetch_cycles_total.labels(status=status).inc()
        self.fetch_cycle_duration.observe(duration)
    
    def record_data_stored(self, data_type: str, count: int):
        """Record data points stored"""
        self.data_points_stored.labels(data_type=data_type).inc(count)


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def init_metrics(enable_metrics: bool = True, port: int = 9099) -> MetricsCollector:
    """Initialize the global metrics collector"""
    global _metrics_collector
    _metrics_collector = MetricsCollector(enable_metrics, port)
    return _metrics_collector


def get_metrics_collector() -> Optional[MetricsCollector]:
    """Get the global metrics collector"""
    return _metrics_collector


def start_metrics(port: int = 9099) -> bool:
    """Start the metrics server"""
    if _metrics_collector:
        _metrics_collector.start_metrics_server()
        return True
    return False


def record_operation_duration(operation: str, duration: float, success: bool = True):
    """Record operation duration to metrics"""
    if _metrics_collector:
        _metrics_collector.record_operation(operation, duration, success)


def increment_counter(metric_name: str, **labels):
    """Increment a counter metric (simplified interface)"""
    if not _metrics_collector:
        return
    
    # Map common metric names to the actual metrics
    if metric_name == 'api_calls':
        endpoint = labels.get('endpoint', 'unknown')
        status_code = labels.get('status_code', 200)
        _metrics_collector.api_calls_total.labels(endpoint=endpoint, status_code=str(status_code)).inc()
    elif metric_name == 'cache_operations':
        operation = labels.get('operation', 'unknown')
        _metrics_collector.cache_operations_total.labels(operation=operation).inc()
    elif metric_name == 'data_stored':
        data_type = labels.get('data_type', 'unknown')
        count = labels.get('count', 1)
        _metrics_collector.data_points_stored.labels(data_type=data_type).inc(count)


@contextmanager
def timer(operation: str):
    """Context manager to time operations and record to metrics"""
    start_time = time.time()
    success = True
    try:
        yield
    except Exception as e:
        success = False
        raise
    finally:
        duration = time.time() - start_time
        record_operation_duration(operation, duration, success)


def update_system_metrics(cpu_percent: float, memory_percent: float, disk_percent: float):
    """Update system resource metrics"""
    if _metrics_collector:
        _metrics_collector.update_system_resource('cpu', cpu_percent)
        _metrics_collector.update_system_resource('memory', memory_percent)
        _metrics_collector.update_system_resource('disk', disk_percent)


def record_fetch_cycle_metrics(duration: float, stats: Dict[str, int]):
    """Record fetch cycle completion"""
    if not _metrics_collector:
        return
    
    success = stats.get('errors', 0) == 0
    _metrics_collector.record_fetch_cycle(duration, success)
    
    # Record data stored
    if stats.get('coins_stored', 0) > 0:
        _metrics_collector.record_data_stored('coins', stats['coins_stored'])
    if stats.get('exchanges_stored', 0) > 0:
        _metrics_collector.record_data_stored('exchanges', stats['exchanges_stored'])
    if stats.get('markets_stored', 0) > 0:
        _metrics_collector.record_data_stored('markets', stats['markets_stored'])