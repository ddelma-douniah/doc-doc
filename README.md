# doc-doc 📁

A modern, secure document management system built with Django, inspired by Nextcloud and Notion's design philosophy.

## ✨ Features

- 📤 **File Upload & Management** - Upload, organize, and manage your documents
- 📂 **Folder Hierarchy** - Create nested folders for perfect organization
- 🔗 **Secure Sharing** - Generate shareable links for files and folders
- 🔐 **OAuth2 Authentication** - Sign in with Google or GitHub
- 📧 **Email Integration** - Password reset and notifications
- 🎨 **Modern UI** - Clean, Notion-inspired interface built with Tailwind CSS
- 🚀 **S3/MinIO Storage** - Scalable file storage
- 🐳 **Docker Ready** - One-command deployment

## 🛠 Tech Stack

- **Backend**: Django 6.0 + HTMX + Uvicorn (ASGI)
- **Database**: PostgreSQL 16
- **Storage**: MinIO (S3-compatible)
- **Frontend**: Django Templates + Tailwind CSS v4 + PostCSS
- **Static Files**: WhiteNoise (production-ready)
- **Authentication**: Django Allauth + OAuth2
- **Deployment**: Docker (Multi-Stage Build) + Docker Compose

## 📋 Prerequisites

### For Production Deployment
- Docker & Docker Compose
- A VPS or server with ports 8080, 9090, 9091 available
- Domain name configured (e.g., doc-doc.douniah.com)

### For Local Development
- Python 3.13+
- Node.js 22+ (for Tailwind CSS compilation)
- PostgreSQL 16 (or use Docker for database only)
- Make (optional, for convenience commands)

## 🚀 Quick Start

Choose your deployment method:
- **[Production with Docker](#production-deployment)** (Recommended for servers)
- **[Local Development](#local-development)** (For development)

---

## 🐳 Production Deployment

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd doc-doc
```

### 2. Create Environment File

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-here-change-this-in-production
ALLOWED_HOSTS=doc-doc.douniah.com,localhost,127.0.0.1

# Database Configuration
POSTGRES_DB=doc_doc
POSTGRES_USER=doc_doc_user
POSTGRES_PASSWORD=your-strong-password-here
POSTGRES_HOST=db
POSTGRES_PORT=5432

# MinIO / S3 Configuration
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=doc-doc
AWS_S3_ENDPOINT_URL=http://minio:9090

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=doc-doc <noreply@douniah.com>

# OAuth2 Configuration (Optional)
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
GITHUB_OAUTH_CLIENT_ID=your-github-client-id
GITHUB_OAUTH_CLIENT_SECRET=your-github-client-secret

# Application URLs
SITE_URL=https://doc-doc.douniah.com

# Ports (non-standard to avoid conflicts)
WEB_PORT=8080
MINIO_API_PORT=9090
MINIO_CONSOLE_PORT=9091
```

### 3. Create Docker Network

Create the external proxy network (if not already exists):

```bash
docker network create proxy
```

### 4. Deploy with Docker Compose

```bash
docker compose up -d --build
```

This command will:
- Build the Docker image
- Start PostgreSQL database
- Start MinIO for S3 storage
- Run database migrations
- Collect static files
- Start the application with Gunicorn

### 5. Create Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 6. Access the Application

- **Main App**: http://doc-doc.douniah.com:8080 (or your configured domain)
- **MinIO Console**: http://your-server:9091
- **Admin Panel**: http://doc-doc.douniah.com:8080/admin

---

## 💻 Local Development

For detailed development instructions, see [DEVELOPMENT.md](DEVELOPMENT.md).

### Quick Setup with Makefile

If you have `make` installed, you can use convenient shortcuts:

```bash
# Install all dependencies (Python + Node.js)
make install

# Setup database
make migrate

# Create admin user
make superuser

# Compile Tailwind CSS
make css-build

# Start development server (in one terminal)
make dev

# Watch Tailwind CSS changes (in another terminal)
make css-dev
```

### Manual Setup

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Node.js dependencies (for Tailwind CSS)
cd theme/static_src
npm install
cd ../..

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings (DEBUG=True for development)

# 5. Run migrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Compile Tailwind CSS
cd theme/static_src
npm run build  # One-time build
# OR
npm run dev    # Watch mode (auto-recompile on changes)
cd ../..

# 8. Collect static files
python manage.py collectstatic --noinput

# 9. Run development server
python manage.py runserver
```

### Available Make Commands

```bash
make help              # Show all available commands
make install           # Install all dependencies
make dev               # Start Django dev server
make css-dev           # Start Tailwind watcher
make css-build         # Build production CSS
make migrate           # Run migrations
make superuser         # Create superuser
make test              # Run tests
make docker-up         # Start Docker services
make docker-logs       # View Docker logs
```

For a complete list, run `make help`.

## 🔧 Configuration

### Nginx Proxy Manager Configuration

This application uses **WhiteNoise** to serve static files efficiently. No special Nginx configuration is needed for static files.

**In Nginx Proxy Manager:**

**Details Tab:**
- Domain: `doc-doc.douniah.com`
- Scheme: `http`
- Forward Hostname: `web` (or container IP)
- Forward Port: `8080`
- ✅ Cache Assets
- ✅ Block Common Exploits
- ✅ Websockets Support

**SSL Tab:**
- ✅ Force SSL
- ✅ HTTP/2 Support
- ✅ HSTS Enabled

**Advanced Tab:**
```nginx
# Proxy headers for Django
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;

# Max upload size (matches Django FILE_UPLOAD_MAX_MEMORY_SIZE)
client_max_body_size 10M;

# Timeouts
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```

**Note:** No `location /static/` block needed - WhiteNoise handles it!

### OAuth2 Setup

#### Google OAuth2

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `https://doc-doc.douniah.com/accounts/google/login/callback/`
6. Add Client ID and Secret to `.env`

#### GitHub OAuth2

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Create new OAuth App
3. Authorization callback URL: `https://doc-doc.douniah.com/accounts/github/login/callback/`
4. Add Client ID and Secret to `.env`

### Email Configuration

For Gmail:
1. Enable 2-Factor Authentication
2. Generate an App Password
3. Use the app password in `EMAIL_HOST_PASSWORD`

## 📁 Project Structure

```
doc-doc/
├── doc_doc/
│   ├── core/           # Main application
│   │   ├── models.py   # Database models
│   │   ├── views.py    # Views (Class-based)
│   │   └── ...
│   ├── settings.py     # Django settings
│   └── urls.py         # URL configuration
├── templates/          # HTML templates
│   ├── account/        # Authentication pages
│   ├── base.html       # Base template
│   ├── dashboard.html  # Main dashboard
│   └── ...
├── theme/              # Tailwind CSS configuration
├── docker-compose.yml  # Docker Compose configuration
├── Dockerfile          # Docker image definition
├── entrypoint.sh       # Container entrypoint script
├── requirements.txt    # Python dependencies
└── .env               # Environment variables
```

## 🔒 Security Checklist

Before going to production:

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Set `DEBUG=False`
- [ ] Use strong passwords for database
- [ ] Configure SSL/TLS (HTTPS)
- [ ] Set up regular backups
- [ ] Configure firewall rules
- [ ] Review `ALLOWED_HOSTS`
- [ ] Set up monitoring and logging
- [ ] Configure email for error notifications
- [ ] Enable CSRF protection (already configured)
- [ ] Use secure cookies (already configured for production)

## 📦 Maintenance

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web
docker compose logs -f db
docker compose logs -f minio
```

### Backup Database

```bash
docker compose exec db pg_dump -U doc_doc_user doc_doc > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
docker compose exec -T db psql -U doc_doc_user doc_doc < backup_20250101.sql
```

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose up -d --build

# Run migrations if needed
docker compose exec web python manage.py migrate
```

### Collect Static Files

```bash
docker compose exec web python manage.py collectstatic --noinput
```

## 🐛 Troubleshooting

### Port Already in Use

If ports 8080, 9090, or 9091 are already in use, update them in `.env`:

```env
WEB_PORT=8081
MINIO_API_PORT=9092
MINIO_CONSOLE_PORT=9093
```

### Static Files Not Loading

```bash
# Manually collect static files
docker compose exec web python manage.py collectstatic --noinput --clear

# Check permissions
docker compose exec web ls -la /app/staticfiles
```

### Database Connection Issues

```bash
# Check if database is running
docker compose ps db

# Check database logs
docker compose logs db

# Test connection
docker compose exec web python manage.py dbshell
```

### MinIO Issues

```bash
# Check MinIO logs
docker compose logs minio

# Access MinIO console
http://your-server:9091

# Credentials: minioadmin / minioadmin (change in production!)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review logs: `docker compose logs -f web`

## 🎯 Roadmap

- [ ] Drag & drop file upload
- [ ] File preview functionality
- [ ] Advanced search
- [ ] User quotas and storage limits
- [ ] Version control for files
- [ ] Trash/Recycle bin
- [ ] File tags and labels
- [ ] Advanced sharing permissions
- [ ] API endpoints
- [ ] Mobile app

---

Made with ❤️ using Django, HTMX, and Tailwind CSS
