# Build stage
FROM python:3.9-slim as builder

WORKDIR /app
COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.9-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH \
    PYTHONPATH=/app \
    FLASK_APP=app.py \
    FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]