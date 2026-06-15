"""Simple in-memory sliding-window rate limiter for API protection."""

import time
import threading
import logging
from functools import wraps
from typing import Dict, List

from flask import request, jsonify

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe in-memory sliding-window rate limiter.

    Tracks request timestamps per client IP and rejects requests that
    exceed the configured threshold within a 60-second window.
    """

    def __init__(self, requests_per_minute: int = 30) -> None:
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self._requests: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def _cleanup(self, ip: str, now: float) -> None:
        """Remove timestamps outside the current sliding window."""
        cutoff = now - self.window_seconds
        if ip in self._requests:
            self._requests[ip] = [
                ts for ts in self._requests[ip] if ts > cutoff
            ]

    def is_rate_limited(self, ip: str) -> bool:
        """Check whether *ip* has exceeded the rate limit.

        If the limit has **not** been reached the current timestamp is
        recorded and ``False`` is returned.
        """
        now = time.time()
        with self._lock:
            self._cleanup(ip, now)
            timestamps = self._requests.get(ip, [])
            if len(timestamps) >= self.requests_per_minute:
                return True
            timestamps.append(now)
            self._requests[ip] = timestamps
            return False

    def get_retry_after(self, ip: str) -> int:
        """Seconds until the oldest request in the window expires."""
        now = time.time()
        with self._lock:
            timestamps = self._requests.get(ip, [])
            if timestamps:
                oldest = min(timestamps)
                return max(1, int(self.window_seconds - (now - oldest)))
        return 1


def rate_limit(requests_per_minute: int = 30):
    """Decorator to apply rate limiting to a Flask route.

    Usage::

        @app.route('/api/predict')
        @rate_limit(requests_per_minute=30)
        def predict():
            ...
    """

    def decorator(f):
        limiter = RateLimiter(requests_per_minute)

        @wraps(f)
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr or "unknown"
            if limiter.is_rate_limited(client_ip):
                retry_after = limiter.get_retry_after(client_ip)
                logger.warning("Rate limit exceeded for IP: %s", client_ip)
                response = jsonify({
                    "success": False,
                    "error": {
                        "message": "Rate limit exceeded. Please try again later.",
                        "code": "RATE_LIMITED",
                        "retry_after_seconds": retry_after,
                    },
                })
                response.status_code = 429
                response.headers["Retry-After"] = str(retry_after)
                return response
            return f(*args, **kwargs)

        return wrapper

    return decorator
