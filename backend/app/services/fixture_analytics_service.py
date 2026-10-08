from app.database import SessionLocal
from app.models.player import Player
from app.models.fixture import Fixture
from app.services.fixture_difficulty_service import (
    get_fixture_difficulty
)
from app.services.football_api import SEASON


def get_upcoming_fixtures(
    player_id,
    current_gameweek,
    limit=5,
    db=None,
    player=None
):
    owns_db = db is None

    if owns_db:
        db = SessionLocal()

    try:
        if player is None:
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
                Fixture.season == SEASON,
                Fixture.gameweek > current_gameweek,
                (
                    (Fixture.home_team_id == player.team_id)
                    |
                    (Fixture.away_team_id == player.team_id)
                )
            )
            .order_by(
                Fixture.fixture_date.asc()
            )
            .limit(limit)
            .all()
        )

        results = []

        for fixture in upcoming_fixtures:
            is_home = (
                fixture.home_team_id
                == player.team_id
            )

            if is_home:
                opponent = fixture.away_team.name
                opponent_team_id = (
                    fixture.away_team_id
                )

            else:
                opponent = fixture.home_team.name
                opponent_team_id = (
                    fixture.home_team_id
                )

            results.append({
                "fixture_id": fixture.id,
                "gameweek": fixture.gameweek,
                "fixture_date":
                    fixture.fixture_date,
                "opponent": opponent,
                "opponent_team_id":
                    opponent_team_id,
                "home": is_home,
                "status": fixture.status
            })

        return results

    finally:
        if owns_db:
            db.close()


def get_player_fixture_outlook(
    player_id,
    current_gameweek,
    limit=5,
    db=None,
    player=None,
    team_strengths=None
):
    owns_db = db is None

    if owns_db:
        db = SessionLocal()

    try:
        if player is None:
            player = (
                db.query(Player)
                .filter(Player.id == player_id)
                .first()
            )

        if not player:
            return {
                "error": "Player not found"
            }

        upcoming_fixtures = get_upcoming_fixtures(
            player_id=player_id,
            current_gameweek=current_gameweek,
            limit=limit,
            db=db,
            player=player
        )

        if (
            isinstance(upcoming_fixtures, dict)
            and "error" in upcoming_fixtures
        ):
            return upcoming_fixtures

        fixture_outlook = []
        difficulty_scores = []

        position_map = {
            "Goalkeeper": "GK",
            "Defender": "DEF",
            "Midfielder": "MID",
            "Attacker": "FWD"
        }

        player_position = position_map.get(
            player.position
        )

        if not player_position:
            return {
                "error":
                    f"Unsupported player position: "
                    f"{player.position}"
            }

        for fixture in upcoming_fixtures:

            difficulty_data = (
                get_fixture_difficulty(
                    opponent_team_id=fixture[
                        "opponent_team_id"
                    ],
                    player_position=player_position,
                    current_gameweek=current_gameweek,
                    team_strengths=team_strengths,
                    db=db
                )
            )

            if "error" in difficulty_data:
                return {
                    "error":
                        difficulty_data["error"]
                }

            difficulty_score = (
                difficulty_data[
                    "difficulty_score"
                ]
            )

            difficulty_scores.append(
                difficulty_score
            )

            fixture_outlook.append({
                **fixture,
                "difficulty_score":
                    difficulty_score
            })

        average_fixture_difficulty = (
            sum(difficulty_scores)
            / len(difficulty_scores)
            if difficulty_scores
            else None
        )

        return {
            "player_id": player_id,
            "average_fixture_difficulty": (
                round(
                    average_fixture_difficulty,
                    2
                )
                if average_fixture_difficulty
                is not None
                else None
            ),
            "fixtures": fixture_outlook
        }

    finally:
        if owns_db:
            db.close()