#!/usr/bin/env python3
"""
Live Coin Watch API Data Fetcher - Main Application

Usage:
    python -m lcw_fetcher.main [OPTIONS] COMMAND

Commands:
    run-once    Run a single fetch cycle
    start       Start the scheduler
    status      Check API and database status
    config      Show configuration
"""

import sys
from pathlib import Path

import click
from loguru import logger

from .utils import Config, setup_logging
from .scheduler import DataScheduler
from .fetcher import DataFetcher


@click.group()
@click.option('--config-file', type=click.Path(), help='Path to configuration file')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']), 
              help='Override log level')
@click.pass_context
def cli(ctx, config_file, log_level):
    """Live Coin Watch API Data Fetcher"""
    
    # Load configuration
    try:
        if config_file and Path(config_file).exists():
            config = Config(_env_file=config_file)
        else:
            config = Config()
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)
    
    # Override log level if specified
    if log_level:
        config.log_level = log_level
    
    # Setup logging
    setup_logging(config.log_level)
    
    # Store config in context
    ctx.ensure_object(dict)
    ctx.obj['config'] = config


@cli.command()
@click.pass_context
def run_once(ctx):
    """Run a single data fetch cycle including 24-hour historical data"""
    config = ctx.obj['config']
    
    click.echo("Starting one-time data fetch with 24-hour historical data...")
    tracked_coins = config.get_tracked_coins()
    click.echo(f"📊 Tracked coins: {', '.join(tracked_coins)}")
    click.echo("⏳ This will fetch current data + 24h history for each tracked coin...")
    logger.info("Starting one-time data fetch with historical data")
    
    try:
        scheduler = DataScheduler(config)
        scheduler.run_once()
        click.echo("✅ Data fetch with 24-hour historical data completed successfully")
        click.echo("📊 Check your InfluxDB/Grafana dashboard for the new historical data points!")
        
    except KeyboardInterrupt:
        click.echo("❌ Fetch interrupted by user")
        logger.info("Fetch interrupted by user")
    except Exception as e:
        click.echo(f"❌ Fetch failed: {e}")
        logger.error(f"Fetch failed: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def start(ctx):
    """Start the scheduled data fetcher"""
    config = ctx.obj['config']
    
    if not config.enable_scheduler:
        click.echo("❌ Scheduler is disabled in configuration")
        sys.exit(1)
    
    click.echo("Starting scheduled data fetcher...")
    logger.info("Starting scheduled data fetcher")
    
    try:
        scheduler = DataScheduler(config)
        scheduler.start()
        
    except KeyboardInterrupt:
        click.echo("❌ Scheduler interrupted by user")
        logger.info("Scheduler interrupted by user")
    except Exception as e:
        click.echo(f"❌ Scheduler failed: {e}")
        logger.error(f"Scheduler failed: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Check API and database connectivity status"""
    config = ctx.obj['config']
    
    click.echo("Checking system status...")
    
    # Test API connection
    try:
        fetcher = DataFetcher(config)
        
        # Check API status
        if fetcher.check_api_status():
            click.echo("✅ Live Coin Watch API: Connected")
        else:
            click.echo("❌ Live Coin Watch API: Failed to connect")
        
        # Check API credits
        credits = fetcher.get_api_credits()
        if credits:
            remaining = credits.get('dailyCreditsRemaining', 'unknown')
            limit = credits.get('dailyCreditsLimit', 'unknown')
            click.echo(f"📊 API Credits: {remaining}/{limit} remaining")
        else:
            click.echo("❌ API Credits: Could not retrieve")
        
        # Check database connection
        try:
            with fetcher.db_client as db:
                stats = db.get_database_stats()
                click.echo("✅ InfluxDB: Connected")
                
                if stats:
                    click.echo("📈 Database Stats (last 30 days):")
                    for key, value in stats.items():
                        click.echo(f"   - {key}: {value}")
                else:
                    click.echo("📈 Database Stats: No data available")
                    
        except Exception as e:
            click.echo(f"❌ InfluxDB: Connection failed - {e}")
        
        fetcher.close()
        
    except Exception as e:
        click.echo(f"❌ Status check failed: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def config(ctx):
    """Show current configuration"""
    config_obj = ctx.obj['config']
    
    click.echo("Current Configuration:")
    click.echo("=" * 50)
    
    # API Configuration
    click.echo("🔑 API Configuration:")
    click.echo(f"   LCW Base URL: {config_obj.lcw_base_url}")
    click.echo(f"   API Key: {'*' * 20}...{config_obj.lcw_api_key[-4:] if len(config_obj.lcw_api_key) > 4 else '****'}")
    
    # Database Configuration
    click.echo("\n💾 Database Configuration:")
    click.echo(f"   InfluxDB URL: {config_obj.influxdb_url}")
    click.echo(f"   Organization: {config_obj.influxdb_org}")
    click.echo(f"   Bucket: {config_obj.influxdb_bucket}")
    click.echo(f"   Token: {'*' * 20}...{config_obj.influxdb_token[-4:] if len(config_obj.influxdb_token) > 4 else '****'}")
    
    # Application Configuration
    click.echo("\n⚙️ Application Configuration:")
    click.echo(f"   Log Level: {config_obj.log_level}")
    click.echo(f"   Fetch Interval: {config_obj.fetch_interval_minutes} minutes")
    click.echo(f"   Max Coins per Fetch: {config_obj.max_coins_per_fetch}")
    click.echo(f"   Requests per Minute: {config_obj.requests_per_minute}")
    
    # Scheduling Configuration
    click.echo("\n📅 Scheduling Configuration:")
    click.echo(f"   Scheduler Enabled: {config_obj.enable_scheduler}")
    click.echo(f"   Timezone: {config_obj.scheduler_timezone}")
    
    # Tracked Coins
    tracked_coins = config_obj.get_tracked_coins()
    click.echo(f"\n🪙 Tracked Coins ({len(tracked_coins)}):")
    click.echo(f"   {', '.join(tracked_coins)}")


@cli.command()
@click.option('--coin', '-c', multiple=True, help='Specific coin codes to fetch historical data for')
@click.option('--hours', '-h', type=int, default=24, help='Number of hours of history to fetch (default: 24)')
@click.pass_context
def history(ctx, coin, hours):
    """Fetch historical data for specific coins"""
    config = ctx.obj['config']
    
    # Determine which coins to fetch
    if coin:
        coin_list = list(coin)
    else:
        coin_list = config.get_tracked_coins()
    
    if not coin_list:
        click.echo("❌ No coins specified and no tracked coins configured")
        return
    
    click.echo(f"Fetching {hours}-hour historical data for: {', '.join(coin_list)}")
    
    try:
        fetcher = DataFetcher(config)
        total_historical_stored = 0
        
        for coin_code in coin_list:
            click.echo(f"⏳ Fetching history for {coin_code}...")
            coin_with_history = fetcher.fetch_coin_history(coin_code, hours_back=hours)
            
            if coin_with_history and coin_with_history.history:
                click.echo(f"✅ Retrieved {len(coin_with_history.history)} historical points for {coin_code}")
                
                # Store historical data points as individual coin records
                historical_coins_stored = 0
                for hist_point in coin_with_history.history:
                    try:
                        from datetime import datetime
                        historical_coin = coin_with_history.model_copy(deep=True)
                        historical_coin.rate = hist_point.rate
                        historical_coin.volume = hist_point.volume
                        historical_coin.cap = hist_point.cap
                        historical_coin.fetched_at = datetime.fromtimestamp(hist_point.date / 1000)
                        historical_coin.history = []  # Clear history to avoid recursion
                        
                        if fetcher.store_coins([historical_coin]):
                            historical_coins_stored += 1
                    except Exception as e:
                        click.echo(f"⚠️ Error storing historical point for {coin_code}: {e}")
                
                total_historical_stored += historical_coins_stored
                click.echo(f"✅ Stored {historical_coins_stored} historical records for {coin_code}")
            else:
                click.echo(f"⚠️ No historical data retrieved for {coin_code}")
        
        fetcher.close()
        click.echo(f"✅ Historical data fetch completed! Stored {total_historical_stored} total records.")
        
    except Exception as e:
        click.echo(f"❌ Historical data fetch failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--coin', '-c', multiple=True, help='Specific coin codes to fetch (can be used multiple times)')
@click.option('--limit', '-l', type=int, help='Limit number of top coins to fetch')
@click.pass_context
def fetch(ctx, coin, limit):
    """Fetch specific coins or top coins list"""
    config = ctx.obj['config']
    
    try:
        fetcher = DataFetcher(config)
        
        if coin:
            # Fetch specific coins
            coin_list = list(coin)
            click.echo(f"Fetching data for coins: {', '.join(coin_list)}")
            coins = fetcher.fetch_specific_coins(coin_list)
            
            if coins:
                if fetcher.store_coins(coins):
                    click.echo(f"✅ Successfully fetched and stored {len(coins)} coins")
                else:
                    click.echo("❌ Failed to store coin data")
            else:
                click.echo("❌ No coin data retrieved")
                
        elif limit:
            # Fetch top coins
            click.echo(f"Fetching top {limit} coins...")
            coins = fetcher.fetch_coins_list(limit=limit)
            
            if coins:
                if fetcher.store_coins(coins):
                    click.echo(f"✅ Successfully fetched and stored {len(coins)} top coins")
                else:
                    click.echo("❌ Failed to store coin data")
            else:
                click.echo("❌ No coin data retrieved")
                
        else:
            click.echo("❌ Please specify either --coin or --limit")
            
        fetcher.close()
        
    except Exception as e:
        click.echo(f"❌ Fetch failed: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    try:
        cli()
    except Exception as e:
        click.echo(f"❌ Application error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
