# LCW Fetch Service - Thread Monitoring Baseline

## Established on: 2025-10-06 23:42:20Z

### Thread Count Baseline (Post Thread Leak Fix)

**Normal Operating Range:**
- Pre-job thread count: 2-3 active threads / 21-22 total threads
- Post-job thread count: 4 active threads / 23 total threads  
- Expected variation: ±1-2 threads due to normal system operations

**Job Execution Pattern:**
- Jobs run every 2 minutes
- Each job creates a fresh DataFetcher instance
- HTTP clients and InfluxDB clients are properly closed after each job
- Thread cleanup occurs explicitly during fetcher closure

### Key Monitoring Metrics

**Thread Count Alerts:**
- ⚠️  **Warning**: Active threads > 8 (sustained for > 10 minutes)  
- 🚨 **Critical**: Active threads > 15 (immediate alert)
- 🚨 **Critical**: Total threads > 50 (immediate alert)

**Performance Baselines:**
- Full fetch cycle: ~20-30 seconds
- 1000 coins fetched and stored per cycle
- 20 exchanges fetched and stored per cycle  
- Zero errors in steady state

**Health Indicators:**
- ✅ All clients closed successfully after each job
- ✅ Zero warnings/errors in logs
- ✅ Consistent resource cleanup messages
- ✅ Jobs complete with "executed successfully" messages

### Changes Made to Fix Thread Leak
1. **Scheduler Modified**: Creates fresh DataFetcher instance per job instead of reusing singleton
2. **Resource Cleanup**: Explicit HTTP client and InfluxDB client closure after each job
3. **Context Manager Fix**: Replaced incorrect `track_performance` context manager usage with `PerformanceContext`
4. **Monitoring Enhanced**: Added thread count logging before/after each job execution

### Log Patterns to Monitor
- Look for increase in "Threads: X/Y" values over time
- Monitor for missing "HTTP client closed successfully" messages
- Watch for missing "Database client closed successfully" messages  
- Alert on any ERROR or WARNING level messages

### Historical Context
- **Problem**: Thread leaks due to persistent DataFetcher instance with unclosed HTTP/DB connections
- **Root Cause**: Singleton pattern preventing resource cleanup + incorrect context manager usage
- **Solution**: Per-job instance creation with explicit cleanup + fixed context managers
- **Result**: Stable thread count with proper resource management
