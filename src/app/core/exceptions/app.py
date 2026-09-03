from fastapi import status


class AppException(Exception):
    """Base application exception with HTTP mapping metadata."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message: str = "Internal server error"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Resource not found"


class InvalidStateTransitionError(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_message = "Invalid state transition"


class UnauthorizedActionError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "You are not authorized to perform this action"


class ValidationError(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Validation error"