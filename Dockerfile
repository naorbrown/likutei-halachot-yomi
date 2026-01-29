# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash botuser

# Copy installed packages from builder
COPY --from=builder /root/.local /home/botuser/.local

# Copy application code
COPY --chown=botuser:botuser . .

# Switch to non-root user
USER botuser

# Add local pip packages to PATH
ENV PATH=/home/botuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Health check - verify bot process is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python scripts/run_polling.py" || exit 1

# Run the bot
CMD ["python", "scripts/run_polling.py"]
