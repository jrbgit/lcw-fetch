import signal
import sys
import time
from datetime import datetime
from typing import Optional

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from .fetcher import DataFetcher
from .utils import Config

# Import metrics functions
try:
    from .utils.metrics import init_metrics, record_fetch_cycle_metrics

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

    def init_metrics(*args, **kwargs):
        pass

    def record_fetch_cycle_metrics(*args, **kwargs):
        pass


class DataScheduler:
    """Scheduler for automated cryptocurrency data fetching"""

    def __init__(self, config: Config):
        self.config = config
        self.fetcher = DataFetcher(config)

        # Initialize metrics if enabled
        if METRICS_AVAILABLE and config.enable_metrics:
            self.metrics_collector = init_metrics(
                enable_metrics=config.enable_metrics, port=config.metrics_port
            )
            logger.info(f"Metrics enabled on port {config.metrics_port}")
        else:
            self.metrics_collector = None
        # Configure scheduler with job defaults including misfire grace time
        job_defaults = {
            "misfire_grace_time": config.job_misfire_grace_time  # Configurable grace time
        }

        # Configure executors with limited thread pool to prevent thread leaks
        executors = {
            'default': ThreadPoolExecutor(max_workers=2)  # Limit concurrent job threads
        }
        self.scheduler = BlockingScheduler(
            timezone=config.scheduler_timezone, job_defaults=job_defaults, executors=executors
        )
        logger.info("Scheduler configured with ThreadPoolExecutor (max_workers=2)")
        self._setup_signal_handlers()
        self._setup_job_listeners()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _setup_job_listeners(self) -> None:
        """Setup job event listeners"""

        def job_listener(event):
            if event.exception:
                logger.error(f"Job {event.job_id} crashed: {event.exception}")
            else:
                logger.info(f"Job {event.job_id} executed successfully")

        self.scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    def add_frequent_fetch_job(self) -> None:
        """Add frequent data fetching job (configurable interval)"""
        trigger = IntervalTrigger(minutes=self.config.fetch_interval_minutes)

        self.scheduler.add_job(
            func=self._frequent_fetch_wrapper,
            trigger=trigger,
            id="frequent_fetch",
            name="Frequent Data Fetch",
            max_instances=1,  # Prevent overlapping runs
            misfire_grace_time=self.config.job_misfire_grace_time,  # Configurable grace time
            replace_existing=True,
        )

        logger.info(
            f"Added frequent fetch job (every {self.config.fetch_interval_minutes} minute(s))"
        )

    def add_regular_fetch_job(self) -> None:
        """Add regular data fetching job (configurable interval, now unused)"""
        # This method is kept for backward compatibility but not used
        # The frequent_fetch_job (1 minute) now handles this functionality
        pass

    def add_hourly_exchange_fetch(self) -> None:
        """Add hourly exchange data fetching"""
        trigger = CronTrigger(minute=0)  # Every hour at minute 0

        self.scheduler.add_job(
            func=self._fetch_exchanges_wrapper,
            trigger=trigger,
            id="hourly_exchanges",
            name="Hourly Exchange Fetch",
            max_instances=1,
            misfire_grace_time=max(
                self.config.job_misfire_grace_time, 300
            ),  # At least 5 minutes for hourly jobs
            replace_existing=True,
        )

        logger.info("Added hourly exchange fetch job")

    def add_daily_historical_fetch(self) -> None:
        """Add daily historical data fetching for tracked coins"""
        trigger = CronTrigger(hour=2, minute=0)  # Every day at 2:00 AM

        self.scheduler.add_job(
            func=self._fetch_historical_wrapper,
            trigger=trigger,
            id="daily_historical",
            name="Daily Historical Fetch",
            max_instances=1,
            misfire_grace_time=max(
                self.config.job_misfire_grace_time, 1800
            ),  # At least 30 minutes for daily jobs
            replace_existing=True,
        )

        logger.info("Added daily historical fetch job")

    def add_weekly_full_sync(self) -> None:
        """Add weekly full synchronization"""
        trigger = CronTrigger(
            day_of_week="sun", hour=3, minute=0
        )  # Every Sunday at 3:00 AM

        self.scheduler.add_job(
            func=self._full_sync_wrapper,
            trigger=trigger,
            id="weekly_full_sync",
            name="Weekly Full Sync",
            max_instances=1,
            misfire_grace_time=max(
                self.config.job_misfire_grace_time, 3600
            ),  # At least 1 hour for weekly jobs
            replace_existing=True,
        )

        logger.info("Added weekly full sync job")

    def _frequent_fetch_wrapper(self) -> None:
        """Wrapper for frequent fetch job (configurable interval)"""
        logger.info("Starting frequent fetch job")
        try:
            start_time = time.time()
            stats = self.fetcher.run_full_fetch()
            duration = time.time() - start_time

            # Record metrics if available
            if METRICS_AVAILABLE:
                record_fetch_cycle_metrics(duration, stats)

            logger.info(f"Frequent fetch completed: {stats}")
        except Exception as e:
            logger.error(f"Frequent fetch job failed: {e}")
            raise

    def _fetch_job_wrapper(self) -> None:
        """Wrapper for regular fetch job (legacy, now unused)"""
        # This method is kept for backward compatibility but not used
        pass

    def _fetch_exchanges_wrapper(self) -> None:
        """Wrapper for exchange fetch job"""
        logger.info("Starting exchange fetch job")
        try:
            exchanges = self.fetcher.fetch_exchanges_list(limit=50)
            if exchanges:
                self.fetcher.store_exchanges(exchanges)
                logger.info(f"Exchange fetch completed: {len(exchanges)} exchanges")
            else:
                logger.warning("No exchanges fetched")
        except Exception as e:
            logger.error(f"Exchange fetch job failed: {e}")
            raise

    def _fetch_historical_wrapper(self) -> None:
        """Wrapper for historical data fetch job"""
        logger.info("Starting historical fetch job")
        try:
            tracked_coins = self.config.get_tracked_coins()
            historical_count = 0

            for coin_code in tracked_coins:
                coin_with_history = self.fetcher.fetch_coin_history(
                    coin_code, hours_back=168
                )  # 1 week
                if coin_with_history and coin_with_history.history:
                    # Store historical data points as individual coin records
                    for hist_point in coin_with_history.history:
                        # Create a coin record for each historical point
                        historical_coin = coin_with_history.copy(deep=True)
                        historical_coin.rate = hist_point.rate
                        historical_coin.volume = hist_point.volume
                        historical_coin.cap = hist_point.cap
                        historical_coin.fetched_at = datetime.fromtimestamp(
                            hist_point.date / 1000
                        )
                        historical_coin.history = []  # Clear history to avoid recursion

                        if self.fetcher.store_coins([historical_coin]):
                            historical_count += 1

            logger.info(
                f"Historical fetch completed: {historical_count} historical records"
            )

        except Exception as e:
            logger.error(f"Historical fetch job failed: {e}")
            raise

    def _full_sync_wrapper(self) -> None:
        """Wrapper for full sync job"""
        logger.info("Starting weekly full sync job")
        try:
            # Fetch more comprehensive data
            coins = self.fetcher.fetch_coins_list(limit=200)  # Top 200 coins
            exchanges = self.fetcher.fetch_exchanges_list(
                limit=100
            )  # Top 100 exchanges
            markets = self.fetcher.fetch_market_overview()

            total_stored = 0
            if coins:
                if self.fetcher.store_coins(coins):
                    total_stored += len(coins)

            if exchanges:
                if self.fetcher.store_exchanges(exchanges):
                    total_stored += len(exchanges)

            if markets:
                if self.fetcher.store_markets(markets):
                    total_stored += len(markets)

            logger.info(f"Full sync completed: {total_stored} total records stored")

        except Exception as e:
            logger.error(f"Full sync job failed: {e}")
            raise

    def run_once(self) -> None:
        """Run a single fetch cycle immediately with 24-hour historical data"""
        logger.info("Running one-time fetch with 24-hour historical data")
        try:
            stats = self.fetcher.run_full_fetch_with_history()
            logger.info(f"One-time fetch with history completed: {stats}")

            # Display summary to user
            if stats.get("historical_fetched", 0) > 0:
                logger.info(
                    f"✅ Successfully fetched {stats['historical_fetched']} historical data points"
                )
                logger.info(
                    f"✅ Successfully stored {stats['historical_stored']} historical records"
                )
            else:
                logger.warning("⚠️ No historical data was fetched")

        except Exception as e:
            logger.error(f"One-time fetch with history failed: {e}")
            raise

    def start(self) -> None:
        """Start the scheduler"""
        if not self.config.enable_scheduler:
            logger.info("Scheduler disabled in configuration")
            return

        logger.info("Starting data scheduler...")

        # Start metrics server if enabled
        if self.metrics_collector:
            self.metrics_collector.start_metrics_server()

        # Add all jobs
        self.add_frequent_fetch_job()  # New 1-minute job
        self.add_hourly_exchange_fetch()
        self.add_daily_historical_fetch()
        self.add_weekly_full_sync()

        # Print job schedule
        logger.info("Scheduled jobs:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name} ({job.id}): {job.trigger}")

        logger.info("Scheduler started. Press Ctrl+C to stop.")

        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the scheduler"""
        logger.info("Stopping scheduler...")

        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)

        if self.fetcher:
            self.fetcher.close()

        logger.info("Scheduler stopped")

    def get_job_status(self) -> list:
        """Get status of all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "trigger": str(job.trigger),
                    "next_run": (
                        job.next_run_time.isoformat() if job.next_run_time else None
                    ),
                }
            )
        return jobs
