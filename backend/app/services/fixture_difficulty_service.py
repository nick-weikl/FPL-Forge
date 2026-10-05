from app.database import SessionLocal
from app.models.fixture import Fixture
from app.models.team import Team


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


def get_all_team_strengths(current_gameweek):
    db = SessionLocal()

    try:
        teams = (
            db.query(Team)
            .order_by(Team.id.asc())
            .all()
        )

        team_strengths = []

        for team in teams:
            strength = get_team_strength(
                team.id,
                current_gameweek
            )

            if "error" not in strength:
                team_strengths.append(strength)

        return team_strengths

    finally:
        db.close()


def get_fixture_difficulty(opponent_team_id, player_position, current_gameweek):
    team_strengths = get_all_team_strengths(current_gameweek)

    opponent_strength = next(
        (
            team
            for team in team_strengths
            if team["team_id"] == opponent_team_id
        ),
        None
    )

    if not opponent_strength:
        return {
            "error": "Opponent team strength not found"
        }

    if player_position in ["GK", "DEF"]:
        attack_values = [
            team["goals_scored_per_match"]
            for team in team_strengths
        ]

        min_attack = min(attack_values)
        max_attack = max(attack_values)

        opponent_attack = (
            opponent_strength["goals_scored_per_match"]
        )

        if max_attack == min_attack:
            normalized_attack = 0.5
        else:
            normalized_attack = (
                opponent_attack - min_attack
            ) / (
                max_attack - min_attack
            )

        difficulty_score = 1 + (normalized_attack * 4)


    elif player_position in ["MID", "FWD"]:
        conceded_values = [
            team["goals_conceded_per_match"]
            for team in team_strengths
        ]

        min_conceded = min(conceded_values)
        max_conceded = max(conceded_values)

        opponent_conceded = (
            opponent_strength["goals_conceded_per_match"]
        )

        if max_conceded == min_conceded:
            normalized_conceded = 0.5
        else:
            normalized_conceded = (
                opponent_conceded - min_conceded
            ) / (
                max_conceded - min_conceded
            )

        normalized_defensive_difficulty = (1 - normalized_conceded)

        difficulty_score = 1 + (normalized_defensive_difficulty * 4)


    else:
        return {
            "error": "Invalid player position"
        }

    return {
        "opponent_team_id": opponent_team_id,
        "player_position": player_position,
        "difficulty_score": round(difficulty_score, 2),
        "opponent_goals_scored_per_match":
            opponent_strength["goals_scored_per_match"],
        "opponent_goals_conceded_per_match":
            opponent_strength["goals_conceded_per_match"]
    }