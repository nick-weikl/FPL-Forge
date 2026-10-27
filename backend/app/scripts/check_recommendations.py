"""Read-only PostgreSQL recommendation smoke check. Requires development dependencies.

Run with the existing DATABASE_URL: python -m app.scripts.check_recommendations
Uses a generated legal squad, not a user's private squad. No provider requests.
"""

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.database import engine, get_db
from app.models import Fixture
from app.models.fpl_data import FPLImport
from app.services.fpl_forecast_service import build_forecasts
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker


def check_recommendations():
    if engine.dialect.name != "postgresql":
        raise RuntimeError("This check requires the existing PostgreSQL database")
    readonly = create_engine(
        engine.url,
        connect_args={
            "options": "-c default_transaction_read_only=on -c statement_timeout=30000",
            "connect_timeout": 10,
        },
    )
    factory = sessionmaker(bind=readonly, autoflush=False)
    try:
        with factory() as db:
            assert db.scalar(text("SHOW transaction_read_only")) == "on"
            from app.services.football_api import SEASON

            gw = db.scalar(select(func.max(FPLImport.gameweek)).where(FPLImport.season == SEASON))
            assert gw is not None, "No official imports available"
            forecast = build_forecasts(db, gw)
            assert "error" not in forecast, forecast
            owned, clubs = [], Counter()
            for role, required in [
                ("Goalkeeper", 2),
                ("Defender", 5),
                ("Midfielder", 5),
                ("Attacker", 3),
            ]:
                players = sorted(
                    forecast["rankings"].get(role, []),
                    key=lambda p: (
                        p["price_tenths"] or 10000,
                        p["expected_points"],
                        p["player_id"],
                    ),
                )
                selected = []
                for player in players:
                    if player["price_tenths"] and clubs[player["team_id"]] < 3:
                        selected.append(player["player_id"])
                        clubs[player["team_id"]] += 1
                    if len(selected) == required:
                        break
                assert len(selected) == required, f"Not enough stored players for {role}"
                owned.extend(selected)
            records = forecast["by_id"]
            bank = 10
            assert sum(records[pid]["price_tenths"] for pid in owned) + bank <= 1000
            selling = {pid: records[pid]["price_tenths"] for pid in owned}
            starters = [owned[i] for i in [0, 2, 3, 4, 7, 8, 9, 10, 12, 13, 14]]
            payload = dict(
                current_gameweek=gw,
                owned_player_ids=owned,
                bank_tenths=bank,
                selling_prices_tenths=selling,
                free_transfers=1,
                starting_player_ids=starters,
                bench_player_ids=[owned[i] for i in [1, 5, 6, 11]],
                captain_id=owned[12],
                vice_captain_id=owned[13],
            )
            # Compare the old club denominator with the new recorded-history denominator.
            club_counts = Counter()
            for fixture in db.scalars(
                select(Fixture).where(
                    Fixture.season == SEASON,
                    Fixture.status == "FT",
                    Fixture.gameweek.between(max(1, gw - 4), gw),
                )
            ):
                club_counts.update([fixture.home_team_id, fixture.away_team_id])
            changed_denominators = sum(
                p["observed_matches"] != club_counts[p["team_id"]] for p in records.values()
            )

        from app.main import app

        def dependency():
            with factory() as db:
                yield db

        previous = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = dependency
        try:
            with (
                patch("app.services.recommendation_service.SessionLocal", factory),
                patch("app.services.squad_service.SessionLocal", factory),
                TestClient(app) as client,
            ):
                outcomes = []
                for free in [0, 1, 2]:
                    response = client.post(
                        "/api/recommendations/strategy", json={**payload, "free_transfers": free}
                    )
                    assert response.status_code == 200, response.text
                    result = response.json()
                    baseline = round(
                        sum(
                            records[pid]["expected_points"]
                            * (2 if pid == payload["captain_id"] else 1)
                            for pid in starters
                        ),
                        2,
                    )
                    assert abs(result["baseline"]["before_points"] - baseline) <= 0.01
                    gains = [0]
                    for key, count in [("single_transfer", 1), ("double_transfer", 2)]:
                        plan = result[key]
                        if plan is None:
                            continue
                        moves = (
                            [plan["transfer"]] if count == 1 else plan["transfer_pair"]["transfers"]
                        )
                        incoming = [m["player_in"]["player_id"] for m in moves]
                        outgoing = [m["player_out"]["player_id"] for m in moves]
                        assert len(set(incoming)) == count and not set(incoming) & set(owned)
                        assert all(records[pid]["can_buy"] for pid in incoming)
                        assert all(
                            m["player_in"]["position"] == m["player_out"]["position"] for m in moves
                        )
                        updated = [pid for pid in owned if pid not in outgoing] + incoming
                        assert (
                            max(Counter(records[pid]["team_id"] for pid in updated).values()) <= 3
                        )
                        remaining = (
                            bank
                            + sum(selling[pid] for pid in outgoing)
                            - sum(records[pid]["price_tenths"] for pid in incoming)
                        )
                        option = plan["transfer"] if count == 1 else plan["transfer_pair"]
                        assert remaining >= 0 and option["remaining_bank_tenths"] == remaining
                        hit = max(count - free, 0) * 4
                        expected_gain = round(
                            sum(
                                (
                                    records[m["player_in"]["player_id"]]["expected_points"]
                                    - records[m["player_out"]["player_id"]]["expected_points"]
                                )
                                * (
                                    2
                                    if m["player_out"]["player_id"] == payload["captain_id"]
                                    else 1
                                    if m["player_out"]["player_id"] in starters
                                    else 0
                                )
                                for m in moves
                            ),
                            2,
                        )
                        assert plan["transfer_cost"] == hit
                        assert abs(plan["raw_score_gain"] - expected_gain) <= 0.01
                        assert abs(plan["net_score_gain"] - (expected_gain - hit)) <= 0.01
                        assert (
                            sum(r["transfer_hit"] for r in plan["projection"]["gameweeks"]) == hit
                        )
                        assert abs(plan["projection"]["net_gain"] - plan["net_score_gain"]) <= 0.01
                        gains.append(plan["net_score_gain"])
                    assert result["best_net_score_gain"] == max(gains)
                    outcomes.append(
                        dict(
                            free_transfers=free,
                            strategy=result["recommended_strategy"],
                            net_gain=result["best_net_score_gain"],
                        )
                    )
                missing = client.post(
                    "/api/recommendations/strategy", json={**payload, "current_gameweek": gw + 1}
                )
                assert missing.status_code == 400 and "coverage is incomplete" in missing.text
                future = datetime.now(timezone.utc) + timedelta(days=8)
                with (
                    patch("app.services.fpl_forecast_service.datetime", wraps=datetime) as fc,
                    patch("app.services.data_quality_service.datetime", wraps=datetime) as qc,
                ):
                    fc.now.return_value = qc.now.return_value = future
                    stale = client.post("/api/recommendations/strategy", json=payload)
                    assert stale.status_code == 400 and "no incoming players" in stale.text
                    assert "recommended_strategy" not in stale.json()["detail"]
                print(
                    json.dumps(
                        dict(
                            read_only=True,
                            gameweek=gw,
                            squad_ids=owned,
                            model=forecast["model"],
                            forecast_players=len(records),
                            changed_denominators=changed_denominators,
                            quality=forecast["data_quality"],
                            outcomes=outcomes,
                            missing_coverage_status=missing.status_code,
                            simulated_stale_prices_status=stale.status_code,
                        ),
                        indent=2,
                    )
                )
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous)
    finally:
        readonly.dispose()


if __name__ == "__main__":
    check_recommendations()
