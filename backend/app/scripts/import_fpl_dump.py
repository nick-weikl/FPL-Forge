"""Preview by default. Apply archived official JSON atomically with --apply."""

import argparse
import json

from app.database import SessionLocal
from app.services.fpl_import_service import import_archive
from sqlalchemy import text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    parser.add_argument("--through-gameweek", type=int, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as db:
        with db.begin():
            if db.bind.dialect.name == "postgresql":
                db.execute(text("SET LOCAL lock_timeout = '5s'"))
                if args.apply:
                    db.execute(text("SELECT pg_advisory_xact_lock(763410022)"))
                else:
                    db.execute(text("SET TRANSACTION READ ONLY"))
            result = import_archive(db, args.directory, args.through_gameweek, args.apply)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
