# Use a CUDA 11.8 runtime base image compatible with PyTorch cu118
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu20.04

# Set environment variables for CUDA
ENV PATH=/usr/local/cuda/bin:$PATH
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Install Python and necessary tools
RUN apt-get update && apt-get install -y \
    python3-pip python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, and wheel
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

# Set the working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the application port
EXPOSE 8002

# Define the entry point for the application
CMD ["python3", "main.py"]
