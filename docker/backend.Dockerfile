# Multi-stage build for Fly.io optimization
FROM python:3.11-slim as builder

# Install build dependencies for ML libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

# Build Python wheels
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /tmp/wheels -r /tmp/requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies for audio processing and ML
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    libsndfile1 \
    libgomp1 \
    git-lfs \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy and install pre-built wheels
COPY --from=builder /tmp/wheels /tmp/wheels
COPY backend/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache /tmp/wheels/* && \
    rm -rf /tmp/wheels

# Copy application code
COPY backend/ .

# Create app user and directories
RUN useradd --create-home --shell /bin/bash --uid 1000 app && \
    mkdir -p /app/uploads/audio /app/ckpt && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Environment variables optimized for Fly.io + Neon + R2
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    STORAGE_TYPE=s3 \
    PORT=8000

# Expose port (Fly.io will bind to this)
EXPOSE 8000

# Health check for Fly.io readiness
HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Production command optimized for Fly.io scale-to-zero
CMD ["uvicorn", "main:socket_app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info", "--access-log"]