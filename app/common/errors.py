"""
Standardized error handling for SOA Library Management System.
Provides consistent error responses across all services.
"""
from flask import jsonify
from functools import wraps


class AppError(Exception):
    """Base application error with HTTP status code."""
    
    def __init__(self, message, status_code=400, error_code=None, details=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "GENERIC_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppError):
    """Validation error (400)."""
    
    def __init__(self, message, details=None):
        super().__init__(message, 400, "VALIDATION_ERROR", details)


class NotFoundError(AppError):
    """Resource not found error (404)."""
    
    def __init__(self, message, details=None):
        super().__init__(message, 404, "NOT_FOUND", details)


class ConflictError(AppError):
    """Conflict error (409)."""
    
    def __init__(self, message, details=None):
        super().__init__(message, 409, "CONFLICT", details)


class UnauthorizedError(AppError):
    """Unauthorized error (401)."""
    
    def __init__(self, message, details=None):
        super().__init__(message, 401, "UNAUTHORIZED", details)


class ForbiddenError(AppError):
    """Forbidden error (403)."""
    
    def __init__(self, message, details=None):
        super().__init__(message, 403, "FORBIDDEN", details)


class InternalError(AppError):
    """Internal server error (500)."""
    
    def __init__(self, message, details=None):
        super().__init__(message, 500, "INTERNAL_ERROR", details)


def error_response(message, status_code=400, error_code=None, details=None):
    """Generate standardized error response."""
    response = {
        "success": False,
        "error": {
            "code": error_code or "ERROR",
            "message": message
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    return jsonify(response), status_code


def success_response(data=None, message=None, status_code=200):
    """Generate standardized success response."""
    response = {
        "success": True
    }
    
    if message:
        response["message"] = message
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response), status_code


def handle_errors(f):
    """Decorator to handle errors consistently."""
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AppError as e:
            return error_response(e.message, e.status_code, e.error_code, e.details)
        except Exception as e:
            # Log the error here in production
            return error_response(
                "An unexpected error occurred",
                500,
                "INTERNAL_ERROR",
                {"original_error": str(e)}
            )
    
    return decorated_function


def register_error_handlers(app):
    """Register global error handlers for Flask app."""
    
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return error_response(error.message, error.status_code, error.error_code, error.details)
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return error_response("Resource not found", 404, "NOT_FOUND")
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        return error_response("Internal server error", 500, "INTERNAL_ERROR")
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        # Log the error in production
        return error_response(
            "An unexpected error occurred",
            500,
            "INTERNAL_ERROR",
            {"original_error": str(error)}
        )
