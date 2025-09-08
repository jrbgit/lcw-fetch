# Deployment Guide

This guide covers different deployment options for the Live Coin Watch API Data Fetcher.

## Table of Contents
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring Setup](#monitoring-setup)

## Local Development

### Quick Setup
```bash
# Clone and setup
git clone <repository-url>
cd lcw_api
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run
python -m lcw_fetcher.main status
python -m lcw_fetcher.main run-once
```

### Development with Local InfluxDB
```bash
# Start InfluxDB using Docker
docker run -d -p 8086:8086 \
  -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=password123 \
  -e DOCKER_INFLUXDB_INIT_ORG=myorg \
  -e DOCKER_INFLUXDB_INIT_BUCKET=crypto_data \
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-auth-token \
  -v influxdb2:/var/lib/influxdb2 \
  influxdb:2.7

# Update .env
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=my-super-secret-auth-token
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=crypto_data
```

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Setup environment variables:**
   ```bash
   # Create .env file for docker-compose
   cat > .env << EOF
   LCW_API_KEY=your_live_coin_watch_api_key
   INFLUXDB_TOKEN=your_super_secret_admin_token
   INFLUXDB_ORG=cryptocurrency
   INFLUXDB_BUCKET=crypto_data
   LOG_LEVEL=INFO
   FETCH_INTERVAL_MINUTES=5
   EOF
   ```

2. **Start the stack:**
   ```bash
   docker-compose up -d
   ```

3. **Check status:**
   ```bash
   docker-compose logs lcw-fetcher
   docker-compose exec lcw-fetcher python -m lcw_fetcher.main status
   ```

4. **Access services:**
   - InfluxDB UI: http://localhost:8086
   - Grafana: http://localhost:3000 (admin/admin)

### Manual Docker Build

```bash
# Build the image
docker build -t lcw-fetcher .

# Run with environment variables
docker run -d \
  --name lcw-fetcher \
  -e LCW_API_KEY=your_api_key \
  -e INFLUXDB_URL=http://your-influxdb:8086 \
  -e INFLUXDB_TOKEN=your_token \
  -e INFLUXDB_ORG=your_org \
  -e INFLUXDB_BUCKET=crypto_data \
  -v $(pwd)/logs:/app/logs \
  lcw-fetcher
```

## Production Deployment

### Prerequisites
- Docker and Docker Compose
- Reverse proxy (nginx/traefik) for HTTPS
- Monitoring solution (Prometheus/Grafana)
- Log aggregation (ELK stack or similar)

### Production Docker Compose

```yaml
version: '3.8'

services:
  influxdb:
    image: influxdb:2.7
    container_name: lcw-influxdb-prod
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD_FILE=/run/secrets/influxdb_password
      - DOCKER_INFLUXDB_INIT_ORG=production
      - DOCKER_INFLUXDB_INIT_BUCKET=crypto_production
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN_FILE=/run/secrets/influxdb_token
    volumes:
      - influxdb-data:/var/lib/influxdb2
      - influxdb-config:/etc/influxdb2
    secrets:
      - influxdb_password
      - influxdb_token
    networks:
      - internal
    restart: unless-stopped

  lcw-fetcher:
    image: lcw-fetcher:latest
    container_name: lcw-fetcher-prod
    environment:
      - LCW_API_KEY_FILE=/run/secrets/lcw_api_key
      - INFLUXDB_URL=http://influxdb:8086
      - INFLUXDB_TOKEN_FILE=/run/secrets/influxdb_token
      - INFLUXDB_ORG=production
      - INFLUXDB_BUCKET=crypto_production
      - LOG_LEVEL=INFO
      - FETCH_INTERVAL_MINUTES=10
    volumes:
      - ./logs:/app/logs
    secrets:
      - lcw_api_key
      - influxdb_token
    networks:
      - internal
    restart: unless-stopped
    depends_on:
      - influxdb

secrets:
  lcw_api_key:
    file: ./secrets/lcw_api_key.txt
  influxdb_password:
    file: ./secrets/influxdb_password.txt
  influxdb_token:
    file: ./secrets/influxdb_token.txt

volumes:
  influxdb-data:
  influxdb-config:

networks:
  internal:
    internal: true
```

### Security Considerations

1. **Secrets Management:**
   ```bash
   # Create secrets directory
   mkdir -p secrets
   echo "your_api_key" > secrets/lcw_api_key.txt
   echo "strong_password" > secrets/influxdb_password.txt
   echo "super_secret_token" > secrets/influxdb_token.txt
   chmod 600 secrets/*
   ```

2. **Firewall Configuration:**
   ```bash
   # Only allow necessary ports
   sudo ufw allow ssh
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw --force enable
   ```

3. **Log Rotation:**
   ```bash
   # Add to /etc/logrotate.d/lcw-fetcher
   /path/to/lcw_api/logs/*.log {
       daily
       missingok
       rotate 30
       compress
       delaycompress
       notifempty
       postrotate
           docker-compose restart lcw-fetcher
       endscript
   }
   ```

## Cloud Deployment

### AWS Deployment

#### Using ECS (Elastic Container Service)

1. **Create ECR repository:**
   ```bash
   aws ecr create-repository --repository-name lcw-fetcher
   ```

2. **Build and push image:**
   ```bash
   # Get login token
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
   
   # Build and tag
   docker build -t lcw-fetcher .
   docker tag lcw-fetcher:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/lcw-fetcher:latest
   
   # Push
   docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/lcw-fetcher:latest
   ```

3. **ECS Task Definition (task-definition.json):**
   ```json
   {
     "family": "lcw-fetcher",
     "networkMode": "awsvpc",
     "requiresAttributes": [
       {
         "name": "com.amazonaws.ecs.capability.docker-remote-api.1.18"
       }
     ],
     "cpu": "512",
     "memory": "1024",
     "containerDefinitions": [
       {
         "name": "lcw-fetcher",
         "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/lcw-fetcher:latest",
         "essential": true,
         "environment": [
           {
             "name": "INFLUXDB_URL",
             "value": "https://your-influxdb-cloud-url.com"
           }
         ],
         "secrets": [
           {
             "name": "LCW_API_KEY",
             "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:lcw-api-key-abc123"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/lcw-fetcher",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

#### Using Lambda (for serverless)

```python
# lambda_handler.py
import json
import os
from lcw_fetcher import Config, DataFetcher

def lambda_handler(event, context):
    config = Config()
    fetcher = DataFetcher(config)
    
    try:
        stats = fetcher.run_full_fetch()
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Fetch completed successfully',
                'stats': stats
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
    finally:
        fetcher.close()
```

### Google Cloud Platform

#### Using Cloud Run

1. **Build and deploy:**
   ```bash
   # Build with Cloud Build
   gcloud builds submit --tag gcr.io/PROJECT_ID/lcw-fetcher
   
   # Deploy to Cloud Run
   gcloud run deploy lcw-fetcher \
     --image gcr.io/PROJECT_ID/lcw-fetcher \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars "INFLUXDB_URL=https://your-influxdb-url.com"
   ```

2. **Schedule with Cloud Scheduler:**
   ```bash
   gcloud scheduler jobs create http lcw-fetch-job \
     --schedule="*/5 * * * *" \
     --uri="https://your-cloud-run-url.com/fetch" \
     --http-method=POST
   ```

## Monitoring Setup

### Grafana Dashboards

1. **Add InfluxDB data source:**
   - URL: http://influxdb:8086
   - Organization: your_org
   - Token: your_token
   - Default Bucket: crypto_data

2. **Example dashboard queries:**
   ```flux
   // Bitcoin price over time
   from(bucket: "crypto_data")
     |> range(start: -24h)
     |> filter(fn: (r) => r._measurement == "cryptocurrency_data")
     |> filter(fn: (r) => r.code == "BTC")
     |> filter(fn: (r) => r._field == "rate")
   
   // Market cap trend
   from(bucket: "crypto_data")
     |> range(start: -7d)
     |> filter(fn: (r) => r._measurement == "market_overview")
     |> filter(fn: (r) => r._field == "total_market_cap")
     |> aggregateWindow(every: 1h, fn: mean)
   ```

### Alerting

#### Prometheus Alerts (alerts.yml)
```yaml
groups:
  - name: lcw-fetcher
    rules:
      - alert: LCWFetcherDown
        expr: up{job="lcw-fetcher"} == 0
        for: 5m
        annotations:
          summary: "LCW Fetcher is down"
          
      - alert: HighErrorRate
        expr: rate(lcw_fetcher_errors_total[5m]) > 0.1
        for: 2m
        annotations:
          summary: "High error rate in LCW Fetcher"
```

### Health Monitoring

```bash
#!/bin/bash
# health-check.sh

CONTAINER_NAME="lcw-data-fetcher"
WEBHOOK_URL="https://your-webhook-url.com"

# Check if container is running
if ! docker ps | grep -q $CONTAINER_NAME; then
    curl -X POST $WEBHOOK_URL -d '{"text":"🚨 LCW Fetcher container is not running!"}'
    exit 1
fi

# Check application health
if ! docker exec $CONTAINER_NAME python -m lcw_fetcher.main status > /dev/null 2>&1; then
    curl -X POST $WEBHOOK_URL -d '{"text":"🚨 LCW Fetcher health check failed!"}'
    exit 1
fi

echo "✅ Health check passed"
```

## Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup-influxdb.sh

BACKUP_DIR="/backups/influxdb"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
docker exec lcw-influxdb influx backup \
  --bucket crypto_data \
  --org cryptocurrency \
  /var/lib/influxdb2/backup_${DATE}

# Copy to host
docker cp lcw-influxdb:/var/lib/influxdb2/backup_${DATE} ${BACKUP_DIR}/

# Compress
tar -czf ${BACKUP_DIR}/backup_${DATE}.tar.gz -C ${BACKUP_DIR} backup_${DATE}
rm -rf ${BACKUP_DIR}/backup_${DATE}

# Cleanup old backups (keep 7 days)
find ${BACKUP_DIR} -name "backup_*.tar.gz" -mtime +7 -delete
```

### Data Recovery

```bash
# Stop services
docker-compose down

# Restore data
tar -xzf /backups/influxdb/backup_YYYYMMDD_HHMMSS.tar.gz -C /tmp/
docker run --rm -v influxdb-storage:/var/lib/influxdb2 \
  -v /tmp/backup_YYYYMMDD_HHMMSS:/restore \
  influxdb:2.7 \
  influx restore --bucket crypto_data /restore

# Start services
docker-compose up -d
```

## Troubleshooting

### Common Issues

1. **Container won't start:**
   ```bash
   # Check logs
   docker logs lcw-data-fetcher
   
   # Check environment variables
   docker exec lcw-data-fetcher env | grep -E "LCW|INFLUX"
   ```

2. **Database connection issues:**
   ```bash
   # Test connection
   docker exec lcw-data-fetcher python -c "
   from lcw_fetcher.database import InfluxDBClient
   import os
   client = InfluxDBClient(
       os.getenv('INFLUXDB_URL'),
       os.getenv('INFLUXDB_TOKEN'),
       os.getenv('INFLUXDB_ORG'),
       os.getenv('INFLUXDB_BUCKET')
   )
   client.connect()
   print('Connection successful')
   "
   ```

3. **API rate limiting:**
   ```bash
   # Check current usage
   docker exec lcw-data-fetcher python -m lcw_fetcher.main status
   
   # Adjust fetch frequency
   docker-compose exec lcw-fetcher env
   # Update FETCH_INTERVAL_MINUTES and restart
   ```

### Performance Tuning

1. **Resource allocation:**
   ```yaml
   # In docker-compose.yml
   lcw-fetcher:
     deploy:
       resources:
         limits:
           cpus: '0.5'
           memory: 512M
         reservations:
           cpus: '0.25'
           memory: 256M
   ```

2. **Database optimization:**
   ```bash
   # InfluxDB configuration
   docker exec lcw-influxdb influx config --help
   ```

For additional help, check the main README.md or create an issue in the repository.
