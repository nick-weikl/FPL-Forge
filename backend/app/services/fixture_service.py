from app.database import SessionLocal
from app.models import Team
from app.models import Fixture
from app.services.football_api import get_premier_league_fixtures


def sync_premier_league_fixtures():
    db = SessionLocal()

    added = 0
    updated = 0
    skipped = 0

    try:
        data = get_premier_league_fixtures()

        for item in data["response"]:
            fixture_data = item["fixture"]
            teams_data = item["teams"]
            league_data = item["league"]
            goals_data = item["goals"]

            fixture_id = fixture_data["id"]

            # External API team IDs
            home_team_api_id = teams_data["home"]["id"]
            away_team_api_id = teams_data["away"]["id"]

            # Find our internal Team records
            home_team = (
                db.query(Team)
                .filter(Team.external_api_id == home_team_api_id)
                .first()
            )

            away_team = (
                db.query(Team)
                .filter(Team.external_api_id == away_team_api_id)
                .first()
            )

            # If either team is missing from our DB, skip the fixture
            if not home_team or not away_team:
                skipped += 1
                continue

            # Example: "Regular Season - 5"
            round_name = league_data["round"]

            gameweek = None

            if round_name:
                parts = round_name.split(" - ")

                if len(parts) == 2:
                    gameweek = int(parts[1])

            # Check whether fixture already exists
            existing_fixture = (
                db.query(Fixture)
                .filter(Fixture.external_api_id == fixture_id)
                .first()
            )

            if existing_fixture:
                existing_fixture.fixture_date = fixture_data["date"]
                existing_fixture.status = fixture_data["status"]["short"]
                existing_fixture.gameweek = gameweek

                existing_fixture.home_team_id = home_team.id
                existing_fixture.away_team_id = away_team.id

                existing_fixture.home_score = goals_data["home"]
                existing_fixture.away_score = goals_data["away"]

                updated += 1

            else:
                new_fixture = Fixture(
                    external_api_id=fixture_id,
                    fixture_date=fixture_data["date"],
                    status=fixture_data["status"]["short"],
                    gameweek=gameweek,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    home_score=goals_data["home"],
                    away_score=goals_data["away"],
                )

                db.add(new_fixture)

                added += 1

        db.commit()

        return {
            "added": added,
            "updated": updated,
            "skipped": skipped,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()