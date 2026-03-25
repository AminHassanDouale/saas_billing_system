# 🚀 Production Deployment Guide

Complete guide for deploying the SaaS Billing System to production.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Application Deployment](#application-deployment)
5. [Security Hardening](#security-hardening)
6. [Monitoring & Logging](#monitoring--logging)
7. [Backup & Recovery](#backup--recovery)
8. [Performance Optimization](#performance-optimization)

---

## Pre-Deployment Checklist

### ✅ Required Accounts & Services

- [ ] D-Money merchant account with API credentials
- [ ] Domain name registered
- [ ] SSL certificate (Let's Encrypt recommended)
- [ ] Cloud hosting account (AWS, Azure, DigitalOcean, etc.)
- [ ] Email service (SendGrid, Mailgun, or SMTP)
- [ ] Redis instance (for caching and Celery)
- [ ] MySQL database (managed or self-hosted)

### ✅ Configuration

- [ ] All `.env` variables configured
- [ ] Strong `SECRET_KEY` generated (32+ characters)
- [ ] D-Money credentials configured
- [ ] SMTP email settings configured
- [ ] SSL certificates installed
- [ ] CORS origins configured
- [ ] Webhook URLs configured in D-Money dashboard

### ✅ Security

- [ ] Database firewall rules configured
- [ ] Application firewall enabled
- [ ] Rate limiting configured
- [ ] API authentication enabled
- [ ] Webhook signature verification enabled
- [ ] HTTPS enforced
- [ ] Security headers configured

---

## Environment Setup

### 1. Server Requirements

**Minimum (Single Server):**
- 2 CPU cores
- 4 GB RAM
- 50 GB SSD storage
- Ubuntu 22.04 LTS or later

**Recommended (Production):**
- 4+ CPU cores
- 8+ GB RAM
- 100+ GB SSD storage
- Load balancer
- Separate database server
- CDN for static assets

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install other tools
sudo apt install -y git nginx certbot python3-certbot-nginx
```

### 3. Clone Repository

```bash
cd /opt
sudo git clone https://github.com/yourusername/saas-billing-system.git
cd saas-billing-system
```

---

## Database Setup

### Option 1: Managed Database (Recommended)

Use a managed MySQL service like:
- AWS RDS
- Google Cloud SQL
- DigitalOcean Managed Databases
- Azure Database for MySQL

**Advantages:**
- Automated backups
- High availability
- Automated updates
- Monitoring included

### Option 2: Self-Hosted MySQL

```bash
# Using Docker
docker run -d \
  --name mysql-production \
  --restart unless-stopped \
  -e MYSQL_ROOT_PASSWORD=STRONG_PASSWORD_HERE \
  -e MYSQL_DATABASE=saas_billing \
  -v /opt/mysql-data:/var/lib/mysql \
  -p 3306:3306 \
  mysql:8.0

# Create database
mysql -u root -p -e "CREATE DATABASE saas_billing CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### Database Configuration

```bash
# Configure MySQL for production
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

Add/modify:
```ini
[mysqld]
max_connections = 200
innodb_buffer_pool_size = 2G
innodb_log_file_size = 512M
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2
```

---

## Application Deployment

### 1. Configure Environment

```bash
cp .env.example .env
nano .env
```

**Critical Settings:**
```bash
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<GENERATE_STRONG_KEY_HERE>

# Database
DATABASE_URL=mysql+pymysql://user:password@db-host:3306/saas_billing

# D-Money
DMONEY_BASE_URL=https://pg.d-moneyservice.dj
DMONEY_NOTIFY_URL=https://yourdomain.com/api/v1/webhooks/dmoney
DMONEY_REDIRECT_URL=https://yourdomain.com/payment/success

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ENABLE_EMAIL_NOTIFICATIONS=True

# Security
ENABLE_WEBHOOKS=True
WEBHOOK_SECRET=<GENERATE_STRONG_KEY_HERE>
RATE_LIMIT_PER_MINUTE=60
```

### 2. Generate Secret Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate WEBHOOK_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Deploy with Docker Compose

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec app alembic upgrade head

# Seed initial data (optional)
docker-compose exec app python scripts/seed_data.py
```

### 4. Configure Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/saas-billing
```

```nginx
upstream saas_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logging
    access_log /var/log/nginx/saas-billing-access.log;
    error_log /var/log/nginx/saas-billing-error.log;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    location / {
        proxy_pass http://saas_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Webhook endpoint (higher timeout)
    location /api/v1/webhooks/ {
        proxy_pass http://saas_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/saas-billing /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Setup SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
# Enable UFW
sudo ufw enable

# Allow essential services
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# Restrict MySQL access (if self-hosted)
sudo ufw allow from your_app_server_ip to any port 3306
```

### 2. Application Security

Update `.env`:
```bash
# Disable debug mode
DEBUG=False

# Enable security features
ENABLE_WEBHOOKS=True
WEBHOOK_SECRET=strong_secret_here
RATE_LIMIT_PER_MINUTE=60
MAX_LOGIN_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=30
```

### 3. Database Security

```bash
# Create dedicated database user
mysql -u root -p

CREATE USER 'saas_app'@'%' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON saas_billing.* TO 'saas_app'@'%';
FLUSH PRIVILEGES;
```

---

## Monitoring & Logging

### 1. Application Logs

```bash
# View application logs
docker-compose logs -f app

# View specific service
docker-compose logs -f celery-worker

# View all logs
tail -f logs/*.log
```

### 2. Setup Log Rotation

```bash
sudo nano /etc/logrotate.d/saas-billing
```

```
/opt/saas-billing-system/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        docker-compose restart app
    endscript
}
```

### 3. Monitoring Tools (Recommended)

- **Sentry** - Error tracking
- **Grafana** - Metrics visualization
- **Prometheus** - Metrics collection
- **Uptime Robot** - Uptime monitoring

---

## Backup & Recovery

### 1. Database Backups

```bash
# Automated daily backups
sudo nano /etc/cron.daily/mysql-backup
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/mysql"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

mysqldump -u root -p'password' saas_billing | gzip > $BACKUP_DIR/saas_billing_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

```bash
sudo chmod +x /etc/cron.daily/mysql-backup
```

### 2. Application Backup

```bash
# Backup uploaded files and logs
tar -czf /opt/backups/app_$(date +%Y%m%d).tar.gz \
    /opt/saas-billing-system/logs \
    /opt/saas-billing-system/.env
```

---

## Performance Optimization

### 1. Database Optimization

```bash
# Add indexes for frequently queried columns
ALTER TABLE transactions ADD INDEX idx_user_created (user_id, created_at);
ALTER TABLE subscriptions ADD INDEX idx_user_status (user_id, status);
```

### 2. Application Optimization

- Enable Redis caching
- Use connection pooling
- Configure Gunicorn workers: `workers = (2 * CPU_cores) + 1`

### 3. CDN Configuration

Use CloudFlare or similar for:
- Static asset caching
- DDoS protection
- SSL/TLS encryption

---

## Health Checks

```bash
# Application health
curl https://yourdomain.com/health

# Database connection
mysql -h your-db-host -u saas_app -p -e "SELECT 1"

# Redis connection
redis-cli -h your-redis-host ping
```

---

## Troubleshooting

### Application Won't Start

1. Check logs: `docker-compose logs app`
2. Verify environment variables
3. Check database connectivity
4. Ensure migrations are applied

### Database Connection Issues

1. Verify credentials in `.env`
2. Check firewall rules
3. Test connection: `mysql -h host -u user -p`

### Webhook Not Working

1. Verify webhook URL in D-Money dashboard
2. Check webhook secret
3. Review webhook logs: `tail -f logs/app.log | grep webhook`

---

## Post-Deployment

1. **Test Payment Flow**
   - Create test subscription
   - Process test payment
   - Verify webhook reception

2. **Monitor Performance**
   - Check response times
   - Monitor error rates
   - Review logs regularly

3. **Setup Alerts**
   - Configure uptime monitoring
   - Set up error notifications
   - Monitor disk usage

---

**🎉 Your SaaS Billing System is now deployed!**

For support, refer to the main README.md or API documentation.
