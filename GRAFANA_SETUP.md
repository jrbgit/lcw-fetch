# Grafana Setup and Troubleshooting Guide

## Fixed Issues

### ❌ **Problem**: Grafana container restarting with plugin error
```
Error: ✗ failed to install plugin grafana-influxdb-datasource@: 404: Plugin not found
```

### ✅ **Solution**: 
The InfluxDB datasource is built into modern Grafana versions. The docker-compose.yml has been updated to:

1. Remove the problematic plugin installation
2. Add proper provisioning configuration
3. Include sample dashboards

## Quick Start

1. **Stop the current containers:**
   ```bash
   docker-compose down
   ```

2. **Update the InfluxDB token in provisioning:**
   Edit `config/grafana/provisioning/datasources/influxdb.yml` and update the token to match your InfluxDB setup.

3. **Restart the stack:**
   ```bash
   docker-compose up -d
   ```

4. **Access Grafana:**
   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `admin`

## Configuration Details

### Automatic Datasource Setup
The InfluxDB datasource is automatically configured via provisioning:

**File**: `config/grafana/provisioning/datasources/influxdb.yml`
```yaml
datasources:
  - name: InfluxDB-Cryptocurrency
    type: influxdb
    url: http://influxdb:8086
    jsonData:
      version: Flux
      organization: cryptocurrency
      defaultBucket: crypto_data
    secureJsonData:
      token: your_super_secret_admin_token
```

### Pre-built Dashboard
A sample dashboard is automatically loaded: "Cryptocurrency Overview"

## Manual Setup (if needed)

If automatic provisioning doesn't work, you can manually configure:

1. **Add InfluxDB Data Source:**
   - Go to Configuration > Data Sources
   - Click "Add data source"
   - Select "InfluxDB"
   - Configure:
     - URL: `http://influxdb:8086`
     - Auth: Off
     - InfluxDB Details:
       - Query Language: Flux
       - Organization: `cryptocurrency`
       - Token: `your_super_secret_admin_token`
       - Default Bucket: `crypto_data`

2. **Import Dashboard:**
   - Go to + > Import
   - Upload the JSON file: `config/grafana/provisioning/dashboards/crypto-overview.json`

## Sample Queries

### Bitcoin Price Over Time
```flux
from(bucket: "crypto_data")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "cryptocurrency_data")
  |> filter(fn: (r) => r.code == "BTC")
  |> filter(fn: (r) => r._field == "rate")
```

### Top 10 Coins by Market Cap
```flux
from(bucket: "crypto_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "cryptocurrency_data")
  |> filter(fn: (r) => r._field == "market_cap")
  |> last()
  |> sort(columns: ["_value"], desc: true)
  |> limit(n: 10)
```

### Market Overview
```flux
from(bucket: "crypto_data")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "market_overview")
  |> filter(fn: (r) => r._field == "total_market_cap")
  |> aggregateWindow(every: 1h, fn: mean)
```

### 24h Price Changes
```flux
from(bucket: "crypto_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "cryptocurrency_data")
  |> filter(fn: (r) => r._field == "delta_24h")
  |> last()
  |> map(fn: (r) => ({ r with _value: (r._value - 1.0) * 100.0 }))
```

## Troubleshooting

### Container Issues

1. **Check Grafana logs:**
   ```bash
   docker-compose logs grafana
   ```

2. **Check if InfluxDB is accessible:**
   ```bash
   docker-compose exec grafana curl -I http://influxdb:8086/ping
   ```

3. **Verify provisioning files are mounted:**
   ```bash
   docker-compose exec grafana ls -la /etc/grafana/provisioning/
   ```

### Data Source Connection Issues

1. **Test InfluxDB connection manually:**
   ```bash
   curl -H "Authorization: Token your_super_secret_admin_token" \
        "http://localhost:8086/api/v2/query?org=cryptocurrency" \
        --data-urlencode 'query=buckets()'
   ```

2. **Check bucket exists:**
   ```bash
   docker-compose exec lcw-fetcher python -c "
   from lcw_fetcher.database import InfluxDBClient
   import os
   client = InfluxDBClient(
       'http://influxdb:8086',
       'your_super_secret_admin_token',
       'cryptocurrency',
       'crypto_data'
   )
   with client as db:
       stats = db.get_database_stats()
       print('Database stats:', stats)
   "
   ```

### Dashboard Issues

1. **No data showing:**
   - Verify the data fetcher is running: `docker-compose logs lcw-fetcher`
   - Check if data exists in InfluxDB
   - Verify time range in dashboard matches data availability

2. **Query errors:**
   - Check bucket name matches in queries
   - Verify measurement names match your data
   - Check field names are correct

### Reset Grafana

If you need to start fresh:

1. **Remove Grafana data:**
   ```bash
   docker-compose down
   docker volume rm lcw_api_grafana-storage
   docker-compose up -d
   ```

2. **Or reset to defaults:**
   ```bash
   docker-compose exec grafana rm -rf /var/lib/grafana/*
   docker-compose restart grafana
   ```

## Advanced Configuration

### Custom Dashboard Variables

Add variables to make dashboards dynamic:

1. **Coin Selection Variable:**
   - Name: `coin`
   - Type: Query
   - Query: `from(bucket: "crypto_data") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "cryptocurrency_data") |> keep(columns: ["code"]) |> distinct(column: "code")`

2. **Time Range Variable:**
   - Name: `timeframe`
   - Type: Custom
   - Values: `1h,6h,24h,7d,30d`

### Alerting Setup

1. **Create notification channels** (Slack, Email, etc.)
2. **Set up alerts** on dashboard panels
3. **Example alert conditions:**
   - BTC price drops more than 5%
   - Volume increases by 50%
   - Data collection stops

### Performance Optimization

1. **Limit query ranges** for better performance
2. **Use aggregation** for long time ranges
3. **Cache results** where possible
4. **Optimize InfluxDB queries**

## Additional Resources

- [Grafana InfluxDB Documentation](https://grafana.com/docs/grafana/latest/datasources/influxdb/)
- [Flux Query Language](https://docs.influxdata.com/flux/v0.x/)
- [Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)

## Support

If you continue having issues:

1. Check the main [README.md](README.md) for general setup
2. Review [DEPLOYMENT.md](DEPLOYMENT.md) for deployment options
3. Check container logs: `docker-compose logs`
4. Verify environment variables in `.env` file
