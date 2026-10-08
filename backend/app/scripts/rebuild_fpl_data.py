import argparse
import json

from sqlalchemy import text

from app.database import engine, SessionLocal
from app.services.fpl_price_service import (
    FPL_SEASON,
    get_fpl_bootstrap,
    get_fpl_players
)
from app.services.team_service import sync_premier_league_teams
from app.services.player_service import sync_premier_league_players


TABLES = (
    "player_match_stats",
    "fixtures",
    "players",
    "teams"
)

SCHEMA_CHANGES = (
    """
    ALTER TABLE players
    ALTER COLUMN external_api_id DROP NOT NULL
    """,
    """
    ALTER TABLE teams
    ALTER COLUMN external_api_id DROP NOT NULL
    """,
    """
    ALTER TABLE teams
        ADD COLUMN IF NOT EXISTS fpl_team_id INTEGER,
        ADD COLUMN IF NOT EXISTS fpl_season VARCHAR(7)
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_teams_fpl_season_id
    ON teams (fpl_season, fpl_team_id)
    """,
    """
    ALTER TABLE fixtures
    ADD COLUMN IF NOT EXISTS season INTEGER
    """
)


def get_counts(connection):
    # Table names come only from the fixed TABLES list.
    return {
        table: connection.execute(
            text(f"SELECT COUNT(*) FROM {table}")
        ).scalar_one()
        for table in TABLES
    }


def rebuild_fpl_data(apply=False):
    if engine.dialect.name != "postgresql":
        raise RuntimeError("This script requires PostgreSQL")

    # Fetch and validate the replacement roster before any writes.
    data = get_fpl_bootstrap()
    players = get_fpl_players(data)

    team_ids = {
        team["id"]
        for team in data["teams"]
    }

    if len(data["teams"]) != 20 or len(team_ids) != 20:
        raise ValueError("Expected 20 distinct FPL clubs")

    if not players:
        raise ValueError("FPL returned an empty player roster")

    with engine.connect() as connection:
        database = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()
        before = get_counts(connection)

    preview = {
        "database": database,
        "season": FPL_SEASON,
        "existing_rows_to_clear": before,
        "replacement_teams": len(team_ids),
        "replacement_players": len(players)
    }

    if not apply:
        return {"mode": "preview", **preview}

    db = SessionLocal()

    try:
        with db.begin():
            db.execute(text("SET LOCAL lock_timeout = '5s'"))

            for statement in SCHEMA_CHANGES:
                db.execute(text(statement))

            # Explicitly reset only these four tables.
            # Preserve sequences so old IDs aren't immediately reused.
            db.execute(text("""
                TRUNCATE TABLE
                    ONLY player_match_stats,
                    ONLY fixtures,
                    ONLY players,
                    ONLY teams
                CONTINUE IDENTITY RESTRICT
            """))

            db.execute(text("""
                ALTER TABLE fixtures
                ALTER COLUMN season SET NOT NULL
            """))

            db.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_fixtures_season
                ON fixtures (season)
            """))

            team_result = sync_premier_league_teams(
                data=data,
                db=db
            )

            player_result = sync_premier_league_players(
                data=data,
                db=db
            )

            after = get_counts(db)

            if (
                after["teams"] != len(team_ids)
                or after["players"] != len(players)
            ):
                raise ValueError(
                    "Imported counts do not match the FPL roster"
                )

        return {
            "mode": "applied",
            **preview,
            "teams": team_result,
            "players": player_result,
            "final_counts": after
        }

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Clear old data, update schema and import the FPL roster"
    )
    args = parser.parse_args()

    result = rebuild_fpl_data(apply=args.apply)
    print(json.dumps(result, indent=2))