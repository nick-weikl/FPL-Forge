import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
import hashlib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.migrations import MIGRATIONS
from app.scripts.migrate import migrate
from sqlalchemy import create_engine, text


class MigrationCheckTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        # Exercise the runner's check logic with an isolated connection. PostgreSQL
        # DDL and advisory locks are tested by the separate real recovery drill.
        self.facade = SimpleNamespace(
            dialect=SimpleNamespace(name="postgresql"), begin=self.engine.begin
        )
        self.version, module = MIGRATIONS[0]
        self.checksum = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
        with self.engine.begin() as connection:
            connection.execute(
                text("CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, checksum TEXT)")
            )

    def tearDown(self):
        self.engine.dispose()

    def add(self, version, checksum):
        with self.engine.begin() as connection:
            connection.execute(
                text("INSERT INTO schema_migrations VALUES (:version,:checksum)"),
                {"version": version, "checksum": checksum},
            )

    def check(self):
        with patch("app.scripts.migrate.engine", self.facade):
            return migrate(check=True)

    def test_pending_is_reported_without_applying(self):
        self.assertEqual(self.check(), {"pending": [self.version]})
        with self.engine.connect() as connection:
            self.assertEqual(connection.scalar(text("SELECT count(*) FROM schema_migrations")), 0)

    def test_matching_migration_needs_no_changes(self):
        self.add(self.version, self.checksum)
        self.assertEqual(self.check(), {"pending": []})

    def test_modified_applied_file_is_rejected(self):
        self.add(self.version, "changed")
        with self.assertRaisesRegex(RuntimeError, "checksum changed"):
            self.check()

    def test_unknown_applied_version_is_rejected(self):
        self.add(self.version, self.checksum)
        self.add("999_future_release", "future")
        with self.assertRaisesRegex(RuntimeError, "unknown to this release"):
            self.check()
