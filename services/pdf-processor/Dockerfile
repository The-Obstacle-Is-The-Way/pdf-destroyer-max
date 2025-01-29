# Use Python slim image with necessary dependencies
FROM python:3.10-slim

# Install only PDF-related dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends poppler-utils gcc libjpeg-dev zlib1g-dev libglib2.0-0 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app/
EXPOSE 8003
CMD ["python3", "main.py"]