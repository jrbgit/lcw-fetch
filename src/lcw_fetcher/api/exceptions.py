"""Custom exceptions for LCW API client"""


class LCWAPIError(Exception):
    """Base exception for LCW API errors"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class LCWRateLimitError(LCWAPIError):
    """Raised when API rate limit is exceeded"""
    pass


class LCWAuthError(LCWAPIError):
    """Raised when API authentication fails"""
    pass


class LCWValidationError(LCWAPIError):
    """Raised when request validation fails"""
    pass


class LCWNetworkError(LCWAPIError):
    """Raised when network/connection issues occur"""
    pass
