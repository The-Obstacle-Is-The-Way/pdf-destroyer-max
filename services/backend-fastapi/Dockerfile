# Use NVIDIA CUDA base image with Ubuntu 20.04
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu20.04

# Set environment variables for CUDA and Python
ENV DEBIAN_FRONTEND=noninteractive
ENV CUDA_HOME=/usr/local/cuda-11.8
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Install Python 3.10 and dependencies
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3.10-distutils python3.10-dev gcc g++ curl && \
    rm -rf /var/lib/apt/lists/*

# Install pip cleanly using get-pip.py
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

# Set the working directory
WORKDIR /app

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install numpy scikit-learn torch transformers

# Copy the rest of the application files
COPY . /app/

# Expose the service port
EXPOSE 8001

# Define the command to run the application using uvicorn directly
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]