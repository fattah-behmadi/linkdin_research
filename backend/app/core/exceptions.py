"""Domain-level errors, translated to HTTP responses in `app.main`."""

from __future__ import annotations


class AppError(Exception):
    """Base class for expected, translatable application errors."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProfileNotFoundError(AppError):
    status_code = 404
    code = "profile_not_found"

    def __init__(self, profile_id: int) -> None:
        super().__init__(f"Profile {profile_id} was not found.")


class SearchBackendUnavailableError(AppError):
    status_code = 503
    code = "search_backend_unavailable"
