#!/usr/bin/env python3
"""
Basic usage examples for the Live Coin Watch API Data Fetcher

This script demonstrates common usage patterns and examples.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lcw_fetcher import Config, DataFetcher, setup_logging
from lcw_fetcher.scheduler import DataScheduler


def example_basic_fetch():
    """Example: Basic data fetching"""
    print("=== Basic Data Fetch Example ===")
    
    # Load configuration (from .env file)
    config = Config()
    
    # Setup logging
    setup_logging(config.log_level)
    
    # Create data fetcher
    fetcher = DataFetcher(config)
    
    try:
        # Check API status
        if fetcher.check_api_status():
            print("✅ API is accessible")
        else:
            print("❌ API is not accessible")
            return
        
        # Get API credits
        credits = fetcher.get_api_credits()
        if credits:
            print(f"📊 API Credits: {credits.get('dailyCreditsRemaining')}/{credits.get('dailyCreditsLimit')}")
        
        # Fetch specific coins
        print("\n--- Fetching specific coins ---")
        coins = fetcher.fetch_specific_coins(['BTC', 'ETH', 'BNB'])
        
        for coin in coins:
            print(f"{coin.code}: ${coin.rate:.2f} (24h: {((coin.delta.day - 1) * 100):.2f}%)")
        
        # Store in database
        success = fetcher.store_coins(coins)
        print(f"Storage success: {success}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        fetcher.close()


def example_top_coins():
    """Example: Fetch top coins by market cap"""
    print("\n=== Top Coins Example ===")
    
    config = Config()
    fetcher = DataFetcher(config)
    
    try:
        # Fetch top 10 coins
        top_coins = fetcher.fetch_coins_list(limit=10)
        
        print("Top 10 Cryptocurrencies by Market Cap:")
        print("-" * 60)
        print(f"{'Rank':<4} {'Code':<6} {'Name':<15} {'Price':<12} {'24h Change':<10}")
        print("-" * 60)
        
        for coin in top_coins:
            change_24h = ((coin.delta.day - 1) * 100) if coin.delta and coin.delta.day else 0
            print(f"{coin.rank:<4} {coin.code:<6} {coin.name[:15]:<15} ${coin.rate:<11.2f} {change_24h:>+7.2f}%")
        
        # Store in database
        fetcher.store_coins(top_coins)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        fetcher.close()


def example_historical_data():
    """Example: Fetch historical data for a coin"""
    print("\n=== Historical Data Example ===")
    
    config = Config()
    fetcher = DataFetcher(config)
    
    try:
        # Fetch 7 days of historical data for Bitcoin
        coin_with_history = fetcher.fetch_coin_history('BTC', hours_back=168)  # 7 days
        
        if coin_with_history and coin_with_history.history:
            print(f"Historical data for {coin_with_history.name} ({coin_with_history.code}):")
            print("-" * 40)
            print(f"{'Timestamp':<20} {'Price':<12} {'Volume':<15}")
            print("-" * 40)
            
            # Show last 5 data points
            for hist_point in coin_with_history.history[-5:]:
                timestamp = datetime.fromtimestamp(hist_point.date / 1000)
                print(f"{timestamp.strftime('%Y-%m-%d %H:%M'):<20} ${hist_point.rate:<11.2f} ${hist_point.volume:>13,.0f}")
        else:
            print("No historical data available")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        fetcher.close()


def example_exchanges():
    """Example: Fetch exchange data"""
    print("\n=== Exchange Data Example ===")
    
    config = Config()
    fetcher = DataFetcher(config)
    
    try:
        # Fetch top 10 exchanges
        exchanges = fetcher.fetch_exchanges_list(limit=10)
        
        print("Top 10 Exchanges by Volume:")
        print("-" * 65)
        print(f"{'Rank':<4} {'Code':<10} {'Name':<20} {'Volume':<15} {'Visitors':<10}")
        print("-" * 65)
        
        for exchange in exchanges:
            volume_str = f"${exchange.volume:,.0f}" if exchange.volume else "N/A"
            visitors_str = f"{exchange.visitors:,}" if exchange.visitors else "N/A"
            print(f"{exchange.rank:<4} {exchange.code:<10} {exchange.name[:20]:<20} {volume_str:<15} {visitors_str:<10}")
        
        # Store in database
        fetcher.store_exchanges(exchanges)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        fetcher.close()


def example_market_overview():
    """Example: Fetch market overview"""
    print("\n=== Market Overview Example ===")
    
    config = Config()
    fetcher = DataFetcher(config)
    
    try:
        # Fetch market overview
        markets = fetcher.fetch_market_overview()
        
        if markets:
            market = markets[0]  # Get first (current) market data
            print("Current Market Overview:")
            print("-" * 30)
            print(f"Total Market Cap: ${market.cap:,.0f}" if market.cap else "N/A")
            print(f"Total Volume:     ${market.volume:,.0f}" if market.volume else "N/A")
            print(f"Total Liquidity:  ${market.liquidity:,.0f}" if market.liquidity else "N/A")
            print(f"BTC Dominance:    {market.btcDominance:.2%}" if market.btcDominance else "N/A")
        else:
            print("No market data available")
            
        # Store in database
        fetcher.store_markets(markets)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        fetcher.close()


def example_full_fetch_cycle():
    """Example: Run a complete fetch cycle"""
    print("\n=== Full Fetch Cycle Example ===")
    
    config = Config()
    fetcher = DataFetcher(config)
    
    try:
        # Run full fetch cycle
        stats = fetcher.run_full_fetch()
        
        print("Fetch Cycle Results:")
        print("-" * 25)
        for key, value in stats.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        fetcher.close()


def example_scheduled_fetching():
    """Example: Start scheduled data fetching (demo mode)"""
    print("\n=== Scheduled Fetching Example ===")
    
    # Create a custom config for demo
    config = Config()
    
    # Override some settings for demo
    config.fetch_interval_minutes = 1  # Every minute for demo
    config.enable_scheduler = True
    
    scheduler = DataScheduler(config)
    
    try:
        print("Starting scheduler (demo mode - will run for 5 minutes)...")
        print("Press Ctrl+C to stop early")
        
        # Add demo jobs
        scheduler.add_regular_fetch_job()
        
        # Start for a limited time (in real use, this would run indefinitely)
        import time
        from threading import Thread
        
        # Start scheduler in a separate thread
        def start_scheduler():
            scheduler.scheduler.start()
        
        scheduler_thread = Thread(target=start_scheduler, daemon=True)
        scheduler_thread.start()
        
        # Run for 5 minutes
        time.sleep(300)
        
        print("Demo completed!")
        
    except KeyboardInterrupt:
        print("Scheduler stopped by user")
    finally:
        scheduler.stop()


def main():
    """Run all examples"""
    print("Live Coin Watch API Data Fetcher - Usage Examples")
    print("=" * 50)
    
    try:
        example_basic_fetch()
        example_top_coins()
        example_historical_data()
        example_exchanges()
        example_market_overview()
        example_full_fetch_cycle()
        
        # Uncomment to run scheduler example (runs for 5 minutes)
        # example_scheduled_fetching()
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"\nError running examples: {e}")


if __name__ == "__main__":
    main()
