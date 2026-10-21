"""Deployment settings. No secrets are returned to clients."""

import os
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    environment: str
    origins: tuple[str, ...]
    allowed_hosts: tuple[str, ...]
    admin_sync: bool
    admin_token: str
    requests_per_minute: int = 120

    @classmethod
    def from_env(cls):
        environment = os.getenv("APP_ENV", "development")
        if environment not in ("development", "test", "production"):
            raise RuntimeError("APP_ENV must be development, test or production")
        production = environment == "production"
        origins = tuple(
            value.strip()
            for value in os.getenv(
                "CORS_ORIGINS", "" if production else "http://localhost:5173,http://127.0.0.1:5173"
            ).split(",")
            if value.strip()
        )
        for origin in origins:
            url = urlsplit(origin)
            if (
                url.scheme not in ("http", "https")
                or not url.hostname
                or url.path
                or url.query
                or url.fragment
                or url.username
                or (production and url.scheme != "https")
            ):
                raise RuntimeError(
                    "CORS_ORIGINS must contain exact origins; production requires HTTPS"
                )
        hosts = tuple(
            value.strip()
            for value in os.getenv("ALLOWED_HOSTS", "" if production else "*").split(",")
            if value.strip()
        )
        if production and (not hosts or "*" in hosts):
            raise RuntimeError("Set explicit ALLOWED_HOSTS for production")
        admin_sync = os.getenv("ENABLE_ADMIN_SYNC", "false").lower() == "true"
        token = os.getenv("ADMIN_SYNC_TOKEN", "")
        if admin_sync and len(token) < 32:
            raise RuntimeError(
                "Enabled admin sync requires an ADMIN_SYNC_TOKEN of at least 32 characters"
            )
        limit = int(os.getenv("REQUESTS_PER_MINUTE", "120"))
        if not 1 <= limit <= 10000:
            raise RuntimeError("REQUESTS_PER_MINUTE must be 1–10000")
        return cls(environment, origins, hosts, admin_sync, token, limit)
