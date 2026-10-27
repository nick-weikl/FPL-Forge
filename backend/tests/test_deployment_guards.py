import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch

from app.config import Settings
from app.database import Base, get_db
from app.main import create_app
from app.migrations import v001
from app.models.fpl_data import FPLMatchStat
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def settings(**changes):
    values = dict(
        environment="test",
        origins=("https://app.example.com",),
        allowed_hosts=("testserver",),
        admin_sync=False,
        admin_token="",
        requests_per_minute=120,
    )
    return Settings(**(values | changes))


class DeploymentGuardTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(settings())
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_sync_is_disabled_without_operator_configuration(self):
        for path in [
            "/sync/teams",
            "/sync/players",
            "/sync/fixtures",
            "/sync/player-fixture-stats/batch",
            "/api/fixtures/1/sync-player-stats",
        ]:
            response = self.client.post(path)
            self.assertEqual(response.status_code, 404, path)

    def test_enabled_sync_requires_secret_and_never_runs_before_authorization(self):
        app = create_app(settings(admin_sync=True, admin_token="x" * 32))
        client = TestClient(app)
        with patch("app.routes.sync.sync_premier_league_teams", return_value={"ok": True}) as sync:
            self.assertEqual(client.post("/sync/teams").status_code, 403)
            self.assertEqual(
                client.post("/sync/teams", headers={"X-Admin-Token": "wrong"}).status_code, 403
            )
            self.assertEqual(
                client.post("/sync/teams", headers=[(b"X-Admin-Token", b"\xff")]).status_code, 403
            )
            sync.assert_not_called()
            self.assertEqual(
                client.post("/sync/teams", headers={"X-Admin-Token": "x" * 32}).status_code, 200
            )
            sync.assert_called_once()

    def test_public_debug_provider_calls_are_removed(self):
        for path in ["/api-test", "/db-test"]:
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_production_docs_disabled_and_hosts_checked(self):
        client = TestClient(create_app(settings(environment="production")))
        self.assertEqual(client.get("/docs").status_code, 404)
        self.assertEqual(client.get("/openapi.json").status_code, 404)
        self.assertEqual(
            client.get("/health/live", headers={"host": "evil.example"}).status_code, 400
        )

    def test_rate_limit_has_retry_hint_and_bounded_body(self):
        client = TestClient(create_app(settings(requests_per_minute=2)))
        self.assertEqual(client.get("/api/not-a-route").status_code, 404)
        self.assertEqual(client.get("/api/not-a-route").status_code, 404)
        response = client.get("/api/not-a-route")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["retry-after"], "60")
        response = self.client.post(
            "/api/squads/validate",
            content=b"x" * 65537,
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.status_code, 413)
        # A generator omits Content-Length; streaming payloads must be limited too.
        response = self.client.post(
            "/api/squads/validate", content=(b"x" * 40000 for _ in range(2))
        )
        self.assertEqual(response.status_code, 413)

    def test_cors_uses_allowlist_and_api_responses_are_not_cached(self):
        accepted = self.client.options(
            "/api/dashboard",
            headers={"Origin": "https://app.example.com", "Access-Control-Request-Method": "GET"},
        )
        self.assertEqual(
            accepted.headers.get("access-control-allow-origin"), "https://app.example.com"
        )
        rejected = self.client.options(
            "/api/dashboard",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
        )
        self.assertNotIn("access-control-allow-origin", rejected.headers)
        response = self.client.get("/health/live")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(len(response.headers["x-request-id"]), 32)

    def test_internal_errors_return_reference_without_exception_details(self):
        @self.app.get("/test-error")
        def error():
            raise RuntimeError("PRIVATE_DATABASE_DETAIL")

        with self.assertLogs("fpl_forge", level="ERROR"):
            response = self.client.get("/test-error")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("PRIVATE_DATABASE_DETAIL", response.text)
        self.assertIn(response.headers["x-request-id"], response.text)

    def test_readiness_queries_schema_and_returns_safe_failure(self):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        factory = sessionmaker(bind=engine)

        def dependency():
            with factory() as db:
                yield db

        self.app.dependency_overrides[get_db] = dependency
        with self.assertLogs("fpl_forge", level="WARNING"):
            self.assertEqual(self.client.get("/health/ready").status_code, 503)
        Base.metadata.create_all(engine)
        self.assertEqual(self.client.get("/health/ready").json(), {"status": "ready"})
        FPLMatchStat.__table__.drop(engine)
        with self.assertLogs("fpl_forge", level="WARNING"):
            self.assertEqual(self.client.get("/health/ready").status_code, 503)
        self.assertEqual(self.client.get("/health/live").status_code, 200)
        engine.dispose()

    def test_production_readiness_requires_matching_migration_ledger(self):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(engine)
        factory = sessionmaker(bind=engine)
        app = create_app(settings(environment="production"))

        def dependency():
            with factory() as db:
                yield db

        app.dependency_overrides[get_db] = dependency
        client = TestClient(app)
        with self.assertLogs("fpl_forge", level="WARNING"):
            self.assertEqual(client.get("/health/ready").status_code, 503)
        checksum = hashlib.sha256(Path(v001.__file__).read_bytes()).hexdigest()
        with engine.begin() as connection:
            connection.execute(
                text("CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, checksum TEXT)")
            )
            connection.execute(
                text("INSERT INTO schema_migrations VALUES (:v, :c)"),
                {"v": "001_fpl_history", "c": checksum},
            )
        self.assertEqual(client.get("/health/ready").status_code, 200)
        with engine.begin() as connection:
            connection.execute(text("UPDATE schema_migrations SET checksum = 'modified'"))
        with self.assertLogs("fpl_forge", level="WARNING"):
            response = client.get("/health/ready")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotIn("modified", response.text)
        engine.dispose()

    def test_production_configuration_fails_closed(self):
        with patch.dict(
            os.environ,
            {"APP_ENV": "production", "ALLOWED_HOSTS": "", "CORS_ORIGINS": ""},
            clear=True,
        ):
            with self.assertRaises(RuntimeError):
                Settings.from_env()
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "ALLOWED_HOSTS": "example.com",
                "CORS_ORIGINS": "http://example.com",
            },
            clear=True,
        ):
            with self.assertRaises(RuntimeError):
                Settings.from_env()
        with patch.dict(os.environ, {"ENABLE_ADMIN_SYNC": "true"}, clear=True):
            with self.assertRaises(RuntimeError):
                Settings.from_env()
