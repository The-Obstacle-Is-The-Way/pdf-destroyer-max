from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from datetime import datetime
from functools import wraps

class AuthMiddleware:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.security = HTTPBearer()

    async def __call__(self, request: Request, call_next: Callable):
        try:
            # Skip auth for health check and public endpoints
            if request.url.path in ["/health", "/docs", "/openapi.json"]:
                return await call_next(request)

            # Get token from header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authorization header"
                )

            # Validate token format
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme"
                )

            # Validate and decode token
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
                # Add decoded token to request state
                request.state.user = payload
            except JWTError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token: {str(e)}"
                )

            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )

            response = await call_next(request)
            return response

        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail}
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error during authentication"}
            )

    @staticmethod
    def requires_scope(required_scope: str):
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = kwargs.get("request")
                if not request or not hasattr(request.state, "user"):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )

                scopes = request.state.user.get("scopes", [])
                if required_scope not in scopes:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Required scope '{required_scope}' not found"
                    )

                return await func(*args, **kwargs)
            return wrapper
        return decorator