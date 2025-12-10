# Makefile for doc-doc project
# Makes common development tasks easier

.PHONY: help install dev build migrate collectstatic superuser test clean docker-build docker-up docker-down docker-logs css-dev css-build

# Default target
help:
	@echo "doc-doc Development Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          - Install all dependencies (Python + Node.js)"
	@echo "  make css-build        - Build Tailwind CSS for production"
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Start Django development server"
	@echo "  make css-dev          - Start Tailwind CSS watcher (run in separate terminal)"
	@echo "  make migrate          - Run database migrations"
	@echo "  make superuser        - Create Django superuser"
	@echo "  make collectstatic    - Collect static files"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     - Build Docker images"
	@echo "  make docker-up        - Start all Docker services"
	@echo "  make docker-down      - Stop all Docker services"
	@echo "  make docker-logs      - View Docker logs (web service)"
	@echo "  make docker-shell     - Access web container shell"
	@echo "  make docker-migrate   - Run migrations in Docker"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test             - Run Django tests"
	@echo "  make check            - Run Django system checks"
	@echo "  make clean            - Clean temporary files"

# Installation
install:
	@echo "Installing Python dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo ""
	@echo "Installing Node.js dependencies for Tailwind CSS..."
	cd theme/static_src && npm install
	@echo ""
	@echo "Installation complete!"
	@echo "Next steps:"
	@echo "  1. Configure your .env file"
	@echo "  2. Run 'make migrate' to setup database"
	@echo "  3. Run 'make superuser' to create admin user"
	@echo "  4. Run 'make css-build' to compile CSS"

# Development server
dev:
	python manage.py runserver

# Tailwind CSS development (watch mode)
css-dev:
	@echo "Starting Tailwind CSS watcher..."
	@echo "Keep this running while you develop."
	@echo "CSS will auto-rebuild when templates change."
	cd theme/static_src && npm run dev

# Tailwind CSS production build
css-build:
	@echo "Building Tailwind CSS for production..."
	cd theme/static_src && npm run build
	@echo "CSS build complete!"

# Database migrations
migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

# Create superuser
superuser:
	python manage.py createsuperuser

# Collect static files
collectstatic:
	python manage.py collectstatic --noinput --clear

# Run tests
test:
	python manage.py test

# Django checks
check:
	python manage.py check --deploy

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov 2>/dev/null || true
	@echo "Clean complete!"

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker compose build --no-cache

docker-up:
	@echo "Starting Docker services..."
	docker compose up -d
	@echo ""
	@echo "Services started!"
	@echo "Application: http://localhost:8080"
	@echo "MinIO Console: http://localhost:9091"
	@echo ""
	@echo "View logs: make docker-logs"

docker-down:
	@echo "Stopping Docker services..."
	docker compose down

docker-logs:
	docker compose logs -f web

docker-logs-all:
	docker compose logs -f

docker-shell:
	docker compose exec web bash

docker-migrate:
	docker compose exec web python manage.py migrate

docker-collectstatic:
	docker compose exec web python manage.py collectstatic --noinput --clear

docker-superuser:
	docker compose exec web python manage.py createsuperuser

docker-restart:
	docker compose restart web

# Full development setup (from scratch)
setup: install migrate superuser css-build collectstatic
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "To start development:"
	@echo "  Terminal 1: make css-dev"
	@echo "  Terminal 2: make dev"
	@echo ""
	@echo "Access your app at: http://localhost:8000"
	@echo "Admin interface: http://localhost:8000/admin"

# Full Docker setup (from scratch)
docker-setup: docker-build docker-up docker-migrate docker-collectstatic
	@echo ""
	@echo "✅ Docker setup complete!"
	@echo ""
	@echo "Application: http://localhost:8080"
	@echo "Create admin user: make docker-superuser"
	@echo "View logs: make docker-logs"
