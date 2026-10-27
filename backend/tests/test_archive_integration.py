"""Optional integration against a locally downloaded official archive."""

import json
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
import unittest
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from app.database import Base
from app.models import Fixture, Player, Team
from app.models.fpl_data import FPLMatchStat, PlayerPriceSnapshot
from app.services.fpl_forecast_service import build_forecasts
from app.services.fpl_import_service import import_archive, load_archive
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

ARCHIVE = Path(__file__).resolve().parents[1] / "data/fpl/2026-27"


@unittest.skipUnless(
    (ARCHIVE / "manifest.json").exists(), "Download the official archive to run this integration"
)
class ArchiveIntegrationTests(unittest.TestCase):
    def test_full_archive_is_atomic_idempotent_and_forecasts(self):
        payloads, _, observed_at = load_archive(ARCHIVE, 7)
        # Archive tests must remain reproducible after the stored prices expire.
        clocks = []
        for module in ["fpl_forecast_service", "data_quality_service"]:
            clock = patch(f"app.services.{module}.datetime", wraps=datetime)
            mocked = clock.start()
            self.addCleanup(clock.stop)
            mocked.now.return_value = observed_at + timedelta(seconds=1)
            clocks.append(mocked)
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            for t in payloads["bootstrap"]["teams"]:
                db.add(Team(id=t["id"], name=t["name"], fpl_team_id=t["id"], fpl_season="2026/27"))
            for f in payloads["fixtures"]:
                db.add(
                    Fixture(
                        id=f["id"],
                        external_api_id=f["id"],
                        home_team_id=f["team_h"],
                        away_team_id=f["team_a"],
                        fixture_date=datetime(2026, 8, 21),
                        season=2026,
                        gameweek=f["event"],
                        status="NS",
                    )
                )
            db.commit()
            preview = import_archive(db, ARCHIVE, 7)
            self.assertEqual(preview["gameweek_6_finished"], 10)
            self.assertEqual(db.scalar(select(func.count()).select_from(Player)), 0)
            result = import_archive(db, ARCHIVE, 7, True)
            db.commit()
            stored_count = db.scalar(select(func.count()).select_from(FPLMatchStat))
            self.assertEqual(stored_count, result["official_stat_rows"])
            self.assertEqual(db.scalar(select(func.count()).select_from(Player)), 668)
            for gw in [1, 6, 7]:
                forecast = build_forecasts(db, gw)
                self.assertNotIn("error", forecast)
                self.assertGreater(len(forecast["by_id"]), 0)
            self.assertEqual(
                db.scalar(
                    select(func.sum(FPLMatchStat.total_points))
                    .join(Fixture)
                    .where(Fixture.gameweek == 6)
                ),
                sum(p["stats"]["total_points"] for p in payloads["event-6"]["elements"]),
            )
            from app.database import get_db
            from fastapi.testclient import TestClient

            # Importing the HTTP app must never create or alter tables.
            with patch.object(
                Base.metadata, "create_all", side_effect=AssertionError("HTTP import attempted DDL")
            ):
                from app.main import app
            factory = sessionmaker(engine)

            def dependency():
                with factory() as request_db:
                    yield request_db

            app.dependency_overrides[get_db] = dependency
            forecast = build_forecasts(db, 7)
            owned = []
            clubs = Counter()
            for position, count in [
                ("Goalkeeper", 2),
                ("Defender", 5),
                ("Midfielder", 5),
                ("Attacker", 3),
            ]:
                for player in reversed(forecast["rankings"][position]):
                    if clubs[player["team_id"]] < 3:
                        owned.append(player["player_id"])
                        clubs[player["team_id"]] += 1
                        count -= 1
                    if not count:
                        break
            try:
                with (
                    patch("app.services.recommendation_service.SessionLocal", factory),
                    patch("app.services.squad_service.SessionLocal", factory),
                ):
                    client = TestClient(app)
                    self.assertEqual(client.get("/api/players").status_code, 200)
                    self.assertEqual(
                        client.get("/api/data-quality").json()["official_fpl_through_gameweek"], 7
                    )
                    self.assertEqual(
                        client.post(
                            "/api/recommendations/strategy",
                            json={"current_gameweek": -1, "owned_player_ids": []},
                        ).status_code,
                        422,
                    )
                    response = client.post(
                        "/api/recommendations/strategy",
                        json={
                            "current_gameweek": 7,
                            "owned_player_ids": owned,
                            "free_transfers": 1,
                            "bank_tenths": 10,
                            "starting_player_ids": [
                                owned[i] for i in [0, 2, 3, 4, 7, 8, 9, 10, 12, 13, 14]
                            ],
                            "bench_player_ids": [owned[i] for i in [1, 5, 6, 11]],
                            "captain_id": owned[12],
                            "vice_captain_id": owned[13],
                        },
                    )
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual(response.json()["score_units"], "expected_fpl_points")
                    for clock in clocks:
                        clock.now.return_value = observed_at + timedelta(days=8)
                    stale = client.post(
                        "/api/recommendations/strategy", json=json.loads(response.request.content)
                    )
                    self.assertEqual(stale.status_code, 400, stale.text)
                    self.assertIn("no incoming players", stale.json()["detail"]["error"])
                    self.assertNotIn("recommended_strategy", stale.json()["detail"])
            finally:
                app.dependency_overrides.clear()
            import_archive(db, ARCHIVE, 7, True)
            db.commit()
            self.assertEqual(
                db.scalar(select(func.count()).select_from(FPLMatchStat)), stored_count
            )
            self.assertEqual(db.scalar(select(func.count()).select_from(PlayerPriceSnapshot)), 668)
        engine.dispose()
