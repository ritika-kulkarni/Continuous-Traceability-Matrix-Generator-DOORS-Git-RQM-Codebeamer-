"""Typed exception hierarchy for predictable failure handling."""

from __future__ import annotations


class TraceabilityError(Exception):
    """Base error for the traceability platform."""


class ConfigurationError(TraceabilityError):
    """Invalid or incomplete configuration."""


class AdapterError(TraceabilityError):
    """External system adapter failure."""

    def __init__(self, system: str, message: str, *, retryable: bool = False) -> None:
        self.system = system
        self.retryable = retryable
        super().__init__(f"[{system}] {message}")


class AuthenticationError(AdapterError):
    def __init__(self, system: str, message: str = "authentication failed") -> None:
        super().__init__(system, message, retryable=False)


class NotFoundError(AdapterError):
    def __init__(self, system: str, resource: str) -> None:
        super().__init__(system, f"resource not found: {resource}", retryable=False)


class ValidationError(TraceabilityError):
    """Domain or PR validation failure."""


class ExportError(TraceabilityError):
    """Matrix export failure."""
