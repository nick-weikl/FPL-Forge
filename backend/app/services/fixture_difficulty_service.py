from app.database import SessionLocal
from app.models.fixture import Fixture


def get_team_strength(team_id, current_gameweek):
    db = SessionLocal()

    try:
        fixtures = (
            db.query(Fixture)
            .filter(
                Fixture.status == "FT",
                (Fixture.home_team_id == team_id)
                | (Fixture.away_team_id == team_id),
                Fixture.gameweek <= current_gameweek
            )
            .order_by(Fixture.gameweek.desc())
            .all()
        )

        if not fixtures:
            return {
                "error": "No matches found for the team"
            }

        matches_played = 0
        total_goals_scored = 0
        total_goals_conceded = 0

        for fixture in fixtures:
            home_score = fixture.home_score or 0
            away_score = fixture.away_score or 0

            if fixture.home_team_id == team_id:
                total_goals_scored += home_score
                total_goals_conceded += away_score
            else:
                total_goals_scored += away_score
                total_goals_conceded += home_score

            matches_played += 1

        average_goals_scored = (
            total_goals_scored / matches_played
        )

        average_goals_conceded = (
            total_goals_conceded / matches_played
        )

        return {
            "team_id": team_id,
            "matches_played": matches_played,
            "total_goals_scored": total_goals_scored,
            "total_goals_conceded": total_goals_conceded,
            "goals_scored_per_match": round(
                average_goals_scored, 2
            ),
            "goals_conceded_per_match": round(
                average_goals_conceded, 2
            )
        }

    finally:
        db.close()