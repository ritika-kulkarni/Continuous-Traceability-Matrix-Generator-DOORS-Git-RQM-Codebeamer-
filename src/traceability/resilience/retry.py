"""Retry helpers with exponential backoff for flaky ALM/REST APIs."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from traceability.exceptions import AdapterError
from traceability.logging_setup import get_logger

T = TypeVar("T")
logger = get_logger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, AdapterError):
        return exc.retryable
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {408, 425, 429, 500, 502, 503, 504}
    return False


async def with_retries(
    operation: Callable[[], Awaitable[T]],
    *,
    system: str,
    max_attempts: int = 3,
    action: str = "request",
) -> T:
    """Execute an async operation with structured retries."""
    attempts = max(1, max_attempts)
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential_jitter(initial=0.5, max=8.0),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
    ):
        with attempt:
            try:
                return await operation()
            except Exception as exc:
                logger.warning(
                    "adapter_retry",
                    system=system,
                    action=action,
                    attempt=attempt.retry_state.attempt_number,
                    max_attempts=attempts,
                    error=str(exc),
                    retryable=_is_retryable(exc),
                )
                raise
    raise AdapterError(system, f"{action} failed after retries", retryable=False)
