# Quick Start Guide - doc-doc

## 🚀 Get Running in 5 Minutes

### Prerequisites
- Docker & Docker Compose installed
- `.env` file configured

---

## Step 1: Generate SECRET_KEY (30 seconds)

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copy the output and paste it into your `.env` file:

```bash
SECRET_KEY=<paste-the-generated-key-here>
```

---

## Step 2: Start the Application (2 minutes)

```bash
# Build and start all services
docker compose up --build -d

# Follow logs
docker compose logs -f web
```

Wait for: **"Application startup complete"**

---

## Step 3: Create Admin Account (1 minute)

```bash
docker compose exec web python manage.py createsuperuser
```

Follow the prompts:
- Username: `admin` (or your choice)
- Email: your-email@example.com
- Password: (enter a strong password)

---

## Step 4: Access the Application (1 minute)

Open your browser:

- **Main App:** http://localhost:8080
- **Admin Panel:** http://localhost:8080/admin
- **MinIO Console:** http://localhost:9091 (minioadmin / minioadmin)

---

## Step 5: Test Everything (1 minute)

Run the test suite:

```bash
docker compose exec web python manage.py test
```

Expected output: **OK** with all tests passing ✅

---

## 🎉 You're Done!

Your doc-doc instance is now running with:
- ✅ Secure authentication
- ✅ File upload validation
- ✅ Password-protected sharing
- ✅ Admin interface
- ✅ All security fixes applied

---

## Common Commands

```bash
# View logs
docker compose logs -f web

# Stop services
docker compose down

# Restart services
docker compose restart

# Access Django shell
docker compose exec web python manage.py shell

# Run migrations
docker compose exec web python manage.py migrate

# Collect static files
docker compose exec web python manage.py collectstatic --noinput

# Create another user
docker compose exec web python manage.py createsuperuser

# Run security checks
docker compose exec web python manage.py check --deploy
```

---

## Troubleshooting

### Issue: "SECRET_KEY environment variable is required"
**Fix:** Make sure you've set `SECRET_KEY` in your `.env` file (see Step 1)

### Issue: "SocialApp.DoesNotExist at /accounts/login/"
**Fix:** The app will auto-fix on startup. If not:
```bash
docker compose exec web python manage.py init_socialapps
docker compose restart web
```

### Issue: Can't upload files
**Check:**
1. File size < 10MB ✓
2. File extension not forbidden (.exe, .bat, etc.) ✓
3. MinIO is running: `docker compose ps minio` ✓

### Issue: Static files not loading
**Fix:**
```bash
docker compose exec web python manage.py collectstatic --noinput --clear
docker compose restart web
```

---

## Default Credentials

### Application
- Create your own via `docker compose exec web python manage.py createsuperuser`

### MinIO Console
- Username: `minioadmin`
- Password: `minioadmin`
- URL: http://localhost:9091

⚠️ **Change these in production!** Edit `.env`:
```bash
AWS_ACCESS_KEY_ID=your-secure-key
AWS_SECRET_ACCESS_KEY=your-secure-secret
```

---

## Production Deployment

For production deployment, see **DEPLOYMENT.md**

Key changes needed:
1. Set `DEBUG=False` in `.env`
2. Change database password
3. Change MinIO credentials
4. Configure email backend (SMTP)
5. Set up SSL/HTTPS
6. Configure domain in `ALLOWED_HOSTS`

---

## Next Steps

1. ✅ Create your admin account (Step 3)
2. ✅ Log in at http://localhost:8080/admin
3. ✅ Create some folders and upload files
4. ✅ Try creating a share link
5. ✅ Test password-protected shares
6. 📖 Read `SECURITY_FIXES.md` to understand what's been fixed
7. 📖 Read `DEPLOYMENT.md` for production deployment

---

## Support

**Documentation:**
- `SECURITY_FIXES.md` - What security issues were fixed
- `DEPLOYMENT.md` - Complete deployment guide
- `CHANGES_SUMMARY.md` - All changes made

**Need Help?**
```bash
# Check application health
docker compose ps

# View all logs
docker compose logs

# Run Django checks
docker compose exec web python manage.py check --deploy
```

---

## Features Overview

### ✅ Secure Authentication
- Username or email login
- Mandatory email verification
- Rate limiting (5 attempts per 5 minutes)
- OAuth2 support (Google, GitHub)

### ✅ File Management
- Folder hierarchy
- 10MB file size limit
- File type validation
- Malware prevention
- S3/MinIO storage

### ✅ Sharing
- Share links for files and folders
- Password protection (hashed)
- Expiration dates
- Access tracking
- User-specific shares

### ✅ Admin Interface
- Manage all folders, files, shares
- View statistics
- User management
- Full control panel

### ✅ Security
- CSRF protection
- XSS prevention
- File validation
- Rate limiting
- Security headers
- Private file storage

---

**That's it! You're ready to use doc-doc.** 🎉
