# Use Python base image
FROM python:3.10-slim

# Set environment variables for Python
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements.txt to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "main.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
