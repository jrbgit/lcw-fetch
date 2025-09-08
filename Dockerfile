FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        gcc \
        && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY setup.py .
COPY README.md .

# Install the application
RUN pip install -e .

# Create logs directory
RUN mkdir -p /app/logs

# Create non-root user
RUN groupadd -r lcwuser && useradd -r -g lcwuser lcwuser
RUN chown -R lcwuser:lcwuser /app
USER lcwuser

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=5s --retries=3 \
    CMD python -m lcw_fetcher.main status || exit 1

# Default command
CMD ["python", "-m", "lcw_fetcher.main", "start"]
