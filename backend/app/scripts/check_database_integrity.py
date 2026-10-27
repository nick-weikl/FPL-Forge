"""Read-only relational/migration integrity and canonical data fingerprints.

Run: python -m app.scripts.check_database_integrity
No provider requests or DDL/DML. Also supports a legacy restored database before migration.
"""

import argparse
import hashlib
import json
from pathlib import Path

from app.database import Base, engine
from app.scripts.migrate import MIGRATIONS
from sqlalchemy import create_engine, inspect, text


def inspect_database():
    if engine.dialect.name != "postgresql":
        raise RuntimeError("This checker requires PostgreSQL")
    readonly = create_engine(
        engine.url,
        isolation_level="REPEATABLE READ",
        connect_args={
            "options": "-c default_transaction_read_only=on -c statement_timeout=30000",
            "connect_timeout": 10,
        },
    )
    try:
        with readonly.connect() as connection:
            assert connection.scalar(text("SHOW transaction_read_only")) == "on"
            connection.execute(text("SET LOCAL TIME ZONE 'UTC'"))
            inspector = inspect(connection)
            tables = sorted(inspector.get_table_names(schema="public"))
            required = {
                table.name: set(table.columns.keys()) for table in Base.metadata.sorted_tables
            }
            required["schema_migrations"] = {"version", "checksum", "applied_at"}
            schema_errors = []
            for table, columns in required.items():
                if table not in tables:
                    schema_errors.append(f"Missing table: {table}")
                    continue
                actual = {
                    column["name"] for column in inspector.get_columns(table, schema="public")
                }
                if columns - actual:
                    schema_errors.append(
                        f"Missing columns in {table}: {', '.join(sorted(columns - actual))}"
                    )
            report = {
                "read_only": True,
                "tables": {},
                "foreign_key_orphans": {},
                "duplicate_unique_keys": {},
                "migration_status": {},
                "integrity_ok": True,
                "schema_errors": schema_errors,
            }
            quote = connection.dialect.identifier_preparer.quote
            for table in tables:
                name = f"public.{quote(table)}"
                rows = (
                    connection.execute(
                        text(
                            f'SELECT row_to_json(t)::text FROM {name} t ORDER BY row_to_json(t)::text COLLATE "C"'
                        )
                    )
                    .scalars()
                    .all()
                )
                digest = hashlib.sha256("\n".join(rows).encode()).hexdigest()
                report["tables"][table] = {"rows": len(rows), "sha256": digest}
                for fk in inspector.get_foreign_keys(table, schema="public"):
                    if not fk.get("referred_table"):
                        continue
                    columns = fk["constrained_columns"]
                    referenced = fk["referred_columns"]
                    matches = " AND ".join(
                        f"child.{quote(a)}=parent.{quote(b)}" for a, b in zip(columns, referenced)
                    )
                    nonnull = " AND ".join(f"child.{quote(a)} IS NOT NULL" for a in columns)
                    target = f"{quote(fk.get('referred_schema') or 'public')}.{quote(fk['referred_table'])}"
                    count = connection.scalar(
                        text(
                            f"SELECT count(*) FROM {name} child WHERE {nonnull} AND NOT EXISTS (SELECT 1 FROM {target} parent WHERE {matches})"
                        )
                    )
                    report["foreign_key_orphans"][f"{table}.{fk['name']}"] = count
                    report["integrity_ok"] &= count == 0
                keys = inspector.get_unique_constraints(table, schema="public")
                keys += [
                    index
                    for index in inspector.get_indexes(table, schema="public")
                    if index.get("unique") and not index.get("duplicates_constraint")
                ]
                for key in keys:
                    columns = key["column_names"]
                    grouped = ", ".join(quote(c) for c in columns)
                    nonnull = " AND ".join(f"{quote(c)} IS NOT NULL" for c in columns)
                    count = connection.scalar(
                        text(
                            f"SELECT count(*) FROM (SELECT {grouped} FROM {name} WHERE {nonnull} GROUP BY {grouped} HAVING count(*)>1) duplicates"
                        )
                    )
                    report["duplicate_unique_keys"][f"{table}.{key['name']}"] = count
                    report["integrity_ok"] &= count == 0
            applied = {}
            if "schema_migrations" in tables and {"version", "checksum"}.issubset(
                {c["name"] for c in inspector.get_columns("schema_migrations", schema="public")}
            ):
                applied = dict(
                    connection.execute(text("SELECT version,checksum FROM schema_migrations")).all()
                )
            expected = {
                version: hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                for version, module in MIGRATIONS
            }
            report["migration_status"] = {
                "pending": sorted(expected.keys() - applied.keys()),
                "unknown": sorted(applied.keys() - expected.keys()),
                "checksum_mismatches": [
                    v for v in expected.keys() & applied.keys() if expected[v] != applied[v]
                ],
            }
            report["integrity_ok"] &= (
                not report["migration_status"]["checksum_mismatches"]
                and not report["migration_status"]["unknown"]
            )
            report["ready_for_application"] = (
                report["integrity_ok"]
                and not report["migration_status"]["pending"]
                and not schema_errors
            )
            print(json.dumps(report, indent=2))
            return report
    finally:
        readonly.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Fail unless required schema and migration ledger match this application",
    )
    args = parser.parse_args()
    result = inspect_database()
    if not result["integrity_ok"] or (args.require_ready and not result["ready_for_application"]):
        raise SystemExit(1)
