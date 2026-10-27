"""Restore a custom-format backup into a new, explicitly disposable database.

Requires psycopg2 and PostgreSQL client utilities. The admin connection is read from
RECOVERY_ADMIN_DATABASE_URL; credentials are never included in child-process arguments.
This command never overwrites an existing database or uses pg_restore --clean.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import psycopg2
from psycopg2 import extensions, sql
from sqlalchemy.engine import make_url


def restore_backup(backup, database_name, expected_sha256, migrate=False):
    if not re.fullmatch(r"fpl_forge_restore_[a-z0-9_]{1,40}", database_name):
        raise ValueError(
            "Use a disposable name beginning fpl_forge_restore_ (lowercase letters/digits)"
        )
    backup = Path(backup).resolve(strict=True)
    actual_hash = hashlib.sha256(backup.read_bytes()).hexdigest()
    if actual_hash != expected_sha256.lower():
        raise ValueError("Backup SHA-256 does not match the expected value")
    admin = make_url(os.environ["RECOVERY_ADMIN_DATABASE_URL"])
    if admin.get_backend_name() != "postgresql":
        raise ValueError("Recovery requires a PostgreSQL admin URL")
    if database_name == admin.database:
        raise ValueError("Recovery target must differ from the admin connection database")
    target = admin.set(database=database_name)
    # libpq parses and validates every connection option, including SSL settings.
    # A private service file keeps credentials out of argv without discarding query options.
    parameters = extensions.parse_dsn(
        target.set(drivername="postgresql").render_as_string(hide_password=False)
    )
    if any("\n" in str(value) or "\r" in str(value) for value in parameters.values()):
        raise ValueError("Connection parameters must not contain line breaks")
    if "service" in parameters or os.environ.get("PGSERVICE"):
        raise ValueError("Use an expanded admin URL rather than a nested libpq service")
    admin_dsn = admin.set(drivername="postgresql").render_as_string(hide_password=False)
    connection = psycopg2.connect(admin_dsn)
    try:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s", (database_name,))
            if cursor.fetchone():
                raise ValueError("Recovery target already exists; choose another disposable name")
            cursor.execute(
                sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(
                    sql.Identifier(database_name)
                )
            )
    finally:
        connection.close()
    # Retain inherited TLS/client settings; explicit service entries override connection defaults.
    child_env = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix="fpl-forge-restore-") as private:
        service = Path(private) / "pg_service.conf"
        service.write_text(
            "[fpl_forge_recovery]\n"
            + "".join(f"{key}={value}\n" for key, value in parameters.items())
        )
        service.chmod(0o600)
        child_env["PGSERVICEFILE"] = str(service)
        subprocess.run(
            [
                "pg_restore",
                "--no-owner",
                "--no-privileges",
                "--exit-on-error",
                "--single-transaction",
                "--dbname",
                "service=fpl_forge_recovery",
                str(backup),
            ],
            env=child_env,
            check=True,
        )
    child_env.pop("PGSERVICEFILE", None)
    child_env["DATABASE_URL"] = target.render_as_string(hide_password=False)
    backend = Path(__file__).resolve().parents[2] / "backend"
    if migrate:
        subprocess.run(
            [sys.executable, "-m", "app.scripts.migrate", "--check"],
            cwd=backend,
            env=child_env,
            check=True,
        )
        subprocess.run(
            [sys.executable, "-m", "app.scripts.migrate"], cwd=backend, env=child_env, check=True
        )
        subprocess.run(
            [sys.executable, "-m", "app.scripts.migrate", "--check"],
            cwd=backend,
            env=child_env,
            check=True,
        )
    print(
        json.dumps(
            {
                "database": database_name,
                "backup_sha256": actual_hash,
                "migrations_requested": migrate,
                "note": "Target retained for inspection; no automatic deletion.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup", type=Path)
    parser.add_argument("--database-name", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--migrate", action="store_true")
    args = parser.parse_args()
    restore_backup(args.backup, args.database_name, args.expected_sha256, args.migrate)
