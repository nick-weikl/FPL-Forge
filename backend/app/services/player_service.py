from app.database import SessionLocal
from app.models.player import Player
from app.models.team import Team
from app.services.football_api import get_premier_league_players


def sync_premier_league_players():
    db = SessionLocal()

    added = 0
    updated = 0
    skipped = 0

    page = 1
    max_free_pages = 3

    try:
        while True:
            data = get_premier_league_players(page)

            for item in data["response"]:
                player_data = item["player"]

                api_id = player_data["id"]
                name = player_data["name"]

                statistics = item.get("statistics", [])

                if not statistics:
                    skipped += 1
                    continue

                stat = statistics[0]

                team_data = stat["team"]
                team_api_id = team_data["id"]

                games = stat.get("games", {})
                position = games.get("position")

                position_mapping = {
                    "Goalkeeper": "Goalkeeper",
                    "Defender": "Defender",
                    "Midfielder": "Midfielder",
                    "Forward": "Attacker",
                    "Attacker": "Attacker"
                }

                position = position_mapping.get(
                    position,
                    position
                )

                team = (
                    db.query(Team)
                    .filter(Team.external_api_id == team_api_id)
                    .first()
                )

                if not team:
                    skipped += 1
                    continue

                existing_player = (
                    db.query(Player)
                    .filter(Player.external_api_id == api_id)
                    .first()
                )

                if existing_player:
                    existing_player.name = name
                    existing_player.position = position
                    existing_player.team_id = team.id

                    updated += 1

                else:
                    new_player = Player(
                        external_api_id=api_id,
                        name=name,
                        position=position,
                        team_id=team.id
                    )

                    db.add(new_player)

                    added += 1

            db.commit()

            current_page = data["paging"]["current"]
            total_pages = data["paging"]["total"]

            if (
                current_page >= max_free_pages
                or current_page >= total_pages
            ):
                break

            page += 1

        return {
            "added": added,
            "updated": updated,
            "skipped": skipped,
            "pages_processed": page
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()