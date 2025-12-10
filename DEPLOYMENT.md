# Deployment Guide - doc-doc

Complete guide for deploying the doc-doc document management system.

## Prerequisites

- Docker & Docker Compose installed
- Domain name configured (or use localhost for testing)
- SSL certificate (recommended for production)

## Quick Start (Development)

```bash
# 1. Clone repository
git clone <repository-url>
cd doc-doc

# 2. Copy environment file
cp .env.example .env

# 3. Generate SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# 4. Update .env file with the generated SECRET_KEY
# Edit .env and replace GENERATE_YOUR_OWN_SECRET_KEY_HERE

# 5. Build and start containers
docker compose up --build -d

# 6. Create superuser
docker compose exec web python manage.py createsuperuser

# 7. Access application
# Web: http://localhost:8080
# Admin: http://localhost:8080/admin/
# MinIO Console: http://localhost:9091
```

## Production Deployment

### Step 1: Environment Configuration

Edit `.env` file with production values:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=<your-generated-secret-key>
ALLOWED_HOSTS=douniah.com,www.douniah.com,doc-doc.douniah.com

# Database Configuration
POSTGRES_DB=doc_doc
POSTGRES_USER=doc_doc_user
POSTGRES_PASSWORD=<strong-random-password>
POSTGRES_HOST=db
POSTGRES_PORT=5432

# MinIO / S3 Configuration
AWS_ACCESS_KEY_ID=<strong-random-key>
AWS_SECRET_ACCESS_KEY=<strong-random-secret>
AWS_STORAGE_BUCKET_NAME=doc-doc
AWS_S3_ENDPOINT_URL=http://minio:9090

# Email Configuration (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@douniah.com
SERVER_EMAIL=server@douniah.com

# OAuth2 Configuration (Optional)
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
GITHUB_OAUTH_CLIENT_ID=your-github-client-id
GITHUB_OAUTH_CLIENT_SECRET=your-github-client-secret

# Application URLs
SITE_URL=https://doc-doc.douniah.com

# Ports
WEB_PORT=8080
MINIO_API_PORT=9090
MINIO_CONSOLE_PORT=9091
```

### Step 2: Security Checklist

- [ ] `DEBUG=False`
- [ ] Strong `SECRET_KEY` generated and set
- [ ] Strong database password
- [ ] Strong MinIO credentials
- [ ] Email backend configured (not console)
- [ ] `ALLOWED_HOSTS` contains your domain
- [ ] `SITE_URL` is HTTPS
- [ ] SSL/TLS certificate configured on reverse proxy

### Step 3: Build and Deploy

```bash
# Stop any running containers
docker compose down

# Build with no cache
docker compose build --no-cache

# Start in production mode
docker compose up -d

# Check logs
docker compose logs -f web
```

### Step 4: Initialize Application

```bash
# Create superuser account
docker compose exec web python manage.py createsuperuser

# Verify migrations
docker compose exec web python manage.py showmigrations

# Run tests (optional but recommended)
docker compose exec web python manage.py test
```

### Step 5: Configure Reverse Proxy

#### Nginx Configuration Example

```nginx
upstream doc_doc {
    server localhost:8080;
}

server {
    listen 80;
    server_name douniah.com www.douniah.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name douniah.com www.douniah.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Max upload size (match Django settings)
    client_max_body_size 10M;

    location / {
        proxy_pass http://doc_doc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/douniah/doc-doc/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        # Media files served through Django/S3, not directly
        proxy_pass http://doc_doc;
    }
}
```

## OAuth Setup

### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `https://douniah.com/accounts/google/login/callback/`
5. Copy Client ID and Client Secret to `.env`
6. Restart containers

### GitHub OAuth

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Register new OAuth application:
   - Homepage URL: `https://douniah.com`
   - Authorization callback URL: `https://douniah.com/accounts/github/login/callback/`
3. Copy Client ID and Client Secret to `.env`
4. Restart containers

## Monitoring & Maintenance

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web
docker compose logs -f db
docker compose logs -f minio

# Application logs (inside container)
docker compose exec web tail -f /app/logs/django.log
```

### Database Backups

```bash
# Create backup
docker compose exec db pg_dump -U doc_doc_user doc_doc > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker compose exec -T db psql -U doc_doc_user doc_doc < backup_20240101_120000.sql
```

### File Storage Backups

```bash
# Backup MinIO data
docker compose exec minio mc mirror /data /backup/minio_data

# Or use Docker volume backup
docker run --rm \
  -v doc-doc_minio_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/minio_backup_$(date +%Y%m%d).tar.gz -C /data .
```

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker compose down
docker compose build --no-cache
docker compose up -d

# Run migrations
docker compose exec web python manage.py migrate

# Collect static files
docker compose exec web python manage.py collectstatic --noinput
```

### Health Checks

```bash
# Check service status
docker compose ps

# Test database connection
docker compose exec web python manage.py dbshell

# Run Django checks
docker compose exec web python manage.py check --deploy

# Test email configuration
docker compose exec web python manage.py sendtestemail your-email@example.com
```

## Troubleshooting

### Issue: Login page shows SocialApp.DoesNotExist

**Solution:**

```bash
# Run the initialization command manually
docker compose exec web python manage.py init_socialapps

# Or restart containers (entrypoint.sh runs it automatically)
docker compose restart web
```

### Issue: Permission denied on logs

**Solution:**

```bash
# Create logs directory with proper permissions
docker compose exec web mkdir -p /app/logs
docker compose exec web chmod 755 /app/logs
```

### Issue: File uploads fail

**Causes:**

1. File too large (>10MB)
2. Forbidden file extension (.exe, .bat, etc.)
3. MinIO not accessible

**Solution:**

```bash
# Check MinIO status
docker compose ps minio

# Test MinIO connection
docker compose exec web python manage.py shell
>>> from django.core.files.storage import default_storage
>>> default_storage.exists('test')

# Check file validation settings in settings.py
```

### Issue: Static files not loading

**Solution:**

```bash
# Collect static files
docker compose exec web python manage.py collectstatic --noinput --clear

# Verify volume mount
docker compose exec web ls -la /app/staticfiles
```

### Issue: Database connection errors

**Solution:**

```bash
# Check database status
docker compose ps db

# View database logs
docker compose logs db

# Test connection
docker compose exec web python manage.py dbshell

# Reset database (WARNING: destroys data)
docker compose down -v
docker compose up -d
docker compose exec web python manage.py migrate
```

## Performance Optimization

### Enable Redis Caching

Add to `docker-compose.yml`:

```yaml
redis:
  image: redis:7-alpine
  restart: unless-stopped
```

Add to `.env`:

```bash
REDIS_URL=redis://redis:6379/0
```

Add to `settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
    }
}
```

### Database Connection Pooling

Add to `settings.py`:

```python
DATABASES = {
    'default': {
        # ... existing config ...
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        }
    }
}
```

### Enable Compression

Add to Nginx configuration:

```nginx
gzip on;
gzip_types text/css text/javascript application/javascript application/json;
gzip_min_length 1000;
```

## Security Best Practices

1. **Regular Updates**: Keep Docker images and Python packages up to date
2. **Backups**: Automate daily backups of database and file storage
3. **Monitoring**: Set up uptime monitoring and error tracking (Sentry)
4. **Firewall**: Only expose necessary ports (80, 443)
5. **Rate Limiting**: Already configured in Django settings
6. **SSL/TLS**: Use Let's Encrypt for free SSL certificates
7. **Password Policy**: Enforce strong passwords via Django settings
8. **Two-Factor Auth**: Consider adding django-two-factor-auth
9. **Audit Logging**: Review access logs regularly
10. **Security Scans**: Run regular security audits

## Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Let's Encrypt](https://letsencrypt.org/)

## Support

For issues or questions:

1. Check logs: `docker compose logs -f`
2. Review `SECURITY_FIXES.md` for recent changes
3. Run tests: `docker compose exec web python manage.py test`
4. Check Django deployment checklist: `docker compose exec web python manage.py check --deploy`
