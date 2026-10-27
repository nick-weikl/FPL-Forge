"""Run explicitly: python -m app.scripts.migrate [--check]. Never runs on import."""

import argparse
import hashlib
from pathlib import Path

from app.database import engine
from app.migrations import MIGRATIONS
from sqlalchemy import inspect, text


def migrate(check=False):
    if engine.dialect.name != "postgresql":
        raise RuntimeError("Production migrations require PostgreSQL")
    with engine.begin() as connection:
        if not check:
            connection.execute(text("SET LOCAL lock_timeout = '5s'"))
            connection.execute(text("SELECT pg_advisory_xact_lock(763410021)"))
            connection.execute(
                text("""CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY, checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
            )
        applied = {}
        if inspect(connection).has_table("schema_migrations"):
            applied = dict(
                connection.execute(text("SELECT version, checksum FROM schema_migrations")).all()
            )
        unknown = sorted(applied.keys() - {version for version, _ in MIGRATIONS})
        if unknown:
            raise RuntimeError(
                f"Database contains migrations unknown to this release: {', '.join(unknown)}"
            )
        pending = []
        for version, module in MIGRATIONS:
            checksum = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
            if version in applied:
                if checksum != applied[version]:
                    raise RuntimeError(f"Applied migration checksum changed: {version}")
                continue
            pending.append(version)
            if not check:
                module.upgrade(connection)
                connection.execute(
                    text("INSERT INTO schema_migrations(version,checksum) VALUES (:v,:c)"),
                    {"v": version, "c": checksum},
                )
        return {"pending" if check else "applied": pending}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    print(migrate(parser.parse_args().check))
