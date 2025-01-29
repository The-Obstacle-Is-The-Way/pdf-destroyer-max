from typing import Callable
from fastapi import Request, Response
from time import time
import logging
import json
import asyncio
from prometheus_client import Counter, Histogram, REGISTRY

class MonitoringMiddleware:
    def __init__(self):
        # Initialize metrics
        self.request_counter = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        self.request_latency = Histogram(
            'http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint']
        )
        self.error_counter = Counter(
            'http_errors_total',
            'Total HTTP errors',
            ['method', 'endpoint', 'error_type']
        )
        
        # Setup logging
        self.logger = logging.getLogger("monitoring")
        
    async def __call__(self, request: Request, call_next: Callable):
        start_time = time()
        request_id = self._generate_request_id()
        path = request.url.path
        method = request.method
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log request start
        self.logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "client_ip": request.client.host if request.client else None
            }
        )
        
        try:
            # Process request
            response: Response = await call_next(request)
            
            # Record metrics
            duration = time() - start_time
            self.request_counter.labels(
                method=method,
                endpoint=path,
                status=response.status_code
            ).inc()
            
            self.request_latency.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            # Log response
            self.logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration
                }
            )
            
            # Add monitoring headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = str(duration)
            
            return response
            
        except Exception as e:
            # Record error metrics
            self.error_counter.labels(
                method=method,
                endpoint=path,
                error_type=type(e).__name__
            ).inc()
            
            # Log error
            self.logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            
            raise
            
    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        import uuid
        return str(uuid.uuid4())
        
    async def _log_request_body(self, request: Request):
        """Log request body if content type is JSON."""
        if request.headers.get("content-type") == "application/json":
            try:
                body = await request.json()
                return json.dumps(body)
            except:
                return None
        return None
        
    def get_metrics(self):
        """Return current metrics."""
        return {
            "requests": REGISTRY.get_sample_value('http_requests_total'),
            "latency": REGISTRY.get_sample_value('http_request_duration_seconds_sum'),
            "errors": REGISTRY.get_sample_value('http_errors_total')
        }