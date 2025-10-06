"""
Performance logging utility for LCW data fetcher.

This module provides tools for tracking operation timing and identifying
performance bottlenecks in the data fetching pipeline.
"""

import functools
import logging
import time
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from loguru import logger

# Import metrics functions
try:
    from .metrics import record_operation_duration, update_system_metrics

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

    def record_operation_duration(*args, **kwargs):
        pass

    def update_system_metrics(*args, **kwargs):
        pass


@dataclass
class OperationMetrics:
    """Container for operation performance metrics"""

    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def complete(self, success: bool = True, error_message: Optional[str] = None):
        """Mark the operation as completed"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging"""
        return {
            "operation": self.operation_name,
            "duration_seconds": round(self.duration or 0, 3),
            "success": self.success,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": (
                datetime.fromtimestamp(self.end_time).isoformat()
                if self.end_time
                else None
            ),
            "error": self.error_message,
            "context": self.context,
        }


class PerformanceTracker:
    """Tracks and logs performance metrics for operations"""

    def __init__(self):
        self.metrics_history: list[OperationMetrics] = []
        self.active_operations: Dict[str, OperationMetrics] = {}

        # Performance thresholds (configurable)
        self.warning_threshold = 30.0  # seconds
        self.critical_threshold = 60.0  # seconds

    def start_operation(
        self, operation_name: str, context: Optional[Dict[str, Any]] = None
    ) -> OperationMetrics:
        """Start tracking a new operation"""
        metrics = OperationMetrics(
            operation_name=operation_name, start_time=time.time(), context=context or {}
        )

        self.active_operations[operation_name] = metrics
        logger.debug(f"Started tracking: {operation_name}")

        return metrics

    def complete_operation(
        self,
        operation_name: str,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> Optional[OperationMetrics]:
        """Complete an operation and log its performance"""
        metrics = self.active_operations.pop(operation_name, None)
        if not metrics:
            logger.warning(
                f"Attempted to complete untracked operation: {operation_name}"
            )
            return None

        metrics.complete(success=success, error_message=error_message)
        self.metrics_history.append(metrics)

        # Log based on performance thresholds
        self._log_performance(metrics)

        # Record to Prometheus metrics if available
        if METRICS_AVAILABLE:
            record_operation_duration(
                operation_name, metrics.duration or 0, metrics.success
            )

        return metrics

    def _log_performance(self, metrics: OperationMetrics):
        """Log performance metrics based on duration thresholds"""
        duration = metrics.duration or 0
        operation_name = metrics.operation_name

        if not metrics.success:
            logger.error(
                f"❌ OPERATION FAILED: {operation_name} after {duration:.2f}s - {metrics.error_message}"
            )
        elif duration >= self.critical_threshold:
            logger.critical(
                f"🚨 CRITICAL SLOW OPERATION: {operation_name} took {duration:.2f}s (threshold: {self.critical_threshold}s)"
            )
        elif duration >= self.warning_threshold:
            logger.warning(
                f"⚠️ SLOW OPERATION: {operation_name} took {duration:.2f}s (threshold: {self.warning_threshold}s)"
            )
        else:
            logger.info(f"✅ {operation_name} completed in {duration:.2f}s")

        # Always log detailed metrics at debug level
        logger.debug(f"Operation metrics: {metrics.to_dict()}")

    def get_recent_stats(
        self, operation_name: Optional[str] = None, limit: int = 100
    ) -> Dict[str, Any]:
        """Get recent performance statistics"""
        recent_metrics = self.metrics_history[-limit:]

        if operation_name:
            recent_metrics = [
                m for m in recent_metrics if m.operation_name == operation_name
            ]

        if not recent_metrics:
            return {"error": "No metrics available"}

        durations = [m.duration for m in recent_metrics if m.duration is not None]
        successes = [m.success for m in recent_metrics]

        if not durations:
            return {"error": "No duration data available"}

        return {
            "operation": operation_name or "all_operations",
            "count": len(recent_metrics),
            "success_rate": sum(successes) / len(successes) * 100,
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "slow_operations": len(
                [d for d in durations if d >= self.warning_threshold]
            ),
            "critical_operations": len(
                [d for d in durations if d >= self.critical_threshold]
            ),
        }


# Global performance tracker instance
_performance_tracker = PerformanceTracker()


@contextmanager
def track_performance(operation_name: str, context: Optional[Dict[str, Any]] = None):
    """Context manager for tracking operation performance"""
    metrics = _performance_tracker.start_operation(operation_name, context)

    try:
        yield metrics
        _performance_tracker.complete_operation(operation_name, success=True)
    except Exception as e:
        _performance_tracker.complete_operation(
            operation_name, success=False, error_message=str(e)
        )
        raise


def performance_monitor(operation_name: Optional[str] = None):
    """Decorator for monitoring function performance"""

    def decorator(func: Callable) -> Callable:
        nonlocal operation_name
        if operation_name is None:
            operation_name = f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with track_performance(operation_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def get_performance_stats(
    operation_name: Optional[str] = None, limit: int = 100
) -> Dict[str, Any]:
    """Get performance statistics from the global tracker"""
    return _performance_tracker.get_recent_stats(operation_name, limit)


def log_system_resources():
    """Log current system resource usage"""
    try:
        import psutil

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)

        # Disk usage (for current directory)
        disk = psutil.disk_usage(".")
        disk_percent = (disk.used / disk.total) * 100


        # Thread count
        active_threads = threading.active_count()
        try:
            import os
            process_threads = len(os.listdir(f"/proc/{os.getpid()}/task"))
        except:
            process_threads = active_threads
        logger.info(
            f"📊 System Resources - "
            f"CPU: {cpu_percent}% | "
            f"Memory: {memory_percent}% ({memory_available_gb:.1f}GB available) | "
            f"Disk: {disk_percent:.1f}% | Threads: {active_threads}/{process_threads}"
        )

        # Record to Prometheus metrics if available
        if METRICS_AVAILABLE:
            update_system_metrics(cpu_percent, memory_percent, disk_percent)

    except ImportError:
        logger.warning(
            "psutil not available - install with 'pip install psutil' for system monitoring"
        )
    except Exception as e:
        logger.error(f"Error logging system resources: {e}")


class PerformanceAlert:
    """Handles performance alerting"""

    def __init__(
        self,
        warning_threshold: float = 30.0,
        critical_threshold: float = 60.0,
        alert_cooldown: int = 300,
    ):  # 5 minutes
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.alert_cooldown = alert_cooldown
        self.last_alert_time = {}

    def check_and_alert(self, metrics: OperationMetrics):
        """Check if an alert should be sent for the given metrics"""
        duration = metrics.duration or 0
        operation = metrics.operation_name
        current_time = time.time()

        # Check cooldown
        last_alert = self.last_alert_time.get(operation, 0)
        if current_time - last_alert < self.alert_cooldown:
            return

        if duration >= self.critical_threshold:
            self._send_alert(
                level="CRITICAL",
                operation=operation,
                duration=duration,
                message=f"Operation {operation} took {duration:.2f}s (>{self.critical_threshold}s)",
            )
            self.last_alert_time[operation] = current_time

        elif duration >= self.warning_threshold:
            self._send_alert(
                level="WARNING",
                operation=operation,
                duration=duration,
                message=f"Operation {operation} took {duration:.2f}s (>{self.warning_threshold}s)",
            )
            self.last_alert_time[operation] = current_time

    def _send_alert(self, level: str, operation: str, duration: float, message: str):
        """Send performance alert (extend this for email/Slack notifications)"""
        logger.warning(f"🚨 PERFORMANCE ALERT [{level}]: {message}")

        # TODO: Extend this to send email/Slack notifications
        # For now, just log the alert
