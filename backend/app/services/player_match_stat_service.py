from app.database import SessionLocal
from app.models import PlayerMatchStat
from app.models.fixture import Fixture
from app.models import Player
from app.services.football_api import get_player_match_stats


def sync_player_match_stats(fixture_id):
    db = SessionLocal()

    added = 0
    updated = 0
    skipped = 0

    fixture = (
    db.query(Fixture)
    .filter(Fixture.id == fixture_id)
    .first()
    )

    if not fixture:
        return {"error": "Fixture not found"}

    external_id = fixture.external_api_id

    try:
        data = get_player_match_stats(external_id)

        for team_item in data["response"]:
            for player_item in team_item["players"]:

                player_data = player_item["player"]
                api_player_id = player_data["id"]

                player = (
                    db.query(Player)
                    .filter(Player.external_api_id == api_player_id)
                    .first()
                )

                if not player:
                    skipped += 1
                    continue

                player_data = player_item["player"]
                # fixture_data = player_item["fixture"]
                stats_data = player_item["statistics"]

                stats = stats_data[0]
                player_id = player_data["id"]
                # fixture_id = fixture_data["id"]

                existing_stat = (
                    db.query(PlayerMatchStat)
                    .filter(
                        PlayerMatchStat.player_id == player.id,
                        PlayerMatchStat.fixture_id == fixture.id
                    )
                    .first()
                )

                if existing_stat:
                    existing_stat.minutes = stats["games"]["minutes"] or 0
                    existing_stat.goals = stats["goals"]["total"] or 0
                    existing_stat.assists = stats["goals"]["assists"] or 0
                    existing_stat.shots = stats["shots"]["total"] or 0
                    existing_stat.shots_on_target = stats["shots"]["on"] or 0
                    existing_stat.key_passes = stats["passes"]["key"] or 0
                    existing_stat.tackles = stats["tackles"]["total"] or 0
                    existing_stat.interceptions = stats["tackles"]["interceptions"] or 0
                    existing_stat.yellow_cards = stats["cards"]["yellow"] or 0
                    existing_stat.red_cards = stats["cards"]["red"] or 0
                    existing_stat.rating = stats["games"]["rating"]

                    db.add(existing_stat)
                    updated += 1
                else:
                    # Create new stat

                    rating = stats["games"]["rating"]

                    if rating is not None:
                        rating = float(rating)

                    new_stat = PlayerMatchStat(
                        player_id=player.id,
                        fixture_id=fixture.id,
                        minutes=stats["games"]["minutes"] or 0,
                        goals=stats["goals"]["total"] or 0,
                        assists=stats["goals"]["assists"] or 0,
                        shots=stats["shots"]["total"] or 0,
                        shots_on_target=stats["shots"]["on"] or 0,
                        key_passes=stats["passes"]["key"] or 0,
                        tackles=stats["tackles"]["total"] or 0,
                        interceptions=stats["tackles"]["interceptions"] or 0,
                        yellow_cards=stats["cards"]["yellow"] or 0,
                        red_cards=stats["cards"]["red"] or 0,
                        rating=rating
                    )

                    db.add(new_stat)
                    added += 1

        db.commit()

        return {
            "added": added,
            "updated": updated,
            "skipped": skipped,
        }

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
