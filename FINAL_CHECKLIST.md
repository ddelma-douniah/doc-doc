# Final Deployment Checklist - doc-doc

Use this checklist before deploying to production.

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### Environment Configuration

- [ ] `.env` file exists and is properly configured
- [ ] `DEBUG=False` in .env
- [ ] `SECRET_KEY` is set and unique (not the example key)
- [ ] `ALLOWED_HOSTS` includes your domain
- [ ] `POSTGRES_PASSWORD` is changed from default
- [ ] `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are changed from `minioadmin`
- [ ] Email backend configured (not console backend)
- [ ] `SITE_URL` is set to your HTTPS domain
- [ ] OAuth credentials configured (if using Google/GitHub login)

### Database

- [ ] PostgreSQL is running: `docker compose ps db`
- [ ] Database health check passes
- [ ] Migrations are up to date: `docker compose exec web python manage.py showmigrations`
- [ ] No pending migrations
- [ ] Backup strategy in place

### File Storage

- [ ] MinIO/S3 is accessible
- [ ] Bucket created successfully
- [ ] Files are private (not public-read)
- [ ] Signed URLs working
- [ ] Backup strategy in place for uploaded files

### Security

- [ ] Django security check passes: `docker compose exec web python manage.py check --deploy`
- [ ] No security warnings in output
- [ ] SSL/TLS certificate configured on reverse proxy
- [ ] HTTPS redirect working
- [ ] Security headers present (HSTS, X-Content-Type-Options, etc.)
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] File upload validation active

### Application

- [ ] All tests pass: `docker compose exec web python manage.py test`
- [ ] Login page loads without errors
- [ ] Can create account with email verification
- [ ] Can log in successfully
- [ ] Can upload files (respects 10MB limit)
- [ ] Cannot upload forbidden file types (.exe, etc.)
- [ ] Share links work
- [ ] Password-protected shares prompt for password
- [ ] Admin interface accessible at /admin/
- [ ] Static files loading correctly
- [ ] Logs directory exists and is writable

### OAuth (if using)

- [ ] Google OAuth configured in Google Cloud Console
- [ ] GitHub OAuth configured in GitHub Developer Settings
- [ ] Redirect URLs match your domain
- [ ] SocialApp objects initialized: `docker compose exec web python manage.py init_socialapps`
- [ ] Can log in via OAuth providers

### Reverse Proxy (Nginx/Apache)

- [ ] SSL certificate installed
- [ ] HTTP redirects to HTTPS
- [ ] Proxy headers configured correctly
- [ ] `client_max_body_size` set to 10M or higher
- [ ] Static files served correctly
- [ ] Security headers added
- [ ] Logs configured

### Monitoring & Logging

- [ ] Application logs accessible: `docker compose logs web`
- [ ] Database logs accessible: `docker compose logs db`
- [ ] Log rotation configured
- [ ] Uptime monitoring set up (optional)
- [ ] Error tracking set up (Sentry, optional)

### Backups

- [ ] Database backup script created
- [ ] File storage backup strategy in place
- [ ] Backup restoration tested
- [ ] Automated backup schedule configured

### Performance

- [ ] Connection pooling enabled (optional)
- [ ] Redis caching configured (optional)
- [ ] Static file compression enabled
- [ ] CDN configured for static files (optional)

---

## 🧪 TESTING CHECKLIST

### Authentication & Authorization

- [ ] Can access login page without errors
- [ ] Can sign up (requires email verification)
- [ ] Can verify email (check email backend)
- [ ] Can log in with username
- [ ] Can log in with email
- [ ] Rate limiting kicks in after 5 failed attempts
- [ ] Can log out
- [ ] Cannot access dashboard when logged out
- [ ] Cannot access other users' files

### File Management

- [ ] Can create folder from dashboard
- [ ] Can create subfolder
- [ ] Can navigate into folders
- [ ] Can upload file to root
- [ ] Can upload file to folder
- [ ] File size limit enforced (try 15MB file)
- [ ] Forbidden extensions blocked (try .exe)
- [ ] Path traversal prevented (try ../../etc/passwd as filename)
- [ ] Can view uploaded files
- [ ] Can delete files
- [ ] Can delete folders

### Sharing

- [ ] Can create share link for file
- [ ] Can create share link for folder
- [ ] Share link works in incognito/private browser
- [ ] Can set share password
- [ ] Password prompt appears for protected shares
- [ ] Correct password grants access
- [ ] Wrong password shows error
- [ ] Can set expiration date
- [ ] Expired shares show error
- [ ] Can deactivate share
- [ ] Inactive shares show error
- [ ] Access count increments
- [ ] Can add specific users to share
- [ ] Only specified users can access (when set)

### Admin Interface

- [ ] Can access /admin/ with superuser account
- [ ] Can view Folders list
- [ ] Can edit Folder
- [ ] Can view Files list
- [ ] Can edit File
- [ ] Can view file size and MIME type
- [ ] Can view Shares list
- [ ] Can see password protection indicator
- [ ] Can see share URL
- [ ] Can see access count
- [ ] Can filter by date, owner, status
- [ ] Search works for folders, files, shares

### Security Tests

- [ ] CSRF token required on POST requests
- [ ] XSS attempts blocked (try `<script>alert(1)</script>` in folder name)
- [ ] SQL injection prevented (Django ORM handles this)
- [ ] Cannot access files without signed URLs
- [ ] S3 URLs contain signature parameters
- [ ] Session cookies have Secure flag (in production)
- [ ] Session cookies have HttpOnly flag
- [ ] Security headers present in response:
  - [ ] Strict-Transport-Security
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-Frame-Options: DENY

### Error Handling

- [ ] 404 pages display correctly
- [ ] 403 pages display correctly
- [ ] 500 errors don't leak sensitive info (with DEBUG=False)
- [ ] Expired shares show user-friendly error
- [ ] Inactive shares show user-friendly error
- [ ] Invalid share IDs show 404

---

## 🚀 DEPLOYMENT STEPS

### Step 1: Final Configuration Review

```bash
# Review all environment variables
cat .env

# Verify SECRET_KEY is set and unique
grep SECRET_KEY .env

# Verify DEBUG is False
grep DEBUG .env
```

### Step 2: Build and Deploy

```bash
# Stop existing containers
docker compose down

# Build fresh images
docker compose build --no-cache

# Start services
docker compose up -d

# Wait for startup
docker compose logs -f web
# Wait for "Application startup complete"
```

### Step 3: Database Setup

```bash
# Run migrations
docker compose exec web python manage.py migrate

# Initialize OAuth apps
docker compose exec web python manage.py init_socialapps

# Collect static files
docker compose exec web python manage.py collectstatic --noinput
```

### Step 4: Create Admin User

```bash
docker compose exec web python manage.py createsuperuser
```

### Step 5: Run Tests

```bash
# Run all tests
docker compose exec web python manage.py test

# Run security checks
docker compose exec web python manage.py check --deploy
```

### Step 6: Verify Application

```bash
# Check all services running
docker compose ps

# Verify health
curl -I https://yourdomain.com

# Check logs
docker compose logs web | grep ERROR
docker compose logs db | grep ERROR
```

### Step 7: Manual Testing

- [ ] Open https://yourdomain.com in browser
- [ ] Verify SSL certificate valid
- [ ] Login page loads
- [ ] Create test account
- [ ] Upload test file
- [ ] Create share link
- [ ] Test share in incognito mode
- [ ] Access admin panel
- [ ] Verify all CRUD operations

---

## 🎯 POST-DEPLOYMENT CHECKLIST

### Immediate Actions

- [ ] Create first backup
- [ ] Test backup restoration
- [ ] Document admin credentials securely
- [ ] Set up monitoring alerts
- [ ] Review logs for any errors
- [ ] Test email sending (password reset)

### Within 24 Hours

- [ ] Monitor error logs
- [ ] Check disk usage
- [ ] Verify backups running
- [ ] Test all major features with real users
- [ ] Review security scan results

### Within 1 Week

- [ ] Review access logs
- [ ] Check for any security warnings
- [ ] Update documentation with any changes
- [ ] Plan regular maintenance schedule
- [ ] Set up automated security updates

---

## 🔧 MAINTENANCE CHECKLIST

### Daily

- [ ] Check logs for errors
- [ ] Verify backups completed
- [ ] Monitor disk usage

### Weekly

- [ ] Review access logs
- [ ] Check for failed login attempts
- [ ] Review share access patterns
- [ ] Test backup restoration

### Monthly

- [ ] Update Docker images
- [ ] Update Python packages
- [ ] Run security audit
- [ ] Review user accounts
- [ ] Clean up old shares
- [ ] Optimize database

### Quarterly

- [ ] Review and update security policies
- [ ] Test disaster recovery plan
- [ ] Review and rotate credentials
- [ ] Performance optimization review

---

## ⚠️ ROLLBACK PLAN

If something goes wrong:

```bash
# Stop current deployment
docker compose down

# Restore previous version
git checkout previous-version-tag

# Rebuild
docker compose build

# Start services
docker compose up -d

# Restore database backup (if needed)
docker compose exec -T db psql -U doc_doc_user doc_doc < backup.sql

# Check status
docker compose ps
docker compose logs -f
```

---

## 📞 EMERGENCY CONTACTS

- [ ] Database admin contact documented
- [ ] System admin contact documented
- [ ] Security team contact documented
- [ ] Escalation procedure documented

---

## ✅ SIGN-OFF

### Pre-Deployment

- [ ] Configuration reviewed: ___________________ Date: __________
- [ ] Security audit passed: ___________________ Date: __________
- [ ] Tests passed: ___________________ Date: __________
- [ ] Backups configured: ___________________ Date: __________

### Deployment

- [ ] Deployed by: ___________________ Date/Time: __________
- [ ] Verification completed: ___________________ Date/Time: __________
- [ ] Stakeholders notified: ___________________ Date/Time: __________

### Post-Deployment

- [ ] 24-hour check: ___________________ Date/Time: __________
- [ ] 1-week review: ___________________ Date/Time: __________
- [ ] All issues resolved: ___________________ Date/Time: __________

---

## 📚 DOCUMENTATION REFERENCES

- **QUICK_START.md** - Quick setup guide
- **DEPLOYMENT.md** - Detailed deployment instructions
- **SECURITY_FIXES.md** - Security improvements details
- **CHANGES_SUMMARY.md** - Complete changes overview

---

**Deployment Status:** [ ] Ready [ ] In Progress [ ] Complete [ ] Issues Found

**Notes:**
_______________________________________________________________________
_______________________________________________________________________
_______________________________________________________________________

---

**Approved By:** ___________________ **Date:** __________
