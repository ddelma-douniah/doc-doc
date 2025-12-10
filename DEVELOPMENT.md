# Development Guide - doc-doc

This guide covers local development setup and best practices for the doc-doc project.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Tailwind CSS Development](#tailwind-css-development)
- [Docker Development](#docker-development)
- [Database Migrations](#database-migrations)
- [Testing](#testing)
- [Code Quality](#code-quality)

---

## Prerequisites

### Required Tools

- **Python 3.13+**
- **Node.js 22+** (LTS version)
- **Docker & Docker Compose** (for containerized development)
- **PostgreSQL 16** (if running without Docker)
- **Git**

### Verify Installation

```bash
python --version  # Should be 3.13+
node --version    # Should be v22+
npm --version     # Should be 10+
docker --version  # Should be 24+
docker compose version
```

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/doc-doc.git
cd doc-doc
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Node.js Dependencies (for Tailwind CSS)

```bash
cd theme/static_src
npm install
cd ../..
```

### 5. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and set:
# - DEBUG=True (for development)
# - SECRET_KEY=<generate-your-own>
# - Database credentials
# - Other settings as needed
```

To generate a SECRET_KEY:

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 6. Database Setup

#### Option A: Using Docker (Recommended)

```bash
# Start only the database service
docker compose up -d db

# Wait for database to be ready
sleep 5

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

#### Option B: Local PostgreSQL

1. Install PostgreSQL 16
2. Create database and user:

```sql
CREATE DATABASE doc_doc;
CREATE USER doc_doc_user WITH PASSWORD 'your_password';
ALTER ROLE doc_doc_user SET client_encoding TO 'utf8';
ALTER ROLE doc_doc_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE doc_doc_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE doc_doc TO doc_doc_user;
```

3. Update `.env` with your database credentials
4. Run migrations: `python manage.py migrate`

---

## Tailwind CSS Development

### Understanding the Setup

This project uses **Tailwind CSS v4** with PostCSS for styling. The setup follows industry best practices:

- **Source files**: `theme/static_src/src/styles.css`
- **Configuration**: `theme/static_src/postcss.config.js`
- **Output**: `theme/static/css/dist/styles.css` (auto-generated, **not in Git**)

### Development Workflow

#### Start Tailwind Watcher (Recommended for Active Development)

This watches your templates and automatically recompiles CSS when you make changes:

```bash
cd theme/static_src
npm run dev
```

Keep this running in a separate terminal while you develop. It will:
- Watch all `.html`, `.py`, and `.js` files
- Automatically detect new Tailwind classes
- Rebuild CSS instantly
- Enable hot-reload (if using with browser-sync)

#### One-Time Build

For a single compilation (useful for testing):

```bash
cd theme/static_src
npm run build
```

This creates an optimized, minified CSS file for production.

### Adding New Styles

1. **Use Tailwind utility classes** in your HTML templates:

```html
<div class="flex items-center justify-between p-4 bg-blue-600 rounded-lg">
    <h1 class="text-2xl font-bold text-white">Hello World</h1>
</div>
```

2. **Tailwind will automatically include** these classes in the compiled CSS
3. **No manual CSS writing needed** in 99% of cases

### Custom CSS (if needed)

If you need custom CSS beyond Tailwind utilities, add it to `theme/static_src/src/styles.css`:

```css
@import "tailwindcss";

/* Custom styles go below */
.my-custom-class {
    /* Your CSS here */
}

/* Or use PostCSS nesting */
.card {
    @apply bg-white rounded-lg shadow-md;

    &:hover {
        @apply shadow-lg;
    }
}
```

### Troubleshooting Tailwind

#### CSS not updating?

1. Make sure the dev watcher is running: `npm run dev`
2. Hard refresh your browser: `Ctrl+Shift+R` (Chrome) or `Ctrl+F5` (Firefox)
3. Check the terminal for PostCSS errors
4. Verify the `@source` path in `styles.css` includes your template directory

#### Classes not being generated?

1. Check that your template files match the `@source` pattern
2. Ensure you're using valid Tailwind class names
3. Rebuild from scratch:
   ```bash
   npm run build:clean && npm run build
   ```

---

## Docker Development

### Full Stack Development with Docker

Start all services (database, web, MinIO):

```bash
docker compose up -d
```

This will:
- Build the Docker image (including Tailwind CSS compilation)
- Start PostgreSQL database
- Start MinIO (S3-compatible storage)
- Start the Django application
- Run migrations automatically

### View Logs

```bash
# All services
docker compose logs -f

# Just the web service
docker compose logs -f web

# Last 50 lines
docker compose logs --tail=50 web
```

### Rebuild After Code Changes

```bash
# Rebuild web service
docker compose build web

# Restart web service
docker compose restart web

# Or rebuild and restart
docker compose up -d --build web
```

### Execute Commands in Container

```bash
# Django management commands
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell

# Collect static files
docker compose exec web python manage.py collectstatic --noinput --clear

# Access container shell
docker compose exec web bash
```

### Stop and Clean Up

```bash
# Stop services
docker compose down

# Stop and remove volumes (CAUTION: Deletes database data!)
docker compose down -v

# Remove all containers, networks, and unused images
docker compose down --rmi all --volumes
```

---

## Database Migrations

### Create Migrations

```bash
# Local development
python manage.py makemigrations

# Docker
docker compose exec web python manage.py makemigrations
```

### Apply Migrations

```bash
# Local development
python manage.py migrate

# Docker
docker compose exec web python manage.py migrate
```

### View Migration Status

```bash
python manage.py showmigrations
```

### Rollback Migration

```bash
# Rollback to specific migration
python manage.py migrate app_name migration_name

# Rollback all migrations for an app
python manage.py migrate app_name zero
```

---

## Testing

### Run Tests

```bash
# All tests
python manage.py test

# Specific app
python manage.py test doc_doc.core

# With coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Run Tests in Docker

```bash
docker compose exec web python manage.py test
```

---

## Code Quality

### Django Check

```bash
# General checks
python manage.py check

# Production deployment checks
python manage.py check --deploy
```

### Linting (if configured)

```bash
# Flake8
flake8 doc_doc/

# Black (code formatter)
black doc_doc/

# isort (import sorting)
isort doc_doc/
```

---

## Best Practices

### 1. **Never Commit Compiled CSS**

The `theme/static/css/dist/` directory is in `.gitignore`. The CSS is automatically compiled during Docker build.

### 2. **Use Tailwind Utility Classes**

Avoid writing custom CSS unless absolutely necessary. Tailwind provides utilities for 95% of use cases.

### 3. **Keep Migrations in Git**

Always commit migration files. They're part of your codebase.

### 4. **Use Environment Variables**

Never hardcode secrets. Use `.env` for local development, environment variables for production.

### 5. **Docker Multi-Stage Build**

Our Dockerfile uses multi-stage build:
- **Stage 1**: Compiles Tailwind CSS with Node.js
- **Stage 2**: Runs Python app (no Node.js in production)

This keeps the production image small and secure.

### 6. **Static Files in Production**

Production uses **WhiteNoise** to serve static files efficiently. No need for a separate Nginx configuration for static files.

---

## Common Issues

### Issue: "ModuleNotFoundError" when running Django

**Solution**: Make sure your virtual environment is activated and dependencies are installed.

```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: "relation does not exist" database error

**Solution**: Run migrations.

```bash
python manage.py migrate
```

### Issue: Tailwind CSS not working (no styles)

**Solution**: Compile the CSS.

```bash
cd theme/static_src
npm install
npm run build
```

### Issue: Docker build fails at npm install

**Solution**: Check your internet connection and Docker network settings. Try:

```bash
docker compose build --no-cache web
```

### Issue: Static files not loading in Docker

**Solution**: Collect static files and restart.

```bash
docker compose exec web python manage.py collectstatic --noinput --clear
docker compose restart web
```

---

## Useful Commands Reference

### Django

```bash
python manage.py runserver                    # Start dev server
python manage.py shell                        # Django shell
python manage.py dbshell                      # Database shell
python manage.py createsuperuser              # Create admin user
python manage.py collectstatic --noinput      # Collect static files
python manage.py migrate                      # Apply migrations
python manage.py makemigrations               # Create migrations
```

### Tailwind CSS

```bash
npm run dev                                   # Watch and compile CSS
npm run build                                 # Production build
npm run build:clean                          # Clean dist directory
```

### Docker

```bash
docker compose up -d                          # Start all services
docker compose down                           # Stop all services
docker compose logs -f web                    # View web logs
docker compose exec web bash                  # Access container
docker compose build --no-cache web           # Rebuild from scratch
docker compose restart web                    # Restart web service
```

---

## Getting Help

- **Django Documentation**: https://docs.djangoproject.com/
- **Tailwind CSS v4**: https://tailwindcss.com/docs
- **Docker Compose**: https://docs.docker.com/compose/

For project-specific issues, check the `README.md` or contact the development team.
