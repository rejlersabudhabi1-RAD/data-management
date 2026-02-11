# Deployment Guide - Data Management Service

## 🎯 Pre-Deployment Checklist

### Required Resources
- [ ] PostgreSQL database (14+)
- [ ] AWS S3 bucket configured
- [ ] JWT secret key (shared with User-Management service)
- [ ] Domain name (for production)
- [ ] SSL certificate (for HTTPS)

### Environment Setup
- [ ] All environment variables configured
- [ ] Database connection verified
- [ ] S3 bucket access verified
- [ ] JWT validation working

---

## 🚀 Railway Deployment

### Step 1: Prepare Repository

1. **Ensure all files are committed:**
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push
   ```

### Step 2: Create Railway Project

1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

### Step 3: Configure Environment Variables

Add these in Railway dashboard:

```bash
# Django
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app

# Database (Railway PostgreSQL)
DB_NAME=${{Postgres.PGDATABASE}}
DB_USER=${{Postgres.PGUSER}}
DB_PASSWORD=${{Postgres.PGPASSWORD}}
DB_HOST=${{Postgres.PGHOST}}
DB_PORT=${{Postgres.PGPORT}}

# AWS S3
USE_S3=True
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# JWT
JWT_SECRET_KEY=shared-secret-with-user-management
JWT_ALGORITHM=HS256
JWT_ISSUER=user-management-service
JWT_AUDIENCE=radai-platform

# CORS
CORS_ALLOWED_ORIGINS=https://your-frontend.com,https://your-backend.com
```

### Step 4: Add PostgreSQL Service

1. In Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will auto-create and link the database

### Step 5: Deploy

Railway will automatically:
- Detect Django project
- Install dependencies from `requirements.txt`
- Run migrations (via `Procfile`)
- Start the server with Gunicorn

### Step 6: Verify Deployment

```bash
# Check health
curl https://your-app.railway.app/health/

# Expected response
{"status":"healthy","service":"data-management-service","version":"1.0.0"}
```

---

## 🐳 Docker Deployment

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations and start server
CMD python manage.py migrate && \
    gunicorn config.wsgi:application --config gunicorn_config.py
```

### Create docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: data_management
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  web:
    build: .
    command: gunicorn config.wsgi:application --config gunicorn_config.py
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

volumes:
  postgres_data:
```

### Deploy with Docker

```bash
# Build and run
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Check logs
docker-compose logs -f web
```

---

## ☁️ AWS Deployment (EC2 + RDS)

### Step 1: Set Up RDS PostgreSQL

1. Create RDS PostgreSQL instance
2. Configure security group (allow port 5432)
3. Note connection details

### Step 2: Set Up S3 Bucket

1. Create S3 bucket
2. Create IAM user with S3 access
3. Configure bucket CORS policy:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": ["ETag"]
  }
]
```

### Step 3: Launch EC2 Instance

```bash
# Connect to EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.11 python3-pip python3-venv postgresql-client nginx -y

# Create app directory
sudo mkdir -p /var/www/data-management
sudo chown ubuntu:ubuntu /var/www/data-management
cd /var/www/data-management

# Clone repository
git clone your-repo.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Configure environment
cp .env.example .env
nano .env  # Edit with production values

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser
```

### Step 4: Configure Gunicorn Service

Create `/etc/systemd/system/data-management.service`:

```ini
[Unit]
Description=Data Management Service
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/data-management
Environment="PATH=/var/www/data-management/venv/bin"
ExecStart=/var/www/data-management/venv/bin/gunicorn \
          --config /var/www/data-management/gunicorn_config.py \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl start data-management
sudo systemctl enable data-management
sudo systemctl status data-management
```

### Step 5: Configure Nginx

Create `/etc/nginx/sites-available/data-management`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/data-management/staticfiles/;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/data-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## 🔄 CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python manage.py test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        uses: berviantoleo/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: data-management-service
```

---

## 📊 Post-Deployment

### Health Check

```bash
curl https://your-domain.com/health/
```

### Create Admin User

```bash
# Railway
railway run python manage.py createsuperuser

# Docker
docker-compose exec web python manage.py createsuperuser

# EC2
cd /var/www/data-management
source venv/bin/activate
python manage.py createsuperuser
```

### Test API Endpoints

```bash
# Get JWT token from User-Management service
TOKEN="your-jwt-token"

# Test document upload
curl -X POST https://your-domain.com/api/documents/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.pdf" \
  -F "document_type=report" \
  -F "owner_service=engineering"

# Test dataset creation
curl -X POST https://your-domain.com/api/datasets/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Dataset",
    "dataset_type": "training",
    "domain": "ai",
    "source_service": "test",
    "data": [{"x": 1, "y": 2}]
  }'
```

---

## 🔍 Monitoring

### Application Logs

```bash
# Railway
railway logs

# Docker
docker-compose logs -f web

# EC2
sudo journalctl -u data-management -f
```

### Database Monitoring

```bash
# Check database size
SELECT pg_size_pretty(pg_database_size('data_management'));

# Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

### Performance Monitoring

- Use Railway's built-in metrics
- Set up AWS CloudWatch (for EC2)
- Configure Sentry for error tracking
- Use PostgreSQL slow query log

---

## 🔐 Security Hardening

### Production Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] HTTPS enabled (SSL certificate)
- [ ] Database connection encrypted
- [ ] S3 bucket ACL properly configured
- [ ] CORS origins restricted
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] Database backups automated
- [ ] Monitoring and alerting set up

### Backup Strategy

```bash
# Automated database backup (cron)
0 2 * * * pg_dump -U postgres data_management > /backups/db_$(date +\%Y\%m\%d).sql

# S3 backup policy
Enable versioning on S3 bucket
Configure lifecycle rules for old versions
```

---

## 🚨 Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# Check migrations
python manage.py showmigrations
python manage.py migrate --fake-initial
```

### S3 Upload Issues

```bash
# Test AWS credentials
aws s3 ls s3://your-bucket-name --profile your-profile

# Check IAM permissions
# Ensure user has: s3:PutObject, s3:GetObject, s3:DeleteObject
```

### JWT Validation Issues

```bash
# Verify JWT secret matches User-Management service
# Check JWT_ISSUER and JWT_AUDIENCE settings
# Test token decoding manually
```

---

## 📞 Support

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Test database and S3 connectivity
4. Review audit logs for errors

---

**Deployment Complete! 🎉**
