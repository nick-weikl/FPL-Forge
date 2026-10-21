"""Add official FPL history, price provenance and season-safe identities."""
from sqlalchemy import text
from app.database import Base
import app.models  # Register all mapped tables.

STATEMENTS = (
    'ALTER TABLE players ADD COLUMN IF NOT EXISTS price_updated_at TIMESTAMPTZ',
    'ALTER TABLE players ADD COLUMN IF NOT EXISTS availability_status VARCHAR(10)',
    'ALTER TABLE players ADD COLUMN IF NOT EXISTS chance_of_playing INTEGER',
    'ALTER TABLE fixtures ADD COLUMN IF NOT EXISTS fpl_fixture_id INTEGER',
    'ALTER TABLE player_match_stats ADD COLUMN IF NOT EXISTS team_id INTEGER REFERENCES teams(id)',
    'ALTER TABLE teams DROP CONSTRAINT IF EXISTS teams_name_key',
    'ALTER TABLE teams DROP CONSTRAINT IF EXISTS teams_external_api_id_key',
    'ALTER TABLE players DROP CONSTRAINT IF EXISTS players_external_api_id_key',
    'CREATE UNIQUE INDEX IF NOT EXISTS uq_teams_name_season ON teams (fpl_season, name)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uq_teams_api_season_id ON teams (fpl_season, external_api_id)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uq_players_api_season_id ON players (fpl_season, external_api_id)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uq_fixtures_fpl_season_id ON fixtures (season, fpl_fixture_id)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uq_fixtures_season_pair ON fixtures (season, home_team_id, away_team_id)',
    'CREATE INDEX IF NOT EXISTS ix_player_match_stats_fixture_id ON player_match_stats (fixture_id)',
)


def upgrade(connection):
    # Explicit migration command also supports an empty database.
    Base.metadata.create_all(connection)
    for statement in STATEMENTS:
        connection.execute(text(statement))
