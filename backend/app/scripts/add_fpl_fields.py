from sqlalchemy import inspect, text

from app.database import engine


def add_fpl_fields():
    if engine.dialect.name != "postgresql":
        raise RuntimeError(
            "This migration requires PostgreSQL"
        )

    with engine.begin() as connection:
        connection.execute(text("""
            ALTER TABLE players
                ADD COLUMN IF NOT EXISTS
                    fpl_player_id INTEGER,
                ADD COLUMN IF NOT EXISTS
                    fpl_position VARCHAR(20),
                ADD COLUMN IF NOT EXISTS
                    fpl_season VARCHAR(7),
                ADD COLUMN IF NOT EXISTS
                    fpl_price_gameweek INTEGER
        """))

        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS
                uq_players_fpl_season_id
            ON players (fpl_season, fpl_player_id)
        """))

    print("FPL fields added successfully.")

    columns = inspect(engine).get_columns("players")

    for column in columns:
        if column["name"].startswith("fpl_"):
            print(
                f"{column['name']}: {column['type']}"
            )


if __name__ == "__main__":
    add_fpl_fields()