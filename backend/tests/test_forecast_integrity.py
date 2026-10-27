import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.database import Base
from app.models import Fixture, Player, Team
from app.models.fpl_data import FPLImport, FPLMatchStat
from app.services.data_quality_service import get_data_quality
from app.services.fpl_forecast_service import build_forecasts
from app.services.recommendation_service import prepare_context
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

NOW = datetime(2026, 10, 27, 12, tzinfo=timezone.utc)


class ForecastIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([Team(id=i, name=f"Club {i}") for i in range(1, 5)])
        self.db.add(
            Player(
                id=1,
                name="Transferred player",
                team_id=2,
                position="Midfielder",
                fpl_season="2026/27",
                price_tenths=50,
                availability_status="a",
                price_updated_at=NOW,
            )
        )
        for gw in [1, 2]:
            self.db.add(
                FPLImport(
                    season=2026,
                    gameweek=gw,
                    source_sha256="0" * 64,
                    observed_at=NOW,
                    player_count=1,
                    fixture_count=2,
                )
            )
        for fid, gw, home, away, status in [
            (1, 1, 1, 3, "FT"),
            (2, 2, 1, 4, "FT"),
            (3, 1, 2, 4, "FT"),
            (4, 2, 2, 3, "FT"),
            (5, 2, 4, 2, "FT"),
            (6, 3, 3, 2, "NS"),
            (7, 3, 2, 1, "NS"),
        ]:
            self.db.add(
                Fixture(
                    id=fid,
                    external_api_id=fid,
                    season=2026,
                    gameweek=gw,
                    home_team_id=home,
                    away_team_id=away,
                    status=status,
                    fixture_date=NOW.replace(tzinfo=None),
                )
            )
        self.db.flush()
        for fid, team, minutes, points in [(1, 1, 90, 8), (2, None, 0, 0)]:
            self.db.add(
                FPLMatchStat(
                    player_id=1,
                    fixture_id=fid,
                    team_id=team,
                    minutes=minutes,
                    total_points=points,
                    stats={},
                    observed_at=NOW,
                )
            )
        self.db.commit()
        self.clocks = [
            patch(f"app.services.{module}.datetime", wraps=datetime)
            for module in ["fpl_forecast_service", "data_quality_service"]
        ]
        self.mock_clocks = [clock.start() for clock in self.clocks]
        self.set_time(NOW)

    def set_time(self, value):
        for clock in self.mock_clocks:
            clock.now.return_value = value

    def tearDown(self):
        for clock in self.clocks:
            clock.stop()
        self.db.close()
        self.engine.dispose()

    def test_transfer_uses_player_fixture_history_and_recorded_dnp(self):
        result = build_forecasts(self.db, 2)
        player = result["by_id"][1]
        # 8 / 2 recorded opportunities * 2 upcoming, not 8 / 3 current-club fixtures.
        self.assertEqual(player["expected_points"], 8)
        self.assertEqual(player["observed_matches"], 2)
        self.assertEqual(player["gameweek_points"], {3: 8, 4: 0, 5: 0, 6: 0, 7: 0})
        self.assertTrue(player["can_buy"])
        self.assertEqual(result["model"], "recent_fpl_points_baseline_v2")

    def test_missing_record_is_unknown_not_a_confirmed_dnp(self):
        self.db.query(FPLMatchStat).filter(FPLMatchStat.fixture_id == 2).delete()
        self.db.commit()
        self.assertEqual(build_forecasts(self.db, 2)["by_id"][1]["expected_points"], 16)
        self.db.query(FPLMatchStat).delete()
        self.db.commit()
        self.assertNotIn(1, build_forecasts(self.db, 2)["by_id"])

    def test_price_boundary_missing_invalid_and_future_dates(self):
        player = self.db.get(Player, 1)
        for age, eligible in [
            (timedelta(days=7), True),
            (timedelta(days=7, seconds=1), False),
            (timedelta(seconds=-1), False),
            (None, False),
        ]:
            with self.subTest(age=age):
                player.price_updated_at = None if age is None else NOW - age
                self.db.commit()
                result = build_forecasts(self.db, 2)
                self.assertEqual(result["by_id"][1]["can_buy"], eligible)
                self.assertEqual(
                    result["data_quality"]["unusable_price_players"], int(not eligible)
                )
        player.price_updated_at = NOW
        player.price_tenths = 0
        self.db.commit()
        self.assertFalse(build_forecasts(self.db, 2)["by_id"][1]["can_buy"])

    def test_partial_stale_pool_warns_and_keeps_fresh_candidates(self):
        self.db.add(
            Player(
                id=2,
                name="Stale player",
                team_id=1,
                position="Midfielder",
                fpl_season="2026/27",
                price_tenths=50,
                availability_status="a",
                price_updated_at=NOW - timedelta(days=8),
            )
        )
        self.db.add(
            FPLMatchStat(
                player_id=2,
                fixture_id=1,
                team_id=1,
                minutes=90,
                total_points=10,
                stats={},
                observed_at=NOW,
            )
        )
        self.db.commit()
        result = build_forecasts(self.db, 2)
        self.assertTrue(result["by_id"][1]["can_buy"])
        self.assertFalse(result["by_id"][2]["can_buy"])
        self.assertTrue(any("excluded from incoming" in w for w in result["warnings"]))

    def test_all_stale_prices_block_a_misleading_hold(self):
        self.set_time(NOW + timedelta(days=8))
        with (
            patch(
                "app.services.recommendation_service.validate_squad", return_value={"valid": True}
            ),
            patch("app.services.recommendation_service.SessionLocal", return_value=self.db),
        ):
            result = prepare_context(2, [1], 0)
        self.assertIn("no incoming players", result["error"])
        self.assertNotIn("recommended_strategy", result)
        self.assertEqual(result["data_quality"]["unusable_price_players"], 1)

    def test_past_unfinished_fixture_warning(self):
        self.set_time(NOW + timedelta(hours=4))
        result = get_data_quality(self.db)
        self.assertEqual(result["past_unfinished_fixtures"], 2)
        self.assertTrue(any("lack a final status" in w for w in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
