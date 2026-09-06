# Multi-stage Dockerfile for AMIP Backend POC
FROM python:3.11-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies for scientific geospatial computing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml .
RUN pip install --upgrade pip setuptools wheel && \
    pip install fastapi uvicorn pydantic pydantic-settings sqlalchemy asyncpg \
    geoalchemy2 redis celery shapely pyproj numpy scipy xarray zarr structlog \
    httpx pytest pytest-asyncio

# Copy packages and applications
COPY packages /app/packages
COPY apps /app/apps

# Install internal editable packages
ENV PYTHONPATH="/app/packages/domain/src:/app/packages/core/src:/app/packages/data_access/src:/app/packages/models/src:/app/packages/iceberg_physics/src:/app/packages/risk_engine/src:/app/packages/routing/src:/app/packages/services/src:/app/apps/backend/src"

WORKDIR /app/apps/backend/src

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
