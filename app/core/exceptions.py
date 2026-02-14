from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
import logging
import traceback

from app.core.config import settings

logger = logging.getLogger(__name__)

class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class DatabaseException(AppException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=500,
            details=details
        )

class ValidationException(AppException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=422,
            details=details
        )

async def app_exception_handler(
    request: Request,
    exc: AppException
) -> JSONResponse:
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "path": request.url.path,
            "status_code": exc.status_code,
            "details": exc.details,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "path": request.url.path,
        }
    )

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    logger.warning(
        f"Validation error: {request.url.path}",
        extra={
            "errors": exc.errors(),
            "body": exc.body,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "path": request.url.path,
        }
    )

async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    logger.warning(
        f"HTTP error {exc.status_code}: {request.url.path}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "path": request.url.path,
        }
    )

async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    logger.error(
        f"Database error: {str(exc)}",
        extra={
            "path": request.url.path,
            "error_type": type(exc).__name__,
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Database error occurred",
            "path": request.url.path,
        }
    )

async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    logger.error(
        f"Unhandled error: {str(exc)}",
        extra={
            "path": request.url.path,
            "error_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        },
        exc_info=True
    )
    error_message = str(exc) if settings.DEBUG else "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={
            "error": error_message,
            "path": request.url.path,
        }
    )
