. Build Docker Images for Each CUDA Version
To ensure compatibility, build two separate Docker images:

For CUDA 11.8:

docker build --build-arg CUDA_VERSION=11.8 -t ocr-tesseract-cuda11 .



For CUDA 12.6:

docker build --build-arg CUDA_VERSION=12.6 -t ocr-tesseract-cuda12 .


# For CUDA 11.8
use_cuda11

# For CUDA 12.6
use_cuda12


Run the Container:
For CUDA 11.8:

docker run --rm --gpus all \
  -e PATH=$PATH \
  -e LD_LIBRARY_PATH=$LD_LIBRARY_PATH \
  -p 8002:8002 \
  ocr-tesseract-cuda11
For CUDA 12.6:

docker run --rm --gpus all \
  -e PATH=$PATH \
  -e LD_LIBRARY_PATH=$LD_LIBRARY_PATH \
  -p 8002:8002 \
  ocr-tesseract-cuda12





# Neural OCR Tesseract Service

## Overview
Advanced OCR processing system built on Tesseract core with state-of-the-art neural enhancements.

### Core Technologies
- **Tesseract OCR Engine**: The primary OCR engine used for text extraction.
- **Neural Network Enhancements**:
  - **DIFT (Deep Image Filter Transform)** for image preprocessing.
  - **PaddleOCR** integration (secondary OCR engine) for multi-model ensemble.
  - **TensorFlow-based Handwriting Recognition**.
  - **Mathematical Equation Parsing** using neural models.
- **GPU Acceleration**: PaddleOCR and TensorFlow-based models leverage GPU acceleration to significantly boost the performance.

### Features
- **Multi-language Support**: English, French, German, Spanish.
- **Neural Image Enhancement**: DIFT for improved OCR quality.
- **Handwriting and Mathematical Parsing**: Detect and extract formulas and handwritten content.
- **PaddleOCR Integration**: For a multi-model ensemble approach.

### Additional Features and Roadmap
1. **Language Support Expansion**: Add support for Arabic, Chinese, and Indic languages.
2. **Customizable OCR Pipelines**: Users can choose specific models for their OCR pipeline.
3. **Batch Processing Capability**: For handling multiple images simultaneously.
4. **Enhanced GPU Utilization**: Optimize batching and multi-GPU usage.
5. **Plugin and API Integration**: For easy integration into existing systems.
6. **Improved Error Handling and Resilience**: Granular error handling with retry mechanisms.
7. **Structured Logging Format**: JSON structured logging for monitoring tools.

## Getting Started

### Prerequisites
- Python 3.10+
- NVIDIA GPU with CUDA (for GPU acceleration)
- Docker & Docker Compose (for running services in containers)

### Installation
Clone the repository and set up a Python virtual environment:

```sh
git clone https://github.com/yourusername/pdf-destroyer-max.git
cd pdf-destroyer-max/services/neural-ocr-tesseract

# Create a Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
