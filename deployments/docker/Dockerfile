# Multi-stage Docker build for Claude Guardian

# Build stage
FROM python:3.13-slim as builder

# Set build arguments
ARG BUILD_ENV=production
ARG VERSION=latest

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt requirements-dev.txt ./
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip wheel setuptools && \
    pip install -r requirements.txt && \
    if [ "$BUILD_ENV" = "development" ]; then pip install -r requirements-dev.txt; fi

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/
COPY scripts/ ./scripts/
COPY config/ ./config/

# Build the package
RUN pip install -e .

# Production stage
FROM python:3.13-slim as production

# Set metadata labels
LABEL maintainer="Claude Guardian Team <team@claude-guardian.com>" \
      version="${VERSION}" \
      description="Claude Guardian threat detection and response system" \
      org.opencontainers.image.title="Claude Guardian" \
      org.opencontainers.image.description="Advanced threat detection and response system" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.vendor="Claude Guardian Team" \
      org.opencontainers.image.licenses="MIT"

# Create non-root user
RUN groupadd -r claudeguardian && useradd -r -g claudeguardian claudeguardian

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/claudeguardian/.local/bin:$PATH" \
    APP_ENV=production \
    WORKERS=4 \
    PORT=8000

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create directories
RUN mkdir -p /app /var/log/claude-guardian /var/lib/claude-guardian && \
    chown -R claudeguardian:claudeguardian /app /var/log/claude-guardian /var/lib/claude-guardian

# Switch to non-root user
USER claudeguardian
WORKDIR /app

# Copy from builder stage
COPY --from=builder --chown=claudeguardian:claudeguardian /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder --chown=claudeguardian:claudeguardian /usr/local/bin/ /usr/local/bin/
COPY --from=builder --chown=claudeguardian:claudeguardian /app/src/ ./src/
COPY --from=builder --chown=claudeguardian:claudeguardian /app/config/ ./config/
COPY --from=builder --chown=claudeguardian:claudeguardian /app/scripts/ ./scripts/

# Copy additional files
COPY --chown=claudeguardian:claudeguardian deployments/docker/entrypoint.sh ./
COPY --chown=claudeguardian:claudeguardian deployments/docker/healthcheck.py ./

# Make scripts executable
USER root
RUN chmod +x /app/entrypoint.sh /app/healthcheck.py
USER claudeguardian

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python healthcheck.py || exit 1

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# Default command
CMD ["uvicorn", "claude_guardian.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]