"""API key authentication and rate limiting.

Simple, production-ready auth that:
- Validates API keys from Authorization header
- Tracks usage per key for billing
- Enforces rate limits per key
- Allows unauthenticated access in development mode
"""

import hashlib
import os
import time
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel


class ApiKey(BaseModel):
    """An API key with associated metadata and limits."""

    key_hash: str  # SHA-256 of the actual key (never store plaintext)
    name: str
    owner: str
    created_at: str
    active: bool = True
    tier: str = "starter"  # starter, professional, enterprise
    rate_limit_per_minute: int = 10
    monthly_quota: int = 100
    usage_this_month: int = 0


class RateLimitEntry(BaseModel):
    """Tracks request timestamps for rate limiting."""

    timestamps: List[float] = []


class AuthManager:
    """Manages API key authentication and rate limiting.

    In development mode (NEXUSOS_AUTH_MODE=open), all requests are allowed.
    In production mode, requests must include a valid API key.
    """

    def __init__(self):
        self._keys: Dict[str, ApiKey] = {}
        self._rate_limits: Dict[str, RateLimitEntry] = {}
        self._mode = os.environ.get("NEXUSOS_AUTH_MODE", "open")

        # Register default development key if in open mode
        if self._mode == "open":
            self._register_dev_key()

    def _register_dev_key(self) -> None:
        """Register a default development API key."""
        dev_key = os.environ.get("NEXUSOS_DEV_KEY", "nexus-dev-key-local")
        key_hash = hashlib.sha256(dev_key.encode()).hexdigest()
        self._keys[key_hash] = ApiKey(
            key_hash=key_hash,
            name="Development Key",
            owner="local",
            created_at="2026-01-01T00:00:00Z",
            tier="enterprise",
            rate_limit_per_minute=1000,
            monthly_quota=999999,
        )

    def register_key(
        self,
        key: str,
        name: str,
        owner: str,
        created_at: str,
        tier: str = "starter",
    ) -> ApiKey:
        """Register a new API key.

        Args:
            key: The plaintext API key (will be hashed for storage).
            name: Human-readable key name.
            owner: Key owner identifier.
            created_at: ISO timestamp.
            tier: Pricing tier.

        Returns:
            The created ApiKey record (with hashed key).
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        limits = {
            "starter": (10, 100),
            "professional": (60, 1000),
            "enterprise": (300, 999999),
        }
        rate, quota = limits.get(tier, (10, 100))

        api_key = ApiKey(
            key_hash=key_hash,
            name=name,
            owner=owner,
            created_at=created_at,
            tier=tier,
            rate_limit_per_minute=rate,
            monthly_quota=quota,
        )
        self._keys[key_hash] = api_key
        return api_key

    def authenticate(self, authorization: Optional[str]) -> Tuple[bool, Optional[ApiKey], str]:
        """Authenticate a request.

        Args:
            authorization: The Authorization header value.

        Returns:
            Tuple of (authenticated, api_key, error_message).
        """
        # Open mode: allow all requests
        if self._mode == "open":
            # Still track if a key is provided
            if authorization and authorization.startswith("Bearer "):
                token = authorization[7:]
                key_hash = hashlib.sha256(token.encode()).hexdigest()
                api_key = self._keys.get(key_hash)
                if api_key:
                    return True, api_key, ""
            # In open mode, allow without key
            return True, None, ""

        # Production mode: require valid key
        if not authorization:
            return False, None, "Missing Authorization header"

        if not authorization.startswith("Bearer "):
            return False, None, "Invalid Authorization format (use Bearer token)"

        token = authorization[7:]
        key_hash = hashlib.sha256(token.encode()).hexdigest()
        api_key = self._keys.get(key_hash)

        if api_key is None:
            return False, None, "Invalid API key"

        if not api_key.active:
            return False, None, "API key is deactivated"

        return True, api_key, ""

    def check_rate_limit(self, api_key: Optional[ApiKey]) -> Tuple[bool, str]:
        """Check if a request is within rate limits.

        Args:
            api_key: The authenticated API key (None in open mode).

        Returns:
            Tuple of (allowed, error_message).
        """
        if api_key is None:
            return True, ""  # No rate limit in open mode without key

        now = time.time()
        key_id = api_key.key_hash[:16]

        # Get or create rate limit entry
        if key_id not in self._rate_limits:
            self._rate_limits[key_id] = RateLimitEntry()

        entry = self._rate_limits[key_id]

        # Remove timestamps older than 60 seconds
        cutoff = now - 60
        entry.timestamps = [t for t in entry.timestamps if t > cutoff]

        # Check rate limit
        if len(entry.timestamps) >= api_key.rate_limit_per_minute:
            return False, f"Rate limit exceeded ({api_key.rate_limit_per_minute}/min)"

        # Check monthly quota
        if api_key.usage_this_month >= api_key.monthly_quota:
            return False, "Monthly quota exceeded"

        # Record this request
        entry.timestamps.append(now)
        api_key.usage_this_month += 1

        return True, ""

    def get_usage(self, api_key: ApiKey) -> Dict:
        """Get usage statistics for an API key."""
        return {
            "key_name": api_key.name,
            "tier": api_key.tier,
            "usage_this_month": api_key.usage_this_month,
            "monthly_quota": api_key.monthly_quota,
            "rate_limit_per_minute": api_key.rate_limit_per_minute,
            "remaining_quota": api_key.monthly_quota - api_key.usage_this_month,
        }

    @property
    def mode(self) -> str:
        """Current authentication mode."""
        return self._mode

    @property
    def key_count(self) -> int:
        """Number of registered API keys."""
        return len(self._keys)
