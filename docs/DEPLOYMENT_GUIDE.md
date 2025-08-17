# IngressKit Deployment Guide

## Overview

This guide covers deploying IngressKit in various environments, from local development to production-ready deployments. IngressKit consists of a Python SDK and a FastAPI server that can be deployed independently or together.

## Table of Contents
1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Configuration Management](#configuration-management)
5. [Monitoring and Maintenance](#monitoring-and-maintenance)
6. [Scaling Considerations](#scaling-considerations)

## Local Development Setup

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Git (for cloning the repository)

### SDK Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd IngressKit

# Set up Python SDK
cd sdk/python
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Test the SDK
python -m ingresskit.cli --in ../../examples/contacts_messy.csv --out ../../examples/contacts_clean.csv --schema contacts
```

### Server Development Setup

```bash
# Set up FastAPI server
cd server
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create environment file
cp .env.example .env  # If available, or create manually

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### Development Environment Variables

Create a `.env` file in the `server/` directory:

```bash
# Basic configuration
INGRESSKIT_API_KEYS=dev_key_1:10000,dev_key_2:5000
INGRESSKIT_FREE_PER_DAY=1000
INGRESSKIT_ADMIN_TOKEN=dev_admin_token_123

# Stripe configuration (optional for development)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Checkout URLs
CHECKOUT_SUCCESS_URL=http://localhost:3000/success
CHECKOUT_CANCEL_URL=http://localhost:3000/cancel
```

### Testing the Setup

```bash
# Test health endpoint
curl http://localhost:8080/ping
# Expected: {"message": "pong"}

# Test webhook processing
curl -X POST "http://localhost:8080/v1/webhooks/ingest?source=stripe" \
  -H "Authorization: Bearer dev_key_1" \
  -H "Content-Type: application/json" \
  -d '{"id":"evt_test","type":"charge.succeeded","data":{"object":{"id":"ch_test","amount":1000,"customer":"cus_test"}},"created":1693526400}'

# Test JSON normalization
curl -X POST "http://localhost:8080/v1/json/normalize?schema=contacts" \
  -H "Authorization: Bearer dev_key_1" \
  -H "Content-Type: application/json" \
  -d '{"Email":"TEST@EXAMPLE.COM","Name":"Smith, John"}'
```

## Docker Deployment

### Building the Docker Image

The server includes a `Dockerfile` for containerized deployment:

```bash
cd server

# Build the image
docker build -t ingresskit-server:latest .

# Run the container
docker run -p 8080:8080 \
  -e INGRESSKIT_API_KEYS="prod_key_1:50000" \
  -e INGRESSKIT_ADMIN_TOKEN="secure_admin_token" \
  ingresskit-server:latest
```

### Docker Compose Setup

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  ingresskit-server:
    build:
      context: ./server
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - INGRESSKIT_API_KEYS=prod_key_1:50000,prod_key_2:25000
      - INGRESSKIT_ADMIN_TOKEN=secure_admin_token_123
      - INGRESSKIT_FREE_PER_DAY=100
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
      - STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET}
    volumes:
      - ./data:/app/data  # Persist credit data
      - ./logs:/app/logs  # Log persistence
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - ingresskit-server
    restart: unless-stopped
```

### Running with Docker Compose

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f ingresskit-server

# Stop services
docker-compose down
```

## Production Deployment

### System Requirements

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 2GB
- Storage: 10GB
- OS: Ubuntu 20.04+ / CentOS 8+ / Amazon Linux 2

**Recommended for Production:**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB+ SSD
- OS: Ubuntu 22.04 LTS

### systemd Service Setup

The repository includes systemd service files in `server/deploy/`:

```bash
# Copy and install systemd service
sudo cp server/deploy/ingresskit.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ingresskit
sudo systemctl start ingresskit

# Check status
sudo systemctl status ingresskit
```

### Production Environment Setup

1. **Create dedicated user:**
```bash
sudo useradd -r -s /bin/false ingresskit
sudo mkdir -p /opt/ingresskit
sudo chown ingresskit:ingresskit /opt/ingresskit
```

2. **Deploy application:**
```bash
# Clone repository to production location
sudo -u ingresskit git clone <repository-url> /opt/ingresskit
cd /opt/ingresskit

# Set up Python environment
sudo -u ingresskit python3 -m venv server/.venv
sudo -u ingresskit server/.venv/bin/pip install -r server/requirements.txt
```

3. **Configure environment:**
```bash
# Create production environment file
sudo -u ingresskit touch /opt/ingresskit/server/.env
sudo chmod 600 /opt/ingresskit/server/.env

# Edit with production values
sudo -u ingresskit nano /opt/ingresskit/server/.env
```

### Production Environment Variables

```bash
# Production .env file (/opt/ingresskit/server/.env)

# API Keys and Security
INGRESSKIT_API_KEYS=prod_key_abc123:100000,prod_key_def456:50000
INGRESSKIT_ADMIN_TOKEN=super_secure_admin_token_production
INGRESSKIT_FREE_PER_DAY=50

# Stripe Configuration
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
INGRESSKIT_PRICE_MAP=price_live_small:5000,price_live_large:25000,price_live_enterprise:100000
INGRESSKIT_PRICE_ALIASES=small:price_live_small,large:price_live_large,enterprise:price_live_enterprise

# URLs
CHECKOUT_SUCCESS_URL=https://yourdomain.com/billing/success
CHECKOUT_CANCEL_URL=https://yourdomain.com/billing/cancel

# Logging (optional)
LOG_LEVEL=INFO
LOG_FILE=/opt/ingresskit/logs/server.log
```

### Nginx Reverse Proxy Configuration

Create `/etc/nginx/sites-available/ingresskit`:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/yourdomain.com.pem;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # Security Headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Client Body Size (for large CSV uploads via future endpoints)
    client_max_body_size 100M;
    
    # Proxy to IngressKit server
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check endpoint (no rate limiting)
    location /ping {
        proxy_pass http://127.0.0.1:8080/ping;
        access_log off;
    }
    
    # Static files (if any)
    location /static/ {
        proxy_pass http://127.0.0.1:8080/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/ingresskit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate Setup

Using Let's Encrypt with Certbot:

```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Or iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

## Configuration Management

### Environment Variable Reference

#### Core Configuration
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INGRESSKIT_API_KEYS` | No | None | Comma-separated key:credits pairs |
| `INGRESSKIT_ADMIN_TOKEN` | Production | None | Admin operations token |
| `INGRESSKIT_FREE_PER_DAY` | No | 100 | Free credits for unknown keys |

#### Stripe Integration
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STRIPE_SECRET_KEY` | For billing | None | Stripe API secret key |
| `STRIPE_WEBHOOK_SECRET` | For webhooks | None | Webhook endpoint secret |
| `INGRESSKIT_PRICE_MAP` | For billing | None | price_id:credits mapping |
| `INGRESSKIT_PRICE_ALIASES` | No | None | alias:price_id mapping |

#### URLs and Redirects
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CHECKOUT_SUCCESS_URL` | No | https://ingresskit.com/ | Post-payment redirect |
| `CHECKOUT_CANCEL_URL` | No | https://ingresskit.com/ | Payment cancel redirect |

### Configuration Validation

Create a configuration validation script:

```python
#!/usr/bin/env python3
import os
import sys

def validate_config():
    """Validate production configuration"""
    errors = []
    warnings = []
    
    # Required for production
    required_vars = [
        'INGRESSKIT_ADMIN_TOKEN',
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Stripe configuration
    stripe_key = os.getenv('STRIPE_SECRET_KEY')
    stripe_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    if stripe_key and not stripe_secret:
        warnings.append("STRIPE_SECRET_KEY set but STRIPE_WEBHOOK_SECRET missing")
    
    if stripe_key and not stripe_key.startswith(('sk_test_', 'sk_live_')):
        errors.append("Invalid STRIPE_SECRET_KEY format")
    
    # API Keys format
    api_keys = os.getenv('INGRESSKIT_API_KEYS')
    if api_keys:
        for pair in api_keys.split(','):
            if ':' not in pair:
                errors.append(f"Invalid API key format: {pair}")
    
    # Print results
    if errors:
        print("Configuration Errors:")
        for error in errors:
            print(f"  ❌ {error}")
    
    if warnings:
        print("Configuration Warnings:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    
    if not errors and not warnings:
        print("✅ Configuration validation passed")
    
    return len(errors) == 0

if __name__ == '__main__':
    if not validate_config():
        sys.exit(1)
```

## Monitoring and Maintenance

### Health Check Endpoints

IngressKit provides several endpoints for monitoring:

```bash
# Basic health check
curl http://localhost:8080/ping

# API key balance (requires valid key)
curl -H "Authorization: Bearer your-api-key" \
  http://localhost:8080/v1/billing/balance
```

### Log Management

Configure log rotation for production:

```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/ingresskit << EOF
/opt/ingresskit/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ingresskit ingresskit
    postrotate
        systemctl reload ingresskit
    endscript
}
EOF
```

### Monitoring Scripts

Create monitoring scripts for key metrics:

```bash
#!/bin/bash
# /opt/ingresskit/scripts/health_check.sh

API_KEY="your-monitoring-api-key"
BASE_URL="https://api.yourdomain.com"

# Test health endpoint
if ! curl -f -s "${BASE_URL}/ping" > /dev/null; then
    echo "CRITICAL: Health check failed"
    exit 2
fi

# Test API functionality
if ! curl -f -s -H "Authorization: Bearer ${API_KEY}" \
    "${BASE_URL}/v1/billing/balance" > /dev/null; then
    echo "WARNING: API functionality impaired"
    exit 1
fi

echo "OK: All checks passed"
exit 0
```

### Backup Procedures

The main data to backup is the credit balance file:

```bash
#!/bin/bash
# /opt/ingresskit/scripts/backup.sh

BACKUP_DIR="/opt/backups/ingresskit"
DATA_DIR="/opt/ingresskit/server/data"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "${BACKUP_DIR}"

# Backup credit data
cp "${DATA_DIR}/balances.json" "${BACKUP_DIR}/balances_${DATE}.json"

# Keep only last 30 days of backups
find "${BACKUP_DIR}" -name "balances_*.json" -mtime +30 -delete

echo "Backup completed: balances_${DATE}.json"
```

Add to crontab:
```bash
# Backup every 6 hours
0 */6 * * * /opt/ingresskit/scripts/backup.sh
```

### Update Procedures

Create an update script:

```bash
#!/bin/bash
# /opt/ingresskit/scripts/update.sh

set -e

INSTALL_DIR="/opt/ingresskit"
BACKUP_DIR="/opt/backups/ingresskit"

echo "Starting IngressKit update..."

# Backup current data
mkdir -p "${BACKUP_DIR}"
cp -r "${INSTALL_DIR}/server/data" "${BACKUP_DIR}/data_$(date +%Y%m%d_%H%M%S)"

# Stop service
sudo systemctl stop ingresskit

# Update code
cd "${INSTALL_DIR}"
sudo -u ingresskit git pull origin main

# Update dependencies
sudo -u ingresskit "${INSTALL_DIR}/server/.venv/bin/pip" install -r "${INSTALL_DIR}/server/requirements.txt"

# Restart service
sudo systemctl start ingresskit

# Verify health
sleep 5
if curl -f -s http://localhost:8080/ping > /dev/null; then
    echo "✅ Update completed successfully"
else
    echo "❌ Update failed - service unhealthy"
    exit 1
fi
```

## Scaling Considerations

### Horizontal Scaling

For high-traffic deployments, consider these scaling strategies:

#### 1. Load Balancer Configuration

```nginx
upstream ingresskit_backend {
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
    
    # Health check
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://ingresskit_backend;
        # ... other proxy settings
    }
}
```

#### 2. Multi-Instance Deployment

```bash
# Run multiple instances on different ports
uvicorn main:app --host 127.0.0.1 --port 8080 &
uvicorn main:app --host 127.0.0.1 --port 8081 &
uvicorn main:app --host 127.0.0.1 --port 8082 &
```

#### 3. Database Migration

For high-scale deployments, migrate from file-based storage:

```python
# Replace KeyStore with database implementation
import psycopg2
from typing import Dict

class PostgresKeyStore:
    def __init__(self, connection_string: str):
        self.conn_string = connection_string
    
    def get_balance(self, key: str) -> int:
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT balance FROM api_keys WHERE key = %s", (key,))
                result = cur.fetchone()
                return result[0] if result else 0
    
    def set_balance(self, key: str, balance: int) -> None:
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO api_keys (key, balance) 
                    VALUES (%s, %s) 
                    ON CONFLICT (key) 
                    DO UPDATE SET balance = EXCLUDED.balance
                """, (key, balance))
```

### Performance Optimization

#### 1. Async Processing
```python
import asyncio
import aiofiles

async def process_large_csv(file_path: str):
    """Async CSV processing for better throughput"""
    async with aiofiles.open(file_path, 'r') as f:
        # Process file asynchronously
        pass
```

#### 2. Caching Layer
```python
import redis
import json

class CachedKeyStore:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.cache_ttl = 300  # 5 minutes
    
    def get_balance(self, key: str) -> int:
        # Try cache first
        cached = self.redis.get(f"balance:{key}")
        if cached:
            return int(cached)
        
        # Fallback to database
        balance = self.db_get_balance(key)
        self.redis.setex(f"balance:{key}", self.cache_ttl, balance)
        return balance
```

### Infrastructure as Code

#### Terraform Example
```hcl
# main.tf
resource "aws_instance" "ingresskit" {
  count         = 3
  ami           = "ami-0c55b159cbfafe1d0"  # Ubuntu 20.04
  instance_type = "t3.medium"
  
  user_data = templatefile("install.sh", {
    api_keys = var.api_keys
    admin_token = var.admin_token
  })
  
  tags = {
    Name = "ingresskit-${count.index + 1}"
  }
}

resource "aws_lb" "ingresskit" {
  name               = "ingresskit-lb"
  internal           = false
  load_balancer_type = "application"
  
  subnets = var.subnet_ids
}
```

#### Kubernetes Deployment
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ingresskit
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ingresskit
  template:
    metadata:
      labels:
        app: ingresskit
    spec:
      containers:
      - name: ingresskit
        image: ingresskit:latest
        ports:
        - containerPort: 8080
        env:
        - name: INGRESSKIT_API_KEYS
          valueFrom:
            secretKeyRef:
              name: ingresskit-secrets
              key: api-keys
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: ingresskit-service
spec:
  selector:
    app: ingresskit
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check systemd status
sudo systemctl status ingresskit

# Check logs
sudo journalctl -u ingresskit -f

# Common causes:
# - Missing environment variables
# - Port already in use
# - Permission issues
```

#### 2. High Memory Usage
```bash
# Monitor memory usage
ps aux | grep uvicorn
htop

# Solutions:
# - Reduce worker processes
# - Implement request size limits
# - Add memory limits in systemd
```

#### 3. Database Connection Issues
```bash
# Check file permissions
ls -la /opt/ingresskit/server/data/

# Fix permissions
sudo chown -R ingresskit:ingresskit /opt/ingresskit/server/data/
```

### Performance Monitoring

```bash
# Monitor API response times
curl -w "@curl-format.txt" -s -o /dev/null \
  -H "Authorization: Bearer test-key" \
  http://localhost:8080/v1/billing/balance

# curl-format.txt content:
#      time_namelookup:  %{time_namelookup}\n
#         time_connect:  %{time_connect}\n
#      time_appconnect:  %{time_appconnect}\n
#     time_pretransfer:  %{time_pretransfer}\n
#        time_redirect:  %{time_redirect}\n
#   time_starttransfer:  %{time_starttransfer}\n
#                     ----------\n
#           time_total:  %{time_total}\n
```

---

*This deployment guide covers most production scenarios. For specific cloud providers or advanced configurations, refer to their respective documentation and adapt these instructions accordingly.*
