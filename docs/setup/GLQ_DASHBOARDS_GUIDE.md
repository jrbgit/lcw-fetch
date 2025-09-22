# GLQ GraphLinq Chain - Grafana Dashboards Guide

This guide provides comprehensive documentation for the GLQ GraphLinq Chain monitoring dashboards in Grafana.

## Overview

The GLQ monitoring system consists of three specialized dashboards designed to provide complete visibility into the GraphLinq Chain ecosystem:

1. **GLQ GraphLinq Chain - Comprehensive Monitoring** (Main Dashboard)
2. **GLQ GraphLinq Chain - Network Health**
3. **GLQ GraphLinq Chain - Alerts & Monitoring**

## Dashboard Architecture

### Data Sources
- **InfluxDB**: Primary time-series database storing GLQ metrics
- **Live Coin Watch API**: Source for real-time cryptocurrency data
- **Measurement**: `cryptocurrency_data` in InfluxDB

### Key Metrics Tracked
- Price (rate) in USD
- 24-hour trading volume
- Market capitalization
- Market rank
- Price changes (1h, 24h, 7d, 30d)
- Liquidity depth
- Active exchanges count
- Trading pairs
- Circulating supply

## Dashboard 1: GLQ GraphLinq Chain - Comprehensive Monitoring

### Purpose
Primary dashboard for monitoring GLQ's market performance and key metrics.

### Key Panels

#### Top Row - Key Metrics
- **GLQ Current Price**: Real-time price in USD
- **GLQ 24H Change**: Percentage change over 24 hours with color coding
- **GLQ Market Cap**: Current market capitalization
- **GLQ 24H Volume**: 24-hour trading volume

#### Price Analysis
- **GLQ Price Trend**: Time series chart showing price evolution
  - Customizable time range
  - Smooth line interpolation
  - Min/max/current value display

#### Volume Analysis
- **GLQ Volume Trend**: Bar chart showing trading volume over time
  - Aggregated by time interval
  - Volume distribution analysis

#### Performance Tracking
- **GLQ Performance Comparison**: Multi-timeframe performance bars
  - 1 Hour, 24 Hours, 7 Days, 30 Days
  - Color-coded thresholds for performance levels

#### Market Statistics
- **GLQ Market Statistics**: Comprehensive table view
  - Price, Market Cap, Volume, 24H Change, Rank, Circulating Supply
  - Color-coded cells for quick status assessment

#### Market Analysis
- **GLQ Market Cap Evolution**: Historical market cap trends
- **GLQ vs Market Leaders**: Comparison with BTC, ETH, BNB, ADA
- **GLQ Volatility**: 24-hour price volatility calculation
- **GLQ Market Rank**: Current ranking position
- **GLQ Circulating Supply**: Available token supply
- **Average Transaction Size**: Estimated transaction size metrics

### Dashboard Settings
- **Refresh Rate**: 30 seconds
- **Time Range**: Default 7 days (customizable)
- **Timezone**: UTC
- **Theme**: Dark mode
- **Variables**: Automatic interval selection

## Dashboard 2: GLQ GraphLinq Chain - Network Health

### Purpose
Specialized dashboard for monitoring GLQ network health, liquidity, and ecosystem metrics.

### Key Panels

#### Health Status Overview
- **Network Health Status**: Binary health indicator
  - Based on volume and price stability
  - Green (Healthy) / Red (Unhealthy)

- **GLQ Liquidity Depth**: Market liquidity assessment
  - Threshold-based color coding
  - Critical levels: <$50K (red), $50K-$100K (yellow), >$100K (green)

- **Active Exchanges**: Number of exchanges trading GLQ
  - Network reach indicator
  - Threshold: <5 (red), 5-10 (yellow), >10 (green)

#### Network Activity
- **Network Activity Trends**: Dual-axis chart
  - Trading volume (left axis)
  - Active exchanges (right axis)
  - Correlation analysis over time

- **GLQ Liquidity Depth Over Time**: Liquidity evolution
  - Bar chart showing liquidity changes
  - Trend analysis for market depth

#### Health Metrics
- **Network Health Breakdown**: Donut chart
  - Volume Score, Liquidity Score, Exchange Score
  - Proportional representation of health factors

- **GLQ Market Infrastructure**: Table view
  - Exchanges, Markets, Trading Pairs, Liquidity
  - Color-coded thresholds for infrastructure health

#### Advanced Analytics
- **Price Stability (1H)**: Short-term price stability indicator
- **Network Adoption Score**: Composite score (0-100%)
  - Based on volume, exchanges, and market rank
  - Weighted scoring algorithm

- **Market Resilience**: Three-tier resilience indicator
  - Low / Medium / High based on volume and liquidity

- **Growth Velocity (7D)**: 7-day growth rate

- **Volume Distribution Analysis**: Multi-window volume analysis
  - 1H, 4H, 24H averages
  - Pattern recognition for trading behavior

### Health Scoring Algorithm

```
Network Adoption Score = (Volume Score × 30%) + (Exchange Score × 35%) + (Rank Score × 35%)

Where:
- Volume Score: Volume/100K × 30 (max 30%)
- Exchange Score: Exchanges/10 × 35 (max 35%)  
- Rank Score: Based on ranking position (35% if <100, declining for higher ranks)
```

## Dashboard 3: GLQ GraphLinq Chain - Alerts & Monitoring

### Purpose
Real-time alerting and notification dashboard for critical GLQ metrics.

### Alert Categories

#### Price Alerts
- **Price Alert Status**: Multi-level price alert system
  - Normal (Green): Changes within ±5% (1H), ±10% (24H)
  - Warning (Yellow): Changes ±5-10% (1H), ±10-20% (24H)
  - Critical (Red): Changes >±10% (1H), >±20% (24H)

#### Volume Alerts
- **Volume Alert Status**: Volume anomaly detection
  - Normal: Volume within 70%-300% of 7-day average
  - Low Volume: <30% of 7-day average
  - High Volume: >300% of 7-day average

#### Rank Alerts
- **Rank Alert Status**: Market position monitoring
  - Stable: Rank <200
  - Rank Drop: Rank >200
  - Rank Rise: Rank <100 (positive alert)

### Alert Visualizations

#### Threshold Charts
- **GLQ Price with Alert Thresholds**: Price chart with threshold lines
  - Dashed lines showing alert boundaries
  - Color zones for different alert levels

- **GLQ Volume with Alert Thresholds**: Volume with alert boundaries
  - Threshold bars showing normal/warning/critical levels

#### Summary Tables
- **GLQ Critical Metrics Alert Summary**: Real-time status table
  - All key metrics with color-coded cells
  - Threshold-based background colors
  - Immediate status assessment

#### Performance Monitoring
- **GLQ Performance Alert Monitor**: Multi-timeframe performance
  - 1H, 24H, 7D performance tracking
  - Alert thresholds for each timeframe

- **GLQ Market Health Alerts**: Liquidity and exchange monitoring
  - Dual-axis chart with alert thresholds
  - Infrastructure health assessment

#### System Status
- **Overall Alert Status**: Aggregated alert level
  - All Clear (0 alerts)
  - Minor Issues (1 alert)
  - Multiple Alerts (2 alerts)
  - Critical State (3+ alerts)

- **Recent Alert Activity**: Alert history table
  - Last 20 significant changes
  - Time-stamped alert log
  - 30-minute aggregation windows

### Configurable Thresholds

The alert dashboard includes template variables for customization:

- **Price Alert Threshold**: 5%, 10%, 15%, 20% (default: 10%)
- **Volume Alert Threshold**: $10K, $25K, $50K, $100K (default: $50K)

## Installation and Setup

### Prerequisites
- Grafana 9.5.2 or higher
- InfluxDB connection configured
- LCW API data pipeline running

### Installation Steps

1. **Copy Dashboard Files**
   ```bash
   cp glq-graphlinq-chain.json /etc/grafana/provisioning/dashboards/
   cp glq-network-health.json /etc/grafana/provisioning/dashboards/
   cp glq-alerts.json /etc/grafana/provisioning/dashboards/
   ```

2. **Update Provisioning Configuration**
   The dashboards are automatically provisioned through the updated `dashboard.yaml` configuration.

3. **Verify Data Source**
   Ensure the InfluxDB data source `influxdb-lcw` is properly configured.

4. **Restart Grafana**
   ```bash
   systemctl restart grafana-server
   ```

### Navigation

The dashboards are organized in the **GLQ Monitoring** folder in Grafana:

```
GLQ Monitoring/
├── GLQ GraphLinq Chain - Comprehensive Monitoring (Main)
├── GLQ GraphLinq Chain - Network Health
└── GLQ GraphLinq Chain - Alerts & Monitoring
```

Each dashboard includes navigation links to the others for seamless monitoring.

## Data Requirements

### InfluxDB Schema

The dashboards expect data in the following InfluxDB schema:

```
Measurement: cryptocurrency_data
Tags:
  - code: "GLQ"
  - name: "GraphLinq"
  - currency: "USD"

Fields:
  - rate (float): Current price
  - volume (float): 24H trading volume
  - market_cap (float): Market capitalization
  - rank (integer): Market ranking
  - delta_1h (float): 1H price change %
  - delta_24h (float): 24H price change %
  - delta_7d (float): 7D price change %
  - delta_30d (float): 30D price change %
  - liquidity (float): Market liquidity
  - exchanges (integer): Active exchanges
  - markets (integer): Number of markets
  - pairs (integer): Trading pairs
  - circulating_supply (float): Circulating supply
```

### Data Collection

Data is collected through the LCW API fetcher:

1. **API Endpoint**: Live Coin Watch API
2. **Update Frequency**: Every 1-5 minutes (configurable)
3. **Data Retention**: Configurable in InfluxDB (default: 30 days)

## Customization

### Time Ranges
All dashboards support custom time ranges:
- Quick selections: 1h, 6h, 12h, 1d, 7d, 30d
- Custom ranges via time picker
- Auto-refresh intervals: 30s to 5m

### Panel Modifications
Dashboard panels can be customized:

1. **Thresholds**: Adjust color thresholds in panel settings
2. **Queries**: Modify InfluxDB queries for different metrics
3. **Visualizations**: Change chart types (line, bar, table, stat)
4. **Alerts**: Configure Grafana alerts for critical metrics

### Adding New Metrics

To add new GLQ metrics:

1. **Update Data Collection**: Modify the LCW fetcher to collect new fields
2. **Create Panels**: Add new panels using the existing patterns
3. **Update Queries**: Write InfluxDB queries for the new metrics
4. **Configure Thresholds**: Set appropriate alert thresholds

## Troubleshooting

### Common Issues

#### No Data Displayed
1. Check InfluxDB connection in Grafana data sources
2. Verify the LCW API fetcher is running and collecting GLQ data
3. Check the measurement name: `cryptocurrency_data`
4. Verify the tag filter: `code == "GLQ"`

#### Incorrect Values
1. Check data source query syntax
2. Verify field names match the InfluxDB schema
3. Check time range settings
4. Validate data types (float vs integer)

#### Dashboard Not Loading
1. Check JSON syntax in dashboard files
2. Verify provisioning configuration
3. Check Grafana logs for errors
4. Restart Grafana service

### Query Debugging

Use Grafana's query inspector to debug InfluxDB queries:

1. Open panel edit mode
2. Click "Query Inspector"
3. Check the generated InfluxDB query
4. Test queries directly in InfluxDB CLI

### Performance Optimization

For large datasets:

1. **Adjust Aggregation**: Use appropriate `aggregateWindow()` intervals
2. **Limit Data**: Use `limit()` for table panels
3. **Optimize Queries**: Use specific field filters
4. **Cache Settings**: Configure Grafana caching for frequently accessed panels

## Best Practices

### Monitoring Workflow

1. **Start with Main Dashboard**: Overview of GLQ performance
2. **Check Network Health**: Assess ecosystem stability
3. **Monitor Alerts**: Watch for critical threshold breaches
4. **Historical Analysis**: Use time ranges for trend analysis

### Alert Configuration

1. **Set Realistic Thresholds**: Based on GLQ's historical volatility
2. **Use Multiple Timeframes**: Different thresholds for 1H vs 24H changes
3. **Configure Notifications**: Set up Grafana alert notifications
4. **Regular Reviews**: Adjust thresholds based on market conditions

### Dashboard Maintenance

1. **Regular Updates**: Keep dashboard JSON files version controlled
2. **Backup Configuration**: Regular Grafana configuration backups
3. **Monitor Performance**: Watch dashboard loading times
4. **Update Documentation**: Keep this guide current with changes

## Support and Contact

For issues with GLQ dashboards:

1. **Technical Issues**: Check Grafana and InfluxDB logs
2. **Data Issues**: Verify LCW API fetcher status
3. **Feature Requests**: Submit enhancement requests
4. **Documentation Updates**: Contribute to this guide

## Version History

- **v1.0**: Initial GLQ dashboard implementation
  - Main monitoring dashboard
  - Network health dashboard  
  - Alerts and monitoring dashboard
  - Grafana provisioning configuration
  - Comprehensive documentation

## Appendix

### InfluxDB Query Examples

#### Basic Price Query
```flux
from(bucket: "crypto_data")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "cryptocurrency_data")
  |> filter(fn: (r) => r["_field"] == "rate")
  |> filter(fn: (r) => r["code"] == "GLQ")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
```

#### Volume Anomaly Detection
```flux
current_volume = from(bucket: "crypto_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "cryptocurrency_data")
  |> filter(fn: (r) => r["_field"] == "volume")
  |> filter(fn: (r) => r["code"] == "GLQ")
  |> last()

avg_volume = from(bucket: "crypto_data")
  |> range(start: -7d)
  |> filter(fn: (r) => r["_measurement"] == "cryptocurrency_data")
  |> filter(fn: (r) => r["_field"] == "volume")
  |> filter(fn: (r) => r["code"] == "GLQ")
  |> mean()

union(tables: [current_volume, avg_volume])
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> map(fn: (r) => ({
    _time: r._time,
    _value: if r.volume < r.mean * 0.3 then 1.0 else if r.volume > r.mean * 3.0 then 2.0 else 0.0
  }))
```

#### Network Health Score
```flux
volume = from(bucket: "crypto_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "cryptocurrency_data")
  |> filter(fn: (r) => r["_field"] == "volume")
  |> filter(fn: (r) => r["code"] == "GLQ")
  |> last()
  |> map(fn: (r) => ({_time: r._time, _field: "volume_score", _value: if r._value > 100000.0 then 30.0 else r._value / 100000.0 * 30.0}))

exchanges = from(bucket: "crypto_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "cryptocurrency_data")
  |> filter(fn: (r) => r["_field"] == "exchanges")
  |> filter(fn: (r) => r["code"] == "GLQ")
  |> last()
  |> map(fn: (r) => ({_time: r._time, _field: "exchange_score", _value: if float(v: r._value) > 10.0 then 35.0 else float(v: r._value) / 10.0 * 35.0}))

rank = from(bucket: "crypto_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "cryptocurrency_data")
  |> filter(fn: (r) => r["_field"] == "rank")
  |> filter(fn: (r) => r["code"] == "GLQ")
  |> last()
  |> map(fn: (r) => ({_time: r._time, _field: "rank_score", _value: if float(v: r._value) < 100.0 then 35.0 else 35.0 - ((float(v: r._value) - 100.0) / 1000.0 * 35.0)}))

union(tables: [volume, exchanges, rank])
  |> sum()
```

### Color Scheme Reference

#### Alert Colors
- **Green** (#73BF69): Normal/Healthy status
- **Yellow** (#FADE2A): Warning/Caution
- **Orange** (#FF9830): Elevated concern
- **Red** (#F2495C): Critical/Alert
- **Light Green** (#96D98D): Positive indicator

#### Chart Colors
- **Primary**: Grafana palette-classic mode
- **Background**: Dark theme optimized
- **Thresholds**: Color-coded by severity level

This completes the comprehensive GLQ GraphLinq Chain dashboard documentation.