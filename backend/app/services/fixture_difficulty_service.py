from app.database import SessionLocal
from app.models.fixture import Fixture
from app.models.team import Team
from app.services.football_api import SEASON
from app.services.fpl_price_service import FPL_SEASON


def get_all_team_strengths(
    current_gameweek,
    db=None
):
    owns_db = db is None

    if owns_db:
        db = SessionLocal()

    try:
        teams = (
            db.query(Team)
            .filter(Team.fpl_season == FPL_SEASON)
            .order_by(Team.id.asc())
            .all()
        )

        fixtures = (
            db.query(Fixture)
            .filter(
                Fixture.status == "FT",
                Fixture.gameweek <= current_gameweek
            )
            .all()
        )

        strength_data = {}

        for team in teams:
            strength_data[team.id] = {
                "team_id": team.id,
                "matches_played": 0,
                "total_goals_scored": 0,
                "total_goals_conceded": 0
            }

        for fixture in fixtures:
            home_score = fixture.home_score or 0
            away_score = fixture.away_score or 0

            home_data = strength_data.get(
                fixture.home_team_id
            )

            away_data = strength_data.get(
                fixture.away_team_id
            )

            if home_data:
                home_data["matches_played"] += 1
                home_data["total_goals_scored"] += home_score
                home_data["total_goals_conceded"] += away_score

            if away_data:
                away_data["matches_played"] += 1
                away_data["total_goals_scored"] += away_score
                away_data["total_goals_conceded"] += home_score

        team_strengths = []

        for data in strength_data.values():
            matches_played = data["matches_played"]

            if matches_played == 0:
                continue

            goals_scored_per_match = (
                data["total_goals_scored"]
                / matches_played
            )

            goals_conceded_per_match = (
                data["total_goals_conceded"]
                / matches_played
            )

            team_strengths.append({
                "team_id": data["team_id"],
                "matches_played": matches_played,
                "total_goals_scored":
                    data["total_goals_scored"],
                "total_goals_conceded":
                    data["total_goals_conceded"],
                "goals_scored_per_match": round(
                    goals_scored_per_match,
                    2
                ),
                "goals_conceded_per_match": round(
                    goals_conceded_per_match,
                    2
                )
            })

        return team_strengths

    finally:
        if owns_db:
            db.close()


def get_team_strength(
    team_id,
    current_gameweek,
    db=None,
    team_strengths=None
):
    if team_strengths is None:
        team_strengths = get_all_team_strengths(
            current_gameweek,
            db=db
        )

    strength = next(
        (
            team
            for team in team_strengths
            if team["team_id"] == team_id
        ),
        None
    )

    if not strength:
        return {
            "error": "No matches found for the team"
        }

    return strength


def get_fixture_difficulty(
    opponent_team_id,
    player_position,
    current_gameweek,
    team_strengths=None,
    db=None
):
    if team_strengths is None:
        team_strengths = get_all_team_strengths(
            current_gameweek,
            db=db
        )

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
            opponent_strength[
                "goals_scored_per_match"
            ]
        )

        if max_attack == min_attack:
            normalized_attack = 0.5
        else:
            normalized_attack = (
                opponent_attack - min_attack
            ) / (
                max_attack - min_attack
            )

        difficulty_score = (
            1 + normalized_attack * 4
        )

    elif player_position in ["MID", "FWD"]:

        conceded_values = [
            team["goals_conceded_per_match"]
            for team in team_strengths
        ]

        min_conceded = min(conceded_values)
        max_conceded = max(conceded_values)

        opponent_conceded = (
            opponent_strength[
                "goals_conceded_per_match"
            ]
        )

        if max_conceded == min_conceded:
            normalized_conceded = 0.5
        else:
            normalized_conceded = (
                opponent_conceded - min_conceded
            ) / (
                max_conceded - min_conceded
            )

        normalized_defensive_difficulty = (
            1 - normalized_conceded
        )

        difficulty_score = (
            1
            + normalized_defensive_difficulty * 4
        )

    else:
        return {
            "error": "Invalid player position"
        }

    return {
        "opponent_team_id": opponent_team_id,
        "player_position": player_position,
        "difficulty_score": round(
            difficulty_score,
            2
        ),
        "opponent_goals_scored_per_match":
            opponent_strength[
                "goals_scored_per_match"
            ],
        "opponent_goals_conceded_per_match":
            opponent_strength[
                "goals_conceded_per_match"
            ]
    }