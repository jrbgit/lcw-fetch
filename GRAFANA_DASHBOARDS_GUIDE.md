# Live Coin Watch API - Grafana Dashboards Guide

## 🎯 Overview

This project now includes **5 comprehensive Grafana dashboards** designed to provide complete monitoring and analysis of your cryptocurrency data collection system and market trends.

## 📊 Dashboard Collection

### 1. **LCW API - Cryptocurrency Dashboard** (Original)
**File**: `lcw-dashboard.json`  
**UID**: `lcw-crypto-dashboard`

**Purpose**: Main cryptocurrency monitoring dashboard  
**Features**:
- Top 5 crypto prices (1 hour view)
- Data collection counter
- Hourly price changes
- Trading volume charts
- Current price overview for top 10 cryptocurrencies

**Key Panels**:
- Real-time price tracking (BTC, ETH, BNB, XRP, ADA)
- 24H price change percentages
- Trading volume trends
- Live data collection verification

---

### 2. **LCW API - System Health Monitor** (New)
**File**: `system-health.json`  
**UID**: `lcw-system-health`

**Purpose**: Monitor API usage, system status, and data collection health  
**Features**:
- API request monitoring with thresholds
- Data collection status indicators
- System performance metrics
- Data distribution analysis

**Key Panels**:
- 🚨 API Requests Used (with threshold warnings)
- 🔍 Data Collection Status (UP/DOWN indicator)
- 📊 Data Collection Rate (24H trend)
- 🔄 API Usage Trend
- 📈 Top Active Coins (by data points)
- 🥧 Data Distribution by Type

**Alert Thresholds**:
- API Usage: Yellow >7000, Red >9500 requests
- Data Collection: Red if no data in last 5 minutes

---

### 3. **LCW API - Market Analysis** (New)
**File**: `market-analysis.json`  
**UID**: `lcw-market-analysis`

**Purpose**: Advanced market analysis and trend monitoring  
**Features**:
- Total market metrics and trends
- Bitcoin dominance tracking
- Top 15 cryptocurrency rankings
- Market cap distribution analysis

**Key Panels**:
- 💰 Total Market Cap
- 📊 24H Trading Volume
- ⚡ Bitcoin Dominance (with threshold indicators)
- 🏆 Top 15 Cryptocurrencies by Market Cap
- 🥧 Market Cap Distribution (Top 10)
- 📈 Market Cap & Volume Trends (24H)
- 📊 Top 10 - 24H Price Changes
- 📉 Trading Volume Trends

**Key Insights**:
- Market dominance tracking (BTC vs. altcoins)
- Market cap trend analysis
- Volume-based activity monitoring

---

### 4. **LCW API - Exchange Activity** (New)
**File**: `exchange-activity.json`  
**UID**: `lcw-exchange-activity`

**Purpose**: Monitor exchange trading activity and performance  
**Features**:
- Exchange volume and visitor tracking
- Exchange efficiency metrics
- Exchange comparison analysis

**Key Panels**:
- 🏛️ Active Exchanges count
- 💱 Total Exchange Volume
- 👥 Total Daily Visitors
- 💸 Average Volume per Visitor
- 📊 Top 15 Exchanges by Volume (table)
- 🥧 Exchange Volume Distribution
- 📈 Top 5 Exchange Volume Trends (24H)
- 👨‍👩‍👧‍👦 Top 5 Exchange Visitor Trends (24H)
- 📊 Exchange Efficiency Rankings
- 🥧 Visitor Distribution

**Exchange Metrics**:
- Trading volume monitoring
- User activity tracking (visitors)
- Efficiency analysis (volume per visitor)

---

### 5. **LCW API - Portfolio Tracking** (New)
**File**: `portfolio-tracking.json`  
**UID**: `lcw-portfolio-tracking`

**Purpose**: Track specific cryptocurrency portfolios and performance  
**Features**:
- Portfolio value calculation
- Asset allocation monitoring
- Performance tracking and analysis
- Customizable coin selection

**Key Panels**:
- 💰 Total Portfolio Value (calculated from holdings)
- 📊 Portfolio 24H Change (weighted average)
- 🚀 Best Performer identification
- 📈 Portfolio Holdings Count
- 🥧 Portfolio Allocation by Value
- 📊 Portfolio Holdings Details (table)
- 📈 Portfolio Price Trends (24H)
- 📊 Portfolio Performance Comparison
- 📈 Portfolio Trading Volume Trends
- 🥧 Portfolio Volume Distribution

**Sample Portfolio**:
- BTC: 0.5 coins
- ETH: 2.0 coins  
- GLQ: 10,000 coins

**Template Variables**:
- `portfolio_coins`: Customizable coin selection (BTC, ETH, GLQ, BNB, XRP, ADA, MATIC, DOT, LINK, UNI)

---

### 6. **LCW API - Alert & Threshold Monitor** (New)
**File**: `alerting-thresholds.json`  
**UID**: `lcw-alert-thresholds`

**Purpose**: Visual alerting with threshold-based monitoring  
**Features**:
- Critical metric alerts with visual thresholds
- Color-coded warning systems
- Real-time status monitoring
- Alert status table

**Key Panels**:
- 🚨 **API Usage Alert** (Threshold: 8500)
  - Green: <7000, Yellow: 7000-8499, Orange: 8500-9499, Red: >9500
- 🔍 **Data Collection Health** (UP/DOWN status)
- ⚠️ **API Credits Remaining** (Min: 1000)
  - Red: <1000, Yellow: 1000-2999, Green: >3000
- 📉 **Bitcoin 24H Change Alert** (-20% threshold)
- 🚨 **API Usage Trend** with visual threshold areas
- 📊 **Portfolio Price Change Alerts** (-20%, -30% thresholds)
- 🚨 **Cryptocurrency Alert Status Table**
  - ✅ OK: >-5% change
  - ⚠️ WARNING: -5% to -30% change  
  - 🚨 CRITICAL: <-30% change
- 💰 **Total Market Cap Alert** ($1.5T/$2T thresholds)
- ⚡ **Bitcoin Dominance Alert** (60%/70% thresholds)

**Additional Status Panels**:
- 📊 Data Collection Rate Alert (Min: 50 data points)
- 🔥 API Usage Percentage (30%/50% warning levels)
- ₿ Bitcoin Price Alert ($30K/$35K)
- Ξ Ethereum Price Alert ($1.8K/$2.2K)

---

## 🚀 Getting Started

### Access Your Dashboards

1. **Start your system**:
   ```powershell
   docker-compose up -d
   ```

2. **Access Grafana**:
   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `admin`

3. **Navigate to Dashboards**:
   - Browse → Dashboards → Live Coin Watch folder
   - Or use the search function to find dashboards by name

### Dashboard Organization

Dashboards are organized into folders:
- **Live Coin Watch**: Main cryptocurrency dashboard
- **System Health**: System monitoring and health dashboards  
- **Market Analytics**: Market analysis and trend dashboards
- **Portfolio Management**: Portfolio tracking and alerting dashboards

## ⚙️ Customization

### Portfolio Dashboard Customization

1. **Update Portfolio Holdings**:
   - Edit the Flux queries in portfolio panels
   - Modify the multiplication factors for your actual holdings:
     ```flux
     |> map(fn: (r) => ({r with _value: r._value * YOUR_AMOUNT}))
     ```

2. **Add New Coins**:
   - Use the `portfolio_coins` template variable
   - Select additional coins from the dropdown

3. **Adjust Weightings**:
   - Modify the weighted average calculations in Portfolio 24H Change panel

### Alert Thresholds Customization

1. **API Usage Thresholds**:
   - Edit the threshold values in panel field configs
   - Modify the Flux query threshold values

2. **Price Change Alerts**:
   - Update percentage thresholds in panel configurations
   - Adjust color schemes for different warning levels

3. **Market Cap Alerts**:
   - Modify the threshold values ($1.5T, $2T) based on market conditions

## 📊 Data Sources and Queries

### Measurements Used

- **`coins`**: Cryptocurrency price and market data
  - Fields: `rate`, `volume`, `market_cap`, `delta_24h`, `delta_7d`, `delta_30d`
  - Tags: `code`, `name`, `currency`

- **`exchange_data`**: Exchange activity and metrics
  - Fields: `volume`, `visitors`, `volume_per_visitor`, `rank`
  - Tags: `code`, `name`, `currency`

- **`market_overview`**: Global market statistics
  - Fields: `total_market_cap`, `total_volume`, `btc_dominance`
  - Tags: `currency`

- **`api_usage`**: System monitoring metrics
  - Fields: `requests_made`, `requests_remaining`

### Sample Queries

**Get Portfolio Value**:
```flux
// Calculate total portfolio value
btc = from(bucket: "crypto_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "coins")
  |> filter(fn: (r) => r["_field"] == "rate")
  |> filter(fn: (r) => r["code"] == "BTC")
  |> last()
  |> map(fn: (r) => ({r with _value: r._value * 0.5}))

union(tables: [btc, eth, glq])
  |> sum()
```

**API Usage Alert**:
```flux
from(bucket: "crypto_data")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "api_usage")
  |> filter(fn: (r) => r["_field"] == "requests_made")
  |> last()
```

## 🚨 Alert Configuration

### Grafana Alerting (Optional)

For production use, consider setting up Grafana alerts:

1. **Configure Notification Channels**:
   - Email, Slack, Discord, or webhook endpoints
   - Go to Alerting → Notification channels

2. **Set Up Alert Rules**:
   - Based on the threshold panels in the Alert dashboard
   - Configure firing conditions and recovery conditions

3. **Example Alert Rules**:
   - API usage >8500 requests
   - Data collection health check failure
   - Portfolio value change >-20%
   - Bitcoin price <$30,000

### External Monitoring

Consider integrating with:
- **Prometheus** for metrics collection
- **AlertManager** for alert routing
- **PagerDuty** for incident management
- **Webhook notifications** for custom integrations

## 🔧 Troubleshooting

### Common Issues

1. **No Data Showing**:
   - Verify InfluxDB connection
   - Check data source configuration
   - Ensure data is being written to correct measurements

2. **Dashboard Not Loading**:
   - Check Grafana logs: `docker-compose logs grafana`
   - Verify dashboard provisioning configuration
   - Restart Grafana: `docker-compose restart grafana`

3. **Query Errors**:
   - Validate Flux query syntax
   - Check measurement and field names
   - Verify time range settings

4. **Alert Thresholds Not Working**:
   - Check threshold configuration in panel field config
   - Verify data types match threshold expectations
   - Test queries independently

### Performance Optimization

1. **Query Performance**:
   - Use appropriate time ranges
   - Implement data aggregation for long periods
   - Consider data retention policies

2. **Dashboard Performance**:
   - Limit the number of panels per dashboard
   - Use efficient Flux queries
   - Set appropriate refresh intervals

3. **Resource Usage**:
   - Monitor Grafana resource consumption
   - Optimize InfluxDB performance
   - Consider dashboard caching

## 📚 Additional Resources

### Grafana Documentation
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/)
- [InfluxDB Data Source](https://grafana.com/docs/grafana/latest/datasources/influxdb/)
- [Flux Query Language](https://docs.influxdata.com/flux/v0.x/)

### Customization Examples
- [Panel Configuration](https://grafana.com/docs/grafana/latest/panels/)
- [Template Variables](https://grafana.com/docs/grafana/latest/variables/)
- [Alert Rules](https://grafana.com/docs/grafana/latest/alerting/)

### Community Resources
- [Grafana Community Dashboards](https://grafana.com/grafana/dashboards/)
- [InfluxDB Community](https://community.influxdata.com/)
- [Cryptocurrency Dashboard Examples](https://grafana.com/grafana/dashboards/?search=cryptocurrency)

---

## 🎉 Conclusion

Your Live Coin Watch API project now includes a comprehensive monitoring solution with:

- ✅ **5 specialized dashboards** covering all aspects of cryptocurrency monitoring
- ✅ **Visual alerting system** with customizable thresholds  
- ✅ **Portfolio tracking capabilities** with performance analysis
- ✅ **System health monitoring** with API usage tracking
- ✅ **Advanced market analysis** with trend identification
- ✅ **Exchange activity monitoring** with efficiency metrics

The dashboards are designed to be:
- **Production-ready** with proper error handling
- **Highly customizable** with template variables and configurable thresholds
- **Scalable** to handle additional cryptocurrencies and metrics
- **Intuitive** with clear visual indicators and organized layouts

Start monitoring your cryptocurrency data like a pro! 🚀📊