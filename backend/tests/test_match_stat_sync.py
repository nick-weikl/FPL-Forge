"""Exercise both insert and update paths without calling the external API."""

import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite://")

from app.database import Base
from app.models import Fixture, Player, PlayerMatchStat, Team
from app.services import player_match_stat_service as service
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class MatchStatSyncTests(unittest.TestCase):
    def test_insert_and_update_use_the_same_stat_mapping(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        factory = sessionmaker(bind=engine)
        with factory() as db:
            db.add_all(
                [
                    Team(id=1, name="Home", external_api_id=101, fpl_season=service.FPL_SEASON),
                    Team(id=2, name="Away", external_api_id=102, fpl_season=service.FPL_SEASON),
                    Player(
                        id=1,
                        name="Player",
                        team_id=1,
                        external_api_id=201,
                        fpl_season=service.FPL_SEASON,
                    ),
                    Fixture(
                        id=1,
                        external_api_id=301,
                        fixture_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
                        home_team_id=1,
                        away_team_id=2,
                        season=service.SEASON,
                        status="FT",
                    ),
                ]
            )
            db.commit()
        stats = {
            "games": {"rating": "7.4", "minutes": 90},
            "goals": {"total": 1, "assists": None},
            "shots": {"total": 3, "on": 2},
            "passes": {"key": 4},
            "tackles": {"total": 5, "interceptions": 6},
            "cards": {"yellow": 1, "red": None},
        }
        payload = {
            "response": [
                {"team": {"id": 101}, "players": [{"player": {"id": 201}, "statistics": [stats]}]}
            ]
        }
        try:
            with (
                patch.object(service, "SessionLocal", factory),
                patch.object(service, "get_player_match_stats", return_value=payload),
            ):
                self.assertEqual(
                    service.sync_player_match_stats(1), {"added": 1, "updated": 0, "skipped": 0}
                )
                stats["goals"]["total"] = 2
                self.assertEqual(
                    service.sync_player_match_stats(1), {"added": 0, "updated": 1, "skipped": 0}
                )
            with factory() as db:
                row = db.query(PlayerMatchStat).one()
                self.assertEqual(
                    [
                        row.team_id,
                        row.minutes,
                        row.goals,
                        row.assists,
                        row.shots,
                        row.shots_on_target,
                        row.key_passes,
                        row.tackles,
                        row.interceptions,
                        row.yellow_cards,
                        row.red_cards,
                        row.rating,
                    ],
                    [1, 90, 2, 0, 3, 2, 4, 5, 6, 1, 0, 7.4],
                )
        finally:
            engine.dispose()
