# ============================================
# Stage 1: Build Tailwind CSS with Node.js
# ============================================
FROM node:22-slim AS css-builder

WORKDIR /app

# Copy only package files first (for better caching)
COPY theme/static_src/package*.json /app/theme/static_src/
RUN cd /app/theme/static_src && npm ci --prefer-offline --no-audit

# Copy source CSS and templates for Tailwind scanning
COPY theme/static_src/ /app/theme/static_src/
COPY templates/ /app/templates/
COPY doc_doc/ /app/doc_doc/

# Build Tailwind CSS (scans all templates and generates full CSS)
RUN cd /app/theme/static_src && npm run build

# ============================================
# Stage 2: Python application
# ============================================
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    netcat-openbsd \
    curl \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . /app/

# Copy compiled CSS from css-builder stage
COPY --from=css-builder /app/theme/static/css/dist/ /app/theme/static/css/dist/

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command - Using Uvicorn with ASGI
CMD ["uvicorn", "doc_doc.asgi:application", "--host", "0.0.0.0", "--port", "8080", "--workers", "3", "--timeout-keep-alive", "120"]
