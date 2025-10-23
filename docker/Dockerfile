# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app

# install system deps needed for building common wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_HOME}

# create a non-root user
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser ${APP_HOME}

# copy only requirements first for better caching
COPY app/requirements.txt ./requirements.txt

# install python dependencies as root then drop to non-root user
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# copy application code
COPY app/ ./

# ensure correct ownership
RUN chown -R appuser:appuser ${APP_HOME}

USER appuser

# expose port application listens on
EXPOSE 5000

# healthcheck (runs as root in container runtime; may be ignored by some orchestrators)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# default command: run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
