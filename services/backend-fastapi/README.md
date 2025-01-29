
## 1. Backend FastAPI Service
# services/backend-fastapi/README.md
# Backend FastAPI Service

## Overview
Core API gateway service handling all PDF processing requests and orchestrating the distributed system.

### Features
- RESTful API endpoints for all PDF operations
- Request validation and error handling
- Service orchestration and task distribution
- Rate limiting and request throttling
- Authentication and authorization

### API Endpoints
- `POST /api/v1/pdf/process`: Process new PDF
- `GET /api/v1/pdf/{id}`: Get processing status
- `POST /api/v1/pdf/batch`: Batch processing
- `GET /api/v1/health`: Service health check

### Configuration
- Environment variables in `/config`
- API settings in `settings.py`
- Logging configuration in `logging.py`

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8000

# Run tests
pytest
```