import time
from datetime import datetime

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
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


def job_listener(event):
    """Job event listener to track completion"""
    if event.exception:
        logger.error(f"Job {event.job_id} crashed: {event.exception}")
    else:
        logger.info(f"Job {event.job_id} executed successfully")


class DataScheduler:
    """Scheduler for automated cryptocurrency data fetching"""

    def __init__(self, config: Config):
        self.config = config
        
        # NOTE: Don't create a persistent fetcher instance here to avoid thread leaks
        # Each job will create its own fetcher instance and clean it up

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
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 30,  # 30 seconds grace for delayed jobs
        }

        self.scheduler = BlockingScheduler(
            executors={"default": ThreadPoolExecutor(max_workers=2)},
            job_defaults=job_defaults,
            timezone="UTC",
        )

        # Add event listener
        self.scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

        logger.info("Scheduler configured with ThreadPoolExecutor (max_workers=2)")

    def _create_fetcher(self) -> DataFetcher:
        """Create a new DataFetcher instance for job execution"""
        return DataFetcher(self.config)

    def _cleanup_fetcher(self, fetcher: DataFetcher) -> None:
        """Properly clean up a DataFetcher instance after job completion"""
        try:
            if fetcher:
                fetcher.close()
                logger.debug("DataFetcher instance cleaned up successfully")
        except Exception as e:
            logger.warning(f"Error during DataFetcher cleanup: {e}")

    def add_frequent_fetch_job(self) -> None:
        """Schedule the main data fetching job at configurable intervals"""
        interval_minutes = getattr(self.config, "fetch_interval_minutes", 2)
        
        self.scheduler.add_job(
            func=self._frequent_fetch_wrapper,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="frequent_fetch",
            name="Frequent Data Fetch",
            replace_existing=True,
        )
        logger.info(f"Added frequent fetch job (every {interval_minutes} minute(s))")

    def add_hourly_exchange_fetch(self) -> None:
        """Schedule exchange data fetching every hour"""
        self.scheduler.add_job(
            func=self._fetch_exchanges_wrapper,
            trigger=CronTrigger(minute=0),
            id="hourly_exchanges",
            name="Hourly Exchange Fetch",
            replace_existing=True,
        )
        logger.info("Added hourly exchange fetch job")

    def add_daily_historical_fetch(self) -> None:
        """Schedule historical data fetching daily at 2 AM"""
        self.scheduler.add_job(
            func=self._fetch_historical_wrapper,
            trigger=CronTrigger(hour=2, minute=0),
            id="daily_historical",
            name="Daily Historical Fetch",
            replace_existing=True,
        )
        logger.info("Added daily historical fetch job")

    def add_weekly_full_sync(self) -> None:
        """Schedule full sync weekly on Sunday at 3 AM"""
        self.scheduler.add_job(
            func=self._full_sync_wrapper,
            trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
            id="weekly_full_sync",
            name="Weekly Full Sync",
            replace_existing=True,
        )
        logger.info("Added weekly full sync job")

    def _frequent_fetch_wrapper(self) -> None:
        """Wrapper for frequent fetch job (configurable interval) with proper cleanup"""
        logger.info("Starting frequent fetch job")
        fetcher = None
        try:
            # Create new fetcher instance for this job
            fetcher = self._create_fetcher()
            
            start_time = time.time()
            stats = fetcher.run_full_fetch()
            duration = time.time() - start_time

            # Record metrics if available
            if METRICS_AVAILABLE:
                record_fetch_cycle_metrics(duration, stats)

            logger.info(f"Frequent fetch completed: {stats}")
        except Exception as e:
            logger.error(f"Frequent fetch job failed: {e}")
            raise
        finally:
            # Always clean up the fetcher instance
            self._cleanup_fetcher(fetcher)

    def _fetch_exchanges_wrapper(self) -> None:
        """Wrapper for exchange fetch job with proper cleanup"""
        logger.info("Starting exchange fetch job")
        fetcher = None
        try:
            # Create new fetcher instance for this job
            fetcher = self._create_fetcher()
            
            exchanges = fetcher.fetch_exchanges_list(limit=50)
            if exchanges:
                fetcher.store_exchanges(exchanges)
                logger.info(f"Exchange fetch completed: {len(exchanges)} exchanges")
            else:
                logger.warning("No exchanges fetched")
        except Exception as e:
            logger.error(f"Exchange fetch job failed: {e}")
            raise
        finally:
            # Always clean up the fetcher instance
            self._cleanup_fetcher(fetcher)

    def _fetch_historical_wrapper(self) -> None:
        """Wrapper for historical data fetch job with proper cleanup"""
        logger.info("Starting historical fetch job")
        fetcher = None
        try:
            # Create new fetcher instance for this job
            fetcher = self._create_fetcher()
            
            tracked_coins = self.config.get_tracked_coins()
            historical_count = 0

            for coin_code in tracked_coins:
                coin_with_history = fetcher.fetch_coin_history(
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

                        if fetcher.store_coins([historical_coin]):
                            historical_count += 1

            logger.info(
                f"Historical fetch completed: {historical_count} historical records"
            )

        except Exception as e:
            logger.error(f"Historical fetch job failed: {e}")
            raise
        finally:
            # Always clean up the fetcher instance
            self._cleanup_fetcher(fetcher)

    def _full_sync_wrapper(self) -> None:
        """Wrapper for full sync job with proper cleanup"""
        logger.info("Starting weekly full sync job")
        fetcher = None
        try:
            # Create new fetcher instance for this job
            fetcher = self._create_fetcher()
            
            # Fetch more comprehensive data
            coins = fetcher.fetch_coins_list(limit=200)  # Top 200 coins
            exchanges = fetcher.fetch_exchanges_list(
                limit=100
            )  # Top 100 exchanges
            markets = fetcher.fetch_market_overview()

            total_stored = 0
            if coins:
                if fetcher.store_coins(coins):
                    total_stored += len(coins)

            if exchanges:
                if fetcher.store_exchanges(exchanges):
                    total_stored += len(exchanges)

            if markets:
                if fetcher.store_markets(markets):
                    total_stored += len(markets)

            logger.info(f"Full sync completed: {total_stored} total records stored")

        except Exception as e:
            logger.error(f"Full sync job failed: {e}")
            raise
        finally:
            # Always clean up the fetcher instance
            self._cleanup_fetcher(fetcher)

    def run_once(self) -> None:
        """Run a single fetch cycle immediately with 24-hour historical data"""
        logger.info("Running one-time fetch with 24-hour historical data")
        fetcher = None
        try:
            # Create fetcher instance for this one-time job
            fetcher = self._create_fetcher()
            
            stats = fetcher.run_full_fetch_with_history()
            logger.info(f"One-time fetch with history completed: {stats}")

            # Display summary to user
            if stats.get("historical_fetched", 0) > 0:
                logger.info(
                    f"✅ Successfully fetched {stats['historical_fetched']} historical data points"
                )
                logger.info(
                    f"✅ Successfully stored {stats['historical_stored']} historical records"
                )
        except Exception as e:
            logger.error(f"One-time fetch failed: {e}")
            raise
        finally:
            # Always clean up the fetcher instance
            self._cleanup_fetcher(fetcher)

    def start(self) -> None:
        """Start the scheduler with all configured jobs"""
        logger.info("Starting data scheduler...")
        
        # Add all jobs
        self.add_frequent_fetch_job()
        self.add_hourly_exchange_fetch()
        self.add_daily_historical_fetch()
        self.add_weekly_full_sync()

        logger.info("Scheduled jobs:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name} ({job.id}): {job.trigger}")

        logger.info("Scheduler started. Press Ctrl+C to stop.")
        
        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("Received stop signal")
            self.stop()

    def stop(self) -> None:
        """Stop the scheduler and cleanup"""
        logger.info("Stopping scheduler...")

        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)

        # No persistent fetcher to clean up since we create/cleanup per job
        logger.info("Scheduler stopped with proper cleanup")

    def get_job_status(self) -> list:
        """Get status of all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time,
                    "trigger": str(job.trigger),
                }
            )
        return jobs
