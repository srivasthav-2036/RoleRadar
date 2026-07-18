"""
groq_throttle.py

Shared per-minute rate-limit enforcement and retry logic for all
modules that make Groq API calls.

WHY A SHARED CLASS INSTEAD OF MODULE-LEVEL GLOBALS:
Both jd_parser.py and matcher.py need identical sliding-window throttle
logic, but they must use SEPARATE windows — their TPM budgets are
tracked independently (different PROVIDER_NAMEs in usage_tracker, and
potentially different API keys).  A class gives each caller its own
window while keeping the logic in one place.

USAGE:
    throttle = GroqThrottle(rpm_limit=30, tpm_limit=6000, label="[matcher]")

    # before each call:
    throttle.wait_for_capacity(estimated_tokens)

    # after each successful call:
    throttle.record_call(actual_tokens)

    # for retry-wrapped calls:
    result = throttle.call_with_retry(my_groq_fn, arg1, arg2)
"""

import logging
import time
from collections import deque
from typing import Callable, Any

logger = logging.getLogger(__name__)

# Default retry settings — callers may override via call_with_retry params
DEFAULT_MAX_RETRIES = 4
DEFAULT_BASE_DELAY  = 5.0   # seconds; doubles each attempt


class GroqThrottle:
    """
    Sliding 60-second window enforcer for Groq RPM and TPM limits,
    plus exponential-backoff retry on 429 responses.

    Parameters
    ----------
    rpm_limit : int
        Max requests per minute allowed by Groq for this key/model.
    tpm_limit : int
        Max tokens per minute allowed by Groq for this key/model.
    label : str
        Short prefix for log messages, e.g. "[matcher]" or "[jd_parser]".
    """

    def __init__(self, rpm_limit: int, tpm_limit: int, label: str) -> None:
        self._rpm_limit = rpm_limit
        self._tpm_limit = tpm_limit
        self._label     = label
        self._window: deque = deque()   # (timestamp: float, tokens: int)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _prune(self) -> None:
        """Drop entries older than 60 seconds from the window."""
        cutoff = time.time() - 60.0
        while self._window and self._window[0][0] < cutoff:
            self._window.popleft()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def wait_for_capacity(self, estimated_tokens: int) -> None:
        """
        Block (sleep) until a call costing `estimated_tokens` fits
        within the rolling 60-second window without exceeding the
        configured RPM or TPM limit.

        Raises ValueError if `estimated_tokens` alone exceeds TPM_LIMIT
        (i.e. the call can never succeed — caller should reduce batch
        size or shorten the prompt).
        """
        while True:
            self._prune()
            tokens_used   = sum(t for _, t in self._window)
            requests_used = len(self._window)

            fits_tokens   = tokens_used   + estimated_tokens <= self._tpm_limit
            fits_requests = requests_used + 1               <= self._rpm_limit

            if fits_tokens and fits_requests:
                return

            if not self._window:
                raise ValueError(
                    f"{self._label} Single call ({estimated_tokens} tokens) exceeds "
                    f"TPM_LIMIT ({self._tpm_limit}). "
                    "Reduce batch size or shorten the prompt."
                )

            oldest_ts = self._window[0][0]
            sleep_for = max(0.5, 60.0 - (time.time() - oldest_ts))
            logger.info(
                "%s Pacing for TPM/RPM: %d tokens / %d requests in last "
                "60 s — waiting %.1f s (tokens_fit=%s, requests_fit=%s)",
                self._label, tokens_used, requests_used, sleep_for,
                fits_tokens, fits_requests,
            )
            time.sleep(sleep_for)

    def record_call(self, actual_tokens: int) -> None:
        """Record a completed call in the rolling window."""
        self._window.append((time.time(), actual_tokens))

    def call_with_retry(
        self,
        fn: Callable[[], Any],
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay:  float = DEFAULT_BASE_DELAY,
    ) -> Any:
        """
        Call `fn()` and retry up to `max_retries` times on 429 errors
        using exponential backoff.  Re-raises on non-429 errors or after
        all retries are exhausted.

        Parameters
        ----------
        fn : callable
            Zero-argument callable that performs the Groq API call and
            returns its result.  Bind arguments with functools.partial or
            a lambda before passing.
        max_retries : int
            Total attempts (including the first).
        base_delay : float
            Initial sleep seconds after first 429; doubles each retry.
        """
        delay = base_delay
        for attempt in range(1, max_retries + 1):
            try:
                return fn()
            except Exception as exc:
                status  = getattr(getattr(exc, "response", None), "status_code", None)
                is_429  = (
                    status == 429
                    or "429"        in str(exc)
                    or "rate_limit" in str(exc).lower()
                )

                if is_429 and attempt < max_retries:
                    logger.warning(
                        "%s 429 rate-limit on attempt %d/%d — retrying in %.1f s. %s",
                        self._label, attempt, max_retries, delay, exc,
                    )
                    time.sleep(delay)
                    delay *= 2
                    continue

                if is_429:
                    logger.error(
                        "%s 429 rate-limit exhausted after %d attempts. %s",
                        self._label, max_retries, exc,
                    )
                else:
                    logger.error(
                        "%s Call failed on attempt %d/%d. %s",
                        self._label, attempt, max_retries, exc,
                    )
                raise
