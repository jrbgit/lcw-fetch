"""
Unit tests for LCW API exceptions.

Tests cover all custom exception classes and their behavior.
"""

import pytest

from src.lcw_fetcher.api.exceptions import (
    LCWAPIError,
    LCWAuthError,
    LCWNetworkError,
    LCWRateLimitError,
)


class TestLCWAPIError:
    """Tests for the base LCWAPIError exception."""

    def test_api_error_creation_with_message(self):
        """Test creating LCWAPIError with message."""
        error = LCWAPIError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.status_code is None
        assert error.response_data is None

    def test_api_error_creation_with_status_code(self):
        """Test creating LCWAPIError with status code."""
        error = LCWAPIError("Bad request", status_code=400)

        assert str(error) == "Bad request"
        assert error.status_code == 400
        assert error.response_data is None

    def test_api_error_creation_with_response_data(self):
        """Test creating LCWAPIError with response data."""
        response_data = {"error": {"code": 400, "description": "Bad request"}}
        error = LCWAPIError("Bad request", status_code=400, response_data=response_data)

        assert str(error) == "Bad request"
        assert error.status_code == 400
        assert error.response_data == response_data

    def test_api_error_inheritance(self):
        """Test that LCWAPIError inherits from Exception."""
        error = LCWAPIError("Test error")
        assert isinstance(error, Exception)

    def test_api_error_repr(self):
        """Test string representation of LCWAPIError."""
        error = LCWAPIError("Test error", status_code=400)
        repr_str = repr(error)

        assert "LCWAPIError" in repr_str
        assert "Test error" in repr_str
        assert "400" in repr_str


class TestLCWRateLimitError:
    """Tests for the LCWRateLimitError exception."""

    def test_rate_limit_error_creation(self):
        """Test creating LCWRateLimitError."""
        error = LCWRateLimitError("Rate limit exceeded", status_code=429)

        assert str(error) == "Rate limit exceeded"
        assert error.status_code == 429
        assert isinstance(error, LCWAPIError)

    def test_rate_limit_error_default_message(self):
        """Test LCWRateLimitError with default handling."""
        error = LCWRateLimitError("API rate limit exceeded")

        assert "rate limit" in str(error).lower()
        assert isinstance(error, LCWAPIError)

    def test_rate_limit_error_with_retry_after(self):
        """Test LCWRateLimitError with retry-after information."""
        response_data = {"retry_after": 60}
        error = LCWRateLimitError(
            "Rate limit exceeded", status_code=429, response_data=response_data
        )

        assert error.response_data["retry_after"] == 60


class TestLCWAuthError:
    """Tests for the LCWAuthError exception."""

    def test_auth_error_creation(self):
        """Test creating LCWAuthError."""
        error = LCWAuthError("Invalid API key", status_code=401)

        assert str(error) == "Invalid API key"
        assert error.status_code == 401
        assert isinstance(error, LCWAPIError)

    def test_auth_error_forbidden(self):
        """Test LCWAuthError for forbidden access."""
        error = LCWAuthError("Access forbidden", status_code=403)

        assert str(error) == "Access forbidden"
        assert error.status_code == 403

    def test_auth_error_inheritance(self):
        """Test LCWAuthError inheritance chain."""
        error = LCWAuthError("Auth failed")

        assert isinstance(error, LCWAPIError)
        assert isinstance(error, Exception)


class TestLCWNetworkError:
    """Tests for the LCWNetworkError exception."""

    def test_network_error_creation(self):
        """Test creating LCWNetworkError."""
        error = LCWNetworkError("Connection timeout")

        assert str(error) == "Connection timeout"
        assert (
            error.status_code is None
        )  # Network errors typically don't have status codes
        assert isinstance(error, LCWAPIError)

    def test_network_error_timeout(self):
        """Test LCWNetworkError for timeout scenarios."""
        error = LCWNetworkError("Request timeout after 30 seconds")

        assert "timeout" in str(error).lower()

    def test_network_error_connection_failed(self):
        """Test LCWNetworkError for connection failures."""
        error = LCWNetworkError("Connection refused")

        assert "connection" in str(error).lower()

    def test_network_error_dns_resolution(self):
        """Test LCWNetworkError for DNS issues."""
        error = LCWNetworkError("DNS resolution failed")

        assert "DNS" in str(error)


class TestExceptionChaining:
    """Tests for exception chaining and context."""

    def test_exception_chaining_with_cause(self):
        """Test exception chaining with __cause__."""
        try:
            # Simulate an underlying exception
            raise ValueError("Original error")
        except ValueError as original_error:
            # Chain with our custom exception
            new_error = LCWAPIError("Wrapped error")
            new_error.__cause__ = original_error

            assert new_error.__cause__ is original_error
            assert isinstance(new_error.__cause__, ValueError)

    def test_raising_with_from_clause(self):
        """Test raising with 'from' clause for proper chaining."""
        with pytest.raises(LCWNetworkError) as exc_info:
            try:
                raise ConnectionError("Network issue")
            except ConnectionError as e:
                raise LCWNetworkError("Failed to connect") from e

        assert isinstance(exc_info.value.__cause__, ConnectionError)
        assert str(exc_info.value.__cause__) == "Network issue"


class TestExceptionAttributes:
    """Tests for exception attributes and properties."""

    def test_all_exceptions_have_required_attributes(self):
        """Test that all exception classes have the expected attributes."""
        exceptions = [
            LCWAPIError("test"),
            LCWRateLimitError("test"),
            LCWAuthError("test"),
            LCWNetworkError("test"),
        ]

        for exc in exceptions:
            assert hasattr(exc, "status_code")
            assert hasattr(exc, "response_data")
            assert hasattr(exc, "args")

    def test_exception_attributes_default_values(self):
        """Test default values for exception attributes."""
        error = LCWAPIError("test message")

        assert error.status_code is None
        assert error.response_data is None
        assert error.args == ("test message",)

    def test_exception_attributes_custom_values(self):
        """Test custom values for exception attributes."""
        response_data = {"error": "Custom error data"}
        error = LCWAPIError(
            "test message", status_code=418, response_data=response_data
        )

        assert error.status_code == 418
        assert error.response_data == response_data
        assert error.args == ("test message",)


class TestExceptionUsagePatterns:
    """Tests for common exception usage patterns."""

    def test_catching_base_exception(self):
        """Test catching the base LCWAPIError."""
        with pytest.raises(LCWAPIError):
            raise LCWRateLimitError("Rate limited")

        with pytest.raises(LCWAPIError):
            raise LCWAuthError("Unauthorized")

        with pytest.raises(LCWAPIError):
            raise LCWNetworkError("Network error")

    def test_catching_specific_exceptions(self):
        """Test catching specific exception types."""
        with pytest.raises(LCWRateLimitError):
            raise LCWRateLimitError("Rate limited")

        with pytest.raises(LCWAuthError):
            raise LCWAuthError("Unauthorized")

        with pytest.raises(LCWNetworkError):
            raise LCWNetworkError("Network error")

    def test_exception_handling_hierarchy(self):
        """Test exception handling follows proper hierarchy."""

        def raise_rate_limit_error():
            raise LCWRateLimitError("Too many requests")

        # Specific exception should be caught first
        try:
            raise_rate_limit_error()
            assert False, "Exception should have been raised"
        except LCWRateLimitError as e:
            assert "requests" in str(e)
        except LCWAPIError:
            assert False, "Should have caught LCWRateLimitError specifically"

    def test_multiple_exception_types(self):
        """Test handling multiple exception types."""

        def raise_various_errors(error_type):
            if error_type == "auth":
                raise LCWAuthError("Unauthorized")
            elif error_type == "rate":
                raise LCWRateLimitError("Rate limited")
            elif error_type == "network":
                raise LCWNetworkError("Network error")
            else:
                raise LCWAPIError("Generic error")

        # Test catching different types
        with pytest.raises(LCWAuthError):
            raise_various_errors("auth")

        with pytest.raises(LCWRateLimitError):
            raise_various_errors("rate")

        with pytest.raises(LCWNetworkError):
            raise_various_errors("network")

        with pytest.raises(LCWAPIError):
            raise_various_errors("other")


class TestExceptionMessages:
    """Tests for exception message formatting and content."""

    def test_empty_message(self):
        """Test exceptions with empty messages."""
        error = LCWAPIError("")
        assert str(error) == ""

    def test_none_message(self):
        """Test exceptions with None message."""
        error = LCWAPIError(None)
        assert str(error) == "None"

    def test_unicode_message(self):
        """Test exceptions with Unicode messages."""
        unicode_msg = "错误信息 - Error message 🚫"
        error = LCWAPIError(unicode_msg)
        assert str(error) == unicode_msg

    def test_multiline_message(self):
        """Test exceptions with multiline messages."""
        multiline_msg = "Line 1\nLine 2\nLine 3"
        error = LCWAPIError(multiline_msg)
        assert str(error) == multiline_msg

    def test_very_long_message(self):
        """Test exceptions with very long messages."""
        long_msg = "x" * 10000
        error = LCWAPIError(long_msg)
        assert str(error) == long_msg
        assert len(str(error)) == 10000
