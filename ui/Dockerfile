FROM python:3.11-slim

# Install system packages commonly needed by data and audio libs and to keep image small
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       git \
       curl \
       ca-certificates \
       ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first to leverage layer caching
COPY requirements.txt ./requirements.txt

# Install python dependencies
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy app sources
COPY . /app

# Use a non-root user for safety
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Expose Gradio default port
EXPOSE 7860

# Run the app
CMD ["python", "main.py"]
