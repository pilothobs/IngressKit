# Multi-stage Dockerfile for IngressKit
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

###########################################
# ingresskit-core: SDK + CLI only
###########################################
FROM base as ingresskit-core

# Copy SDK
COPY sdk/python /app/sdk
WORKDIR /app/sdk

# Install SDK dependencies
RUN pip install -r requirements.txt && \
    pip install -e .

# Create CLI entrypoint
RUN echo '#!/bin/bash\nexec python -m ingresskit.cli "$@"' > /usr/local/bin/ingresskit && \
    chmod +x /usr/local/bin/ingresskit

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import ingresskit; print('OK')" || exit 1

ENTRYPOINT ["ingresskit"]
CMD ["--help"]

###########################################
# ingresskit-server: FastAPI server
###########################################
FROM base as ingresskit-server

# Copy SDK first (server depends on it)
COPY sdk/python /app/sdk
WORKDIR /app/sdk
RUN pip install -r requirements.txt && pip install -e .

# Copy server
WORKDIR /app
COPY server/main_oss.py /app/main.py
COPY server/requirements_oss.txt /app/requirements.txt
COPY server/static /app/static

# Install server dependencies
RUN pip install -r requirements.txt

# Create non-root user
RUN useradd --create-home --shell /bin/bash ingresskit
USER ingresskit

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/ping || exit 1

# Start server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

###########################################
# Default target: server
###########################################
FROM ingresskit-server as default
