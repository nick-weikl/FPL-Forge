import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
import unittest
from unittest.mock import MagicMock, patch

from app.database import get_db
from app.routes.players import router
from fastapi import FastAPI
from fastapi.testclient import TestClient


class PublicQueryTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)

    def test_summary_passes_requested_gameweek_and_session(self):
        with patch("app.routes.players.get_player_summary", return_value={"ok": True}) as summary:
            response = self.client.get("/api/players/1/summary?current_gameweek=7")
        self.assertEqual(response.status_code, 200)
        summary.assert_called_once_with(1, 7, db=self.db)

    def test_unbounded_history_queries_are_rejected(self):
        for query in [
            "current_gameweek=0",
            "current_gameweek=39",
            "current_gameweek=7&recent_matches=99999",
            "current_gameweek=7&fixture_limit=-1",
        ]:
            self.assertEqual(self.client.get("/api/players/1/analytics?" + query).status_code, 422)
