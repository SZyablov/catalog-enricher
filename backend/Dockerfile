# Multi-stage Dockerfile for the catalog_enricher backend

FROM python:3.12-slim as build
WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install into a wheel cache
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip --no-cache-dir install -r requirements.txt

# --- Final runtime image ---
FROM python:3.12-slim
WORKDIR /app

# Runtime OS packages (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from build stage
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

# Copy application code
COPY . /app

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose default port for the API
EXPOSE 8000

# Default command runs the entrypoint which supports running either the web server or a worker
ENTRYPOINT ["/app/entrypoint.sh"]
# By default, run the web server. To run worker, override CMD to: ["worker"]
CMD ["web"]