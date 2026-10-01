from app.database import SessionLocal
from app.models.player import Player
from app.models.fixture import Fixture


def get_upcoming_fixtures(player_id, current_gameweek, limit=5):
    db = SessionLocal()

    try:
        player = (
            db.query(Player)
            .filter(Player.id == player_id)
            .first()
        )

        if not player:
            return {
                "error": "Player not found"
            }

        upcoming_fixtures = (
            db.query(Fixture)
            .filter(
                Fixture.gameweek > current_gameweek,
                (
                    (Fixture.home_team_id == player.team_id)
                    | (Fixture.away_team_id == player.team_id)
                )
            )
            .order_by(Fixture.fixture_date.asc())
            .limit(limit)
            .all()
        )

        results = []

        for fixture in upcoming_fixtures:
            is_home = fixture.home_team_id == player.team_id

            if is_home:
                opponent = fixture.away_team.name
            else:
                opponent = fixture.home_team.name

            results.append({
                "fixture_id": fixture.id,
                "gameweek": fixture.gameweek,
                "fixture_date": fixture.fixture_date,
                "opponent": opponent,
                "home": is_home,
                "status": fixture.status
            })

        return results

    finally:
        db.close()