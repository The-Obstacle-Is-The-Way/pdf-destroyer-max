# Use CUDA base image
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    TORCH_CUDA_ARCH_LIST="7.5 8.0 8.6" \
    TORCH_NVCC_FLAGS="-Xfatbin -compress-all" \
    MAX_JOBS=4

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    ninja-build \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies in layers
COPY requirements.txt .

# Install basic dependencies
RUN pip3 install --no-cache-dir -U pip setuptools wheel && \
    pip3 install --no-cache-dir torch==2.0.1+cu118 -f https://download.pytorch.org/whl/torch_stable.html

# Install other dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data/input data/output

# Predownload and cache models
RUN python3 -c "from transformers import AutoTokenizer, AutoModelForSeq2SeqGeneration; \
    model_name='facebook/bart-large-cnn'; \
    AutoTokenizer.from_pretrained(model_name); \
    AutoModelForSeq2SeqGeneration.from_pretrained(model_name)"

# Set up model caching
ENV TRANSFORMERS_CACHE=/app/model_cache
ENV HF_HOME=/app/model_cache

# Expose port
EXPOSE 8006

# Set up entrypoint script
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8006", "--workers", "4"]