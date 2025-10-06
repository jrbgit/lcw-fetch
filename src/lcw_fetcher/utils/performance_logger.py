import logging
import psutil
import threading
import time
from typing import Any, Dict, Optional

# Import Prometheus metrics if available  
METRICS_AVAILABLE = True
try:
    from prometheus_client import Counter, Histogram, Summary
    
    # Prometheus metrics
    FETCH_DURATION = Summary("lcw_fetch_duration_seconds", "Time spent on data fetching operations", ["operation"])
    FETCH_COUNTER = Counter("lcw_fetch_total", "Total number of fetch operations", ["operation", "status"])
    RESOURCE_USAGE = Histogram("lcw_resource_usage", "System resource usage", ["resource_type"])
except ImportError:
    METRICS_AVAILABLE = False

from loguru import logger


class PerformanceContext:
    """Context manager for tracking performance of code blocks"""
    
    def __init__(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        self.operation_name = operation_name
        self.metadata = metadata or {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
    def __enter__(self):
        self.start_time = time.time()
        logger.debug(f"⏱️ Starting {self.operation_name}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        # Log performance
        _log_performance(self.operation_name, duration, self.metadata, exc_type is None)
        
        return False  # Don't suppress exceptions


def track_performance(operation_name: str, metadata: Optional[Dict[str, Any]] = None):
    """Decorator for tracking performance of functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with PerformanceContext(operation_name, metadata):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def _log_performance(operation_name: str, duration: float, metadata: Dict[str, Any], success: bool) -> None:
    """Internal function to log performance metrics"""
    
    # Format duration appropriately
    if duration < 1:
        duration_str = f"{duration:.2f}s"
    elif duration < 60:
        duration_str = f"{duration:.1f}s"
    else:
        minutes = int(duration // 60)
        seconds = duration % 60
        duration_str = f"{minutes}m{seconds:.1f}s"
    
    # Log with appropriate level based on duration and success
    if not success:
        logger.error(f"❌ {operation_name} failed after {duration_str}")
    elif duration > 30:
        logger.warning(f"🐌 {operation_name} completed in {duration_str} (slow)")
    elif duration > 10:
        logger.info(f"⏳ {operation_name} completed in {duration_str}")
    else:
        logger.info(f"✅ {operation_name} completed in {duration_str}")
    
    # Add metadata if provided
    if metadata:
        logger.debug(f"📋 {operation_name} metadata: {metadata}")
    
    # Record to Prometheus if available
    if METRICS_AVAILABLE:
        FETCH_DURATION.labels(operation=operation_name).observe(duration)
        FETCH_COUNTER.labels(operation=operation_name, status='success' if success else 'failure').inc()


def get_system_stats() -> Dict[str, Any]:
    """Get current system resource statistics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        # Disk usage for current directory
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Thread count
        active_threads = threading.active_count()
        
        # Try to get more accurate process thread count
        try:
            import os
            # Get actual process thread count from /proc
            process_threads = len(os.listdir(f"/proc/{os.getpid()}/task"))
        except:
            process_threads = active_threads
            
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_available_gb': memory_available_gb,
            'disk_percent': disk_percent,
            'active_threads': active_threads,
            'process_threads': process_threads
        }
    except Exception as e:
        logger.warning(f"Failed to get system stats: {e}")
        return {}


def log_system_resources() -> None:
    """Log current system resource usage with thread monitoring"""
    stats = get_system_stats()
    
    if not stats:
        logger.warning("Unable to retrieve system resource information")
        return
    
    cpu_percent = stats['cpu_percent']
    memory_percent = stats['memory_percent']
    memory_available_gb = stats['memory_available_gb']
    disk_percent = stats['disk_percent']
    active_threads = stats['active_threads']
    process_threads = stats['process_threads']
    
    # Log thread information with more detail
    logger.info(
        f"📊 System Resources - "
        f"CPU: {cpu_percent}% | "
        f"Memory: {memory_percent}% ({memory_available_gb:.1f}GB available) | "
        f"Disk: {disk_percent:.1f}% | Threads: {active_threads}/{process_threads}"
    )
    
    # Alert on high thread count (potential leak detection)
    if process_threads > 100:
        logger.warning(f"⚠️ High thread count detected: {process_threads} threads (potential leak!)")
    elif process_threads > 50:
        logger.info(f"📈 Elevated thread count: {process_threads} threads")
    elif process_threads <= 30:
        logger.debug(f"✅ Normal thread count: {process_threads} threads")

    # Record to Prometheus metrics if available
    if METRICS_AVAILABLE:
        RESOURCE_USAGE.labels(resource_type='cpu').observe(cpu_percent)
        RESOURCE_USAGE.labels(resource_type='memory').observe(memory_percent)
        RESOURCE_USAGE.labels(resource_type='disk').observe(disk_percent)
        RESOURCE_USAGE.labels(resource_type='threads').observe(process_threads)


def monitor_resource_usage(operation_name: str):
    """Decorator to monitor resource usage before and after operation"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"🔍 Resource monitoring for {operation_name}")
            
            # Get stats before
            stats_before = get_system_stats()
            
            try:
                result = func(*args, **kwargs)
                
                # Get stats after
                stats_after = get_system_stats()
                
                # Log resource changes if significant
                if stats_before and stats_after:
                    thread_diff = stats_after['process_threads'] - stats_before['process_threads']
                    if abs(thread_diff) > 2:  # More than 2 threads changed
                        if thread_diff > 0:
                            logger.warning(f"🔺 {operation_name} increased threads by {thread_diff} "
                                         f"({stats_before['process_threads']} → {stats_after['process_threads']})")
                        else:
                            logger.info(f"🔻 {operation_name} decreased threads by {abs(thread_diff)} "
                                       f"({stats_before['process_threads']} → {stats_after['process_threads']})")
                
                return result
            except Exception as e:
                # Log final stats on error
                stats_after = get_system_stats()
                if stats_before and stats_after:
                    thread_diff = stats_after['process_threads'] - stats_before['process_threads']
                    if thread_diff > 0:
                        logger.error(f"💥 {operation_name} failed and leaked {thread_diff} threads")
                raise
                
        return wrapper
    return decorator


def alert_on_resource_threshold(max_threads: int = 100, max_memory_percent: float = 90.0):
    """Check resource thresholds and alert if exceeded"""
    stats = get_system_stats()
    
    if not stats:
        return
    
    alerts = []
    
    if stats['process_threads'] > max_threads:
        alerts.append(f"Thread count ({stats['process_threads']}) exceeds threshold ({max_threads})")
    
    if stats['memory_percent'] > max_memory_percent:
        alerts.append(f"Memory usage ({stats['memory_percent']:.1f}%) exceeds threshold ({max_memory_percent}%)")
    
    if alerts:
        logger.warning("🚨 Resource threshold alerts:")
        for alert in alerts:
            logger.warning(f"  - {alert}")


# Convenience function for backward compatibility
def track_performance_simple(operation_name: str, duration: float, metadata: Dict[str, Any] = None, success: bool = True):
    """Simple function to track performance - for backward compatibility"""
    _log_performance(operation_name, duration, metadata or {}, success)


# Make commonly used items available at module level
__all__ = [
    'track_performance',
    'PerformanceContext', 
    'log_system_resources',
    'get_system_stats',
    'monitor_resource_usage',
    'alert_on_resource_threshold'
]
