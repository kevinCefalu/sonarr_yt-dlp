# check=skip=UndefinedVar

FROM python:3.11-alpine AS base

# Install system dependencies
RUN apk update && \
    apk add --no-cache ffmpeg && \
    rm -rf /var/cache/apk/*

FROM python:3.11-alpine AS dependencies

# Install build dependencies and Python packages
COPY requirements.txt ./
RUN apk update && \
    apk add --no-cache build-base && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/cache/apk/*

FROM base

ARG UID=1000 GID=1000 UNAME=abc

# Create user and directories
RUN adduser -D -u $UID $UNAME && \
    mkdir -p /config /sonarr_root /logs /app && \
    chown -R $UNAME:$UNAME /config /sonarr_root /logs /app

# Install requirements directly (simpler approach)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Copy application files
COPY app/ /app/
RUN chmod +x /app/main.py && \
    chown -R $UNAME:$UNAME /app

# Set working directory and user
WORKDIR /app
USER $UNAME

# Set environment variables

ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV CONFIGPATH="/config/config.yml"

# Define volumes
VOLUME ["/config", "/sonarr_root", "/logs"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); from config import ConfigManager; ConfigManager().load_config()" || exit 1

# Start the application
CMD ["python", "-u", "/app/main.py"]
