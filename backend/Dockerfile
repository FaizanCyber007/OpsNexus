# ==============================================================================
# OpsNexus Backend Production Dockerfile (Django + Gunicorn + WhiteNoise)
# ==============================================================================

# --- Stage 1: Build & Dependencies ---
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Final Runtime ---
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user and group
RUN groupadd -g 1001 appuser && \
    useradd -u 1001 -g appuser -d /app -s /bin/bash appuser

WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy backend source code
COPY . /app/

# Ensure required persistent storage directories exist, entrypoint is executable, and owned by appuser
RUN mkdir -p /app/media /app/chroma_data /app/staticfiles && \
    chmod +x /app/entrypoint.sh && \
    chown -R appuser:appuser /app

# Collect static assets into staticfiles directory using WhiteNoise
RUN SECRET_KEY="build-static-collection-key" \
    DEBUG="False" \
    python manage.py collectstatic --noinput && \
    chown -R appuser:appuser /app/staticfiles

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "opsnexus_backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
