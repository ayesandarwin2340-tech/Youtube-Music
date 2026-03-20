# Stage 1: Builder stage
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better cache utilization
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir --upgrade pip && \
    /venv/bin/pip install --no-cache-dir wheel && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Final stage
FROM python:3.11-slim

# Install FFmpeg and other runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 botuser && \
    mkdir -p /app && \
    chown -R botuser:botuser /app

# Copy virtual environment from builder
COPY --from=builder /venv /venv

# Set working directory
WORKDIR /app

# Copy application files
COPY --chown=botuser:botuser bot.py .
COPY --chown=botuser:botuser requirements.txt .

# Create necessary directories with proper permissions
RUN mkdir -p /tmp/downloads && \
    chown -R botuser:botuser /tmp/downloads && \
    chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Add virtual environment to PATH
ENV PATH="/venv/bin:$PATH"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Yangon

# Expose port (if needed for health checks)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('localhost', 8080))" || exit 1

# Run the bot
CMD ["python", "main.py"]
