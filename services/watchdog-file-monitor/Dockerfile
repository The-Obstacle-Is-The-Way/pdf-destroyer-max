# Base image: Lightweight Python image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies for Watchdog
RUN apt-get update && apt-get install -y \
    gcc \
    libssl-dev \
    python3-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install pip dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optional: Install additional dependencies for `watchmedo` CLI (only if needed)
RUN pip install --no-cache-dir 'watchdog[watchmedo]'

# Create directories for logs
RUN mkdir -p /app/logs

# Copy application files
COPY handlers/ handlers/
COPY utils/ utils/
COPY tests/ tests/
COPY main.py .

# Expose port 8007 to match docker-compose.yml
EXPOSE 8007

# Command to run the application
CMD ["python", "main.py"]