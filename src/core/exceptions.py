"""Custom exceptions for the AquaMax agent."""

from __future__ import annotations


class AquaMaxError(Exception):
    """Base exception for all AquaMax agent errors."""

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class LLMError(AquaMaxError):
    """Raised when LLM API calls fail."""

    pass


class ToolError(AquaMaxError):
    """Raised when a tool execution fails."""

    pass


class DatabaseError(AquaMaxError):
    """Raised when database operations fail."""

    pass


class ValidationError(AquaMaxError):
    """Raised when input validation fails."""

    pass


class ConfigurationError(AquaMaxError):
    """Raised when configuration is invalid."""

    pass
