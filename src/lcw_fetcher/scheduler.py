import signal
import sys
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from loguru import logger

from .fetcher import DataFetcher
from .utils import Config


class DataScheduler:
    """Scheduler for automated cryptocurrency data fetching"""
    
    def __init__(self, config: Config):
        self.config = config
        self.fetcher = DataFetcher(config)
        self.scheduler = BlockingScheduler(timezone=config.scheduler_timezone)
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
    
    def add_regular_fetch_job(self) -> None:
        """Add regular data fetching job"""
        trigger = IntervalTrigger(minutes=self.config.fetch_interval_minutes)
        
        self.scheduler.add_job(
            func=self._fetch_job_wrapper,
            trigger=trigger,
            id='regular_fetch',
            name='Regular Data Fetch',
            max_instances=1,  # Prevent overlapping runs
            replace_existing=True
        )
        
        logger.info(f"Added regular fetch job (every {self.config.fetch_interval_minutes} minutes)")
    
    def add_hourly_exchange_fetch(self) -> None:
        """Add hourly exchange data fetching"""
        trigger = CronTrigger(minute=0)  # Every hour at minute 0
        
        self.scheduler.add_job(
            func=self._fetch_exchanges_wrapper,
            trigger=trigger,
            id='hourly_exchanges',
            name='Hourly Exchange Fetch',
            max_instances=1,
            replace_existing=True
        )
        
        logger.info("Added hourly exchange fetch job")
    
    def add_daily_historical_fetch(self) -> None:
        """Add daily historical data fetching for tracked coins"""
        trigger = CronTrigger(hour=2, minute=0)  # Every day at 2:00 AM
        
        self.scheduler.add_job(
            func=self._fetch_historical_wrapper,
            trigger=trigger,
            id='daily_historical',
            name='Daily Historical Fetch',
            max_instances=1,
            replace_existing=True
        )
        
        logger.info("Added daily historical fetch job")
    
    def add_weekly_full_sync(self) -> None:
        """Add weekly full synchronization"""
        trigger = CronTrigger(day_of_week='sun', hour=3, minute=0)  # Every Sunday at 3:00 AM
        
        self.scheduler.add_job(
            func=self._full_sync_wrapper,
            trigger=trigger,
            id='weekly_full_sync',
            name='Weekly Full Sync',
            max_instances=1,
            replace_existing=True
        )
        
        logger.info("Added weekly full sync job")
    
    def _fetch_job_wrapper(self) -> None:
        """Wrapper for regular fetch job"""
        logger.info("Starting regular fetch job")
        try:
            stats = self.fetcher.run_full_fetch()
            logger.info(f"Regular fetch completed: {stats}")
        except Exception as e:
            logger.error(f"Regular fetch job failed: {e}")
            raise
    
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
                coin_with_history = self.fetcher.fetch_coin_history(coin_code, hours_back=168)  # 1 week
                if coin_with_history and coin_with_history.history:
                    # Store historical data points as individual coin records
                    for hist_point in coin_with_history.history:
                        # Create a coin record for each historical point
                        historical_coin = coin_with_history.copy(deep=True)
                        historical_coin.rate = hist_point.rate
                        historical_coin.volume = hist_point.volume
                        historical_coin.cap = hist_point.cap
                        historical_coin.fetched_at = datetime.fromtimestamp(hist_point.date / 1000)
                        historical_coin.history = []  # Clear history to avoid recursion
                        
                        if self.fetcher.store_coins([historical_coin]):
                            historical_count += 1
            
            logger.info(f"Historical fetch completed: {historical_count} historical records")
            
        except Exception as e:
            logger.error(f"Historical fetch job failed: {e}")
            raise
    
    def _full_sync_wrapper(self) -> None:
        """Wrapper for full sync job"""
        logger.info("Starting weekly full sync job")
        try:
            # Fetch more comprehensive data
            coins = self.fetcher.fetch_coins_list(limit=200)  # Top 200 coins
            exchanges = self.fetcher.fetch_exchanges_list(limit=100)  # Top 100 exchanges
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
        """Run a single fetch cycle immediately"""
        logger.info("Running one-time fetch")
        try:
            stats = self.fetcher.run_full_fetch()
            logger.info(f"One-time fetch completed: {stats}")
        except Exception as e:
            logger.error(f"One-time fetch failed: {e}")
            raise
    
    def start(self) -> None:
        """Start the scheduler"""
        if not self.config.enable_scheduler:
            logger.info("Scheduler disabled in configuration")
            return
        
        logger.info("Starting data scheduler...")
        
        # Add all jobs
        self.add_regular_fetch_job()
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
            jobs.append({
                'id': job.id,
                'name': job.name,
                'trigger': str(job.trigger),
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            })
        return jobs
