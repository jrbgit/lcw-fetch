#!/usr/bin/env python3
"""
Simple script to test data access from InfluxDB
"""

import requests
import json
from datetime import datetime

def test_influxdb_connection():
    """Test direct connection to InfluxDB"""
    url = "http://localhost:8086/api/v2/query?org=cryptocurrency"
    headers = {
        "Authorization": "Token your_super_secret_admin_token",
        "Content-Type": "application/vnd.flux",
        "Accept": "application/csv"
    }
    
    # Simple query to get recent coin data
    query = """
from(bucket: "crypto_data")
  |> range(start: -30m)
  |> filter(fn: (r) => r["_measurement"] == "coins")
  |> filter(fn: (r) => r["_field"] == "rate")
  |> limit(n: 10)
"""
    
    try:
        response = requests.post(url, headers=headers, data=query)
        if response.status_code == 200:
            print(f"✅ InfluxDB Connection: SUCCESS")
            print(f"📊 Data Retrieved: {len(response.text.split(chr(10)))} lines")
            return True
        else:
            print(f"❌ InfluxDB Connection: FAILED ({response.status_code})")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ InfluxDB Connection: ERROR - {e}")
        return False

def test_grafana_connection():
    """Test Grafana health"""
    try:
        response = requests.get("http://localhost:3000/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Grafana Health: {data}")
            return True
        else:
            print(f"❌ Grafana Health: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Grafana Health: ERROR - {e}")
        return False

if __name__ == "__main__":
    print(f"🔍 Testing Data Access at {datetime.now()}")
    print("=" * 50)
    
    influx_ok = test_influxdb_connection()
    grafana_ok = test_grafana_connection()
    
    print("=" * 50)
    if influx_ok and grafana_ok:
        print("✅ All systems operational!")
        print("🌐 Access Grafana Dashboard: http://localhost:3000")
        print("🔐 Login: admin / admin")
    else:
        print("❌ Some systems have issues")
