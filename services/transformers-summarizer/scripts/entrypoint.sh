#!/bin/bash

# Configure CUDA settings
export CUDA_VISIBLE_DEVICES=0
export CUDA_LAUNCH_BLOCKING=0

# Optimize Python settings
export PYTHONOPTIMIZE=2
export TOKENIZERS_PARALLELISM=true

# Set up model caching
mkdir -p /app/model_cache
export TRANSFORMERS_CACHE=/app/model_cache
export HF_HOME=/app/model_cache

# Configure torch settings
python3 -c "
import torch
torch.backends.cudnn.benchmark = True
torch.backends.cuda.matmul.allow_tf32 = True
"

# Execute the main command
exec "$@"
