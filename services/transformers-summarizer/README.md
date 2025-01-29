6. README for transformers-summarizer
Here’s an updated README.md for this container:

# Transformers Summarizer Service

The `transformers-summarizer` container provides an AI-powered summarization service using Hugging Face Transformers. It processes text and generates concise summaries, leveraging GPU acceleration when available.

## Features
- Supports summarization with models like `facebook/bart-large-cnn`.
- Compatible with GPU and CPU.
- REST API endpoints for easy integration.

## API Endpoints
### POST `/summarize`
- **Description**: Generate a summary for the given text.
- **Request Body**:
  ```json
  {
      "text": "Your input text here",
      "params": {
          "min_length": 30,
          "max_length": 130
      }
  }
Response:
{
    "summary": "Generated summary text here"
}
GET /health
Description: Check the health of the service.
Response:
{
    "status": "healthy",
    "model_loaded": true,
    "gpu_available": true
}
Setup and Usage
Prerequisites
Docker installed
NVIDIA drivers and CUDA for GPU acceleration
Build and Run
Build the Docker image:

docker build -t transformers-summarizer .
Run the container:

docker run -p 8006:8006 --gpus all transformers-summarizer
Test the API:

curl -X POST http://localhost:8006/summarize -H "Content-Type: application/json" \
     -d '{"text": "Your input text here"}'
Troubleshooting
Model Not Loading: Ensure the transformers library and the correct model are installed.
GPU Not Detected: Verify NVIDIA drivers and CUDA installation with nvidia-smi.
Logs
Application logs: logs/app.log
Error logs: logs/error.log
Tests
Run the unit tests:

pytest tests/

---

This setup ensures the `transformers-summarizer` container is fully functional and aligned with the overall multi-container architecture. Let me know if you need further refinements!