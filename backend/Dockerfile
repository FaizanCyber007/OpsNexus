# ==============================================================================
# OpsNexus Backend Production Dockerfile (Django + Gunicorn + WhiteNoise)
# ==============================================================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install system dependencies required for compilation and Postgres connectivity
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for optimal Docker layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . /app/

# Ensure required persistent storage directories exist and entrypoint is executable
RUN mkdir -p /app/media /app/chroma_data /app/staticfiles && \
    chmod +x /app/entrypoint.sh

# Collect static assets into staticfiles directory using WhiteNoise
RUN SECRET_KEY="build-static-collection-key" \
    DEBUG="False" \
    python manage.py collectstatic --noinput

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "opsnexus_backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
