# Build stage
FROM python:3.9-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies with pip cache cleanup
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.9-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy from builder and application files
COPY --from=builder /root/.local /root/.local
COPY . .

# Environment configuration
ENV PATH=/root/.local/bin:$PATH \
    PYTHONPATH=/app \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create needed directories
RUN mkdir -p /app/logs /app/static

# Health check with timeout
HEALTHCHECK --interval=30s --timeout=10s \
    --start-period=5s \
    --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Non-root user for security
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Port and runtime configuration
EXPOSE 5000

# Gunicorn configuration
CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
    "--workers", "4", \
    "--threads", "2", \
    "--timeout", "120", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "app:app"]