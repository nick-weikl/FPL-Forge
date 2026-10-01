from app.database import SessionLocal
from app.models.team import Team
from app.services.football_api import get_premier_league_teams


def sync_premier_league_teams():

    data = get_premier_league_teams()

    db = SessionLocal()

    added = 0
    updated = 0

    try:

        for item in data["response"]:

            team_data = item["team"]

            api_id = team_data["id"]
            name = team_data["name"]
            code = team_data["code"]

            existing_team = (
                db.query(Team)
                .filter(Team.external_api_id == api_id)
                .first()
            )

            if existing_team:

                existing_team.name = name
                existing_team.short_name = code

                updated += 1

            else:

                new_team = Team(
                    external_api_id=api_id,
                    name=name,
                    short_name=code
                )

                db.add(new_team)

                added += 1

        db.commit()

        return {
            "added": added,
            "updated": updated
        }

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()