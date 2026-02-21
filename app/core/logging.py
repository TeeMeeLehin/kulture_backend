import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kulture_api")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log Request
        logger.info(f"Incoming Request: {request.method} {request.url}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(f"Response: {response.status_code} | Time: {process_time:.4f}s")
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request Failed: {e} | Time: {process_time:.4f}s")
            raise e # Re-raise for exception handler

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Our team has been notified."},
    )
